import asyncio
from datetime import datetime, timezone
import email
from email.mime.text import MIMEText
import email.policy
import hashlib
from typing import Any, Dict, List, Optional

import aioimaplib
import aiosmtplib

from src.core.intelligent_response import IntelligentResponseHandler
from src.db.mongodb import MongoDBManager
from src.logs.logs import logger


class EmailClient:
    def __init__(self, email_address: str, app_password: str):
        self.email_address = email_address
        self.app_password = app_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993

    async def send_email(self, to_address: str, subject: str, body: str):
        msg = MIMEText(body, "html")
        msg["Subject"] = subject
        msg["From"] = self.email_address
        msg["To"] = to_address

        await aiosmtplib.send(
            msg,
            hostname=self.smtp_server,
            port=self.smtp_port,
            username=self.email_address,
            password=self.app_password,
            start_tls=True,
        )

    async def fetch_emails(self, folder="INBOX", search_criteria="ALL", limit=10) -> List[Dict]:
        client = aioimaplib.IMAP4_SSL(host=self.imap_server, port=self.imap_port)
        await client.wait_hello_from_server()

        await client.login(self.email_address, self.app_password)
        await client.select(folder)

        _, search_data = await client.search(search_criteria)
        email_ids = search_data[0].split()[-limit:]

        emails = []
        for eid in email_ids:
            _, fetch_data = await client.fetch(eid.decode(), "(RFC822)")

            raw_msg = None
            for item in fetch_data:
                if isinstance(item, tuple) and isinstance(item[1], (bytes, bytearray)):
                    raw_msg = item[1]
                    break
                elif isinstance(item, (bytes, bytearray)):
                    if item.startswith(b"From:") or item.startswith(b"Delivered-To:"):
                        raw_msg = item
                        break

            if not raw_msg:
                continue

            msg = email.message_from_bytes(raw_msg, policy=email.policy.default)
            subject = msg.get("subject", "").strip()
            from_ = msg.get("from", "").strip()
            body = ""

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain" and not part.get_filename():
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode(  # type: ignore
                                part.get_content_charset() or "utf-8",
                                errors="ignore",
                            ).strip()
                            break
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(  # type: ignore
                        msg.get_content_charset() or "utf-8", errors="ignore"
                    ).strip()

            unique_key = hashlib.sha256(f"{from_}{subject}{body}".encode()).hexdigest()

            emails.append(
                {
                    "uid": eid.decode(),
                    "subject": subject,
                    "from": from_,
                    "body": body,
                    "hash": unique_key,
                }
            )

        await client.logout()
        return emails


class EmailTaskManager:
    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.mongo_manager = MongoDBManager()
        self.client_cache: Dict[str, EmailClient] = {}
        self.check_interval = 10

    async def start_email_task(
        self,
        organization_id: str,
        email_address: str,
        app_password: str,
        filters: Optional[list] = None,
    ) -> Dict[str, Any]:
        try:
            if organization_id in self.active_tasks:
                return {
                    "success": False,
                    "message": f"Email task already running for organization {organization_id}",
                    "task_id": organization_id,
                }

            email_client = EmailClient(email_address, app_password)
            self.client_cache[organization_id] = email_client

            task = asyncio.create_task(
                self._run_email_task(organization_id, email_client, filters)  # type: ignore
            )
            self.active_tasks[organization_id] = task

            task_info = {
                "organization_id": organization_id,
                "email_address": email_address,
                "filters": filters or [],
                "status": "running",
                "started_at": datetime.now(timezone.utc),
            }

            await self.mongo_manager.update_one(
                "email_tasks",
                {"organization_id": organization_id},
                task_info,
                upsert=True,
            )

            logger.info(f"Started email task for organization {organization_id}")

            return {
                "success": True,
                "message": f"Email task started for organization {organization_id}",
                "task_id": organization_id,
                "email_address": email_address,
                "started_at": task_info["started_at"],
            }
        except Exception as e:
            logger.error(f"Error starting email task: {str(e)}")
            return {"success": False, "message": f"Failed to start email task: {str(e)}"}

    async def _run_email_task(self, organization_id: str, email_client, filters: list):
        intelligent_response_handler = IntelligentResponseHandler()
        try:
            logger.info(f"Running email task for organization {organization_id}")
            while True:
                # ✅ Restrict to today's unseen emails
                today = datetime.now().strftime("%d-%b-%Y")  # e.g., "19-Aug-2025"
                search_criteria = f"(UNSEEN SINCE {today})"

                logger.info("Fetching today's emails")
                emails = await email_client.fetch_emails(search_criteria=search_criteria, limit=10)
                logger.info(f"Fetched {len(emails)} emails")

                for mail in emails:
                    logger.info(f"Fetched email: {mail.get('subject')} from {mail.get('from')}")

                    llm_responses = await intelligent_response_handler.handle_message(
                        mail.get("body", ""),
                        recent_messages=None,
                        current_message={
                            "text": mail.get("body", ""),
                            "subject": mail.get("subject", ""),
                            "from": mail.get("from", ""),
                        },
                        search_results=None,
                    )

                    reply_text = llm_responses[0] if llm_responses else "Thank you for your email."

                    await email_client.send_email(
                        to_address=mail.get("from"),
                        subject=f"Re: {mail.get('subject')}",
                        body=reply_text,
                    )
                    logger.info(f"Sent LLM reply to {mail.get('from')}")

                await asyncio.sleep(self.check_interval)

        except asyncio.CancelledError:
            logger.info(f"Email task cancelled for organization {organization_id}")

        finally:
            await self.mongo_manager.update_one(
                "email_tasks",
                {"organization_id": organization_id},
                {"status": "stopped", "stopped_at": datetime.now(timezone.utc)},
            )

    async def stop_email_task(self, organization_id: str) -> Dict[str, Any]:
        try:
            if organization_id not in self.active_tasks:
                return {
                    "success": False,
                    "message": f"No active email task found for organization {organization_id}",
                }

            task = self.active_tasks[organization_id]
            task.cancel()
            del self.active_tasks[organization_id]

            await self.mongo_manager.update_one(
                "email_tasks",
                {"organization_id": organization_id},
                {"status": "stopped", "stopped_at": datetime.now(timezone.utc)},
            )

            logger.info(f"Stopped email task for organization {organization_id}")

            return {
                "success": True,
                "message": f"Email task stopped for organization {organization_id}",
                "task_id": organization_id,
            }
        except Exception as e:
            logger.error(f"Error stopping email task: {str(e)}")
            return {"success": False, "message": f"Failed to stop email task: {str(e)}"}

    async def get_active_tasks(self) -> Dict[str, Any]:
        active_tasks = {}
        for org_id, task in self.active_tasks.items():
            active_tasks[org_id] = {
                "task_id": org_id,
                "status": "running",
                "is_running": True,
            }
        return {"success": True, "active_tasks": active_tasks, "total_active": len(active_tasks)}

    async def get_task_status(self, organization_id: str) -> Dict[str, Any]:
        try:
            if organization_id in self.active_tasks:
                return {
                    "success": True,
                    "task_id": organization_id,
                    "status": "running",
                    "is_running": True,
                }
            else:
                task_info = await self.mongo_manager.find_one(
                    "email_tasks", {"organization_id": organization_id}
                )
                if task_info:
                    return {
                        "success": True,
                        "task_id": organization_id,
                        "status": task_info.get("status", "unknown"),
                        "started_at": task_info.get("started_at"),
                        "stopped_at": task_info.get("stopped_at"),
                    }
                else:
                    return {
                        "success": False,
                        "message": f"No email task found for organization {organization_id}",
                    }
        except Exception as e:
            logger.error(f"Error getting email task status: {str(e)}")
            return {"success": False, "message": f"Failed to get email task status: {str(e)}"}

    async def stop_all_tasks(self) -> Dict[str, Any]:
        results = []
        for org_id in list(self.active_tasks.keys()):
            result = await self.stop_email_task(org_id)
            results.append(result)
        return {
            "success": True,
            "message": f"Stopped {len(results)} email tasks",
            "results": results,
        }


email_task_manager = EmailTaskManager()
