from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import Channel, Chat, Message

from src.config.config import config
from src.core.intelligent_response import IntelligentResponseHandler
from src.core.rag.qdrant import SemanticEmbeddingService, SemanticQdrantService, SemanticSearchRepo
from src.db.mongodb import MongoDBManager
from src.llm import  LLMManager
from src.logs.logs import logger


class RealTimeIntelligenceHandler:
    def __init__(self, organization_id: Optional[str] = None):
        self.organization_id = organization_id
        self.api_id: Optional[int] = None
        self.api_hash: Optional[str] = None
        self.phone: Optional[str] = None
        self.client: Optional[TelegramClient] = None
        self.mongo_manager = MongoDBManager()
        self.llm_manager = LLMManager()
        self.message_handlers: Dict[str, Callable] = {}
        self.allowed_group_ids: set = set()  # Track groups to monitor
        self.is_running = False
        self.intelligent_response_handler = IntelligentResponseHandler()
        self.is_auto_response_enabled = True
        embedding_service = SemanticEmbeddingService()
        qdrant_service = SemanticQdrantService(
            url=config.QDRANT_API_URL,
            api_key=config.QDRANT_API_KEY,
        )
        self.rag_repo = SemanticSearchRepo(embedding_service, qdrant_service)

    async def _setup_database_indexes(self) -> bool:
        try:
            await self.mongo_manager.create_index(
                "sessions", [("organization_id", 1), ("phone", 1)], unique=True
            )
            await self.mongo_manager.create_index(
                "groups", [("organization_id", 1), ("group_id", 1)], unique=True
            )

            await self.mongo_manager.create_index(
                "messages",
                [("organization_id", 1), ("chat_id", 1), ("date", -1)],
            )

            return True
        except Exception as e:
            logger.error(f"Failed to setup database indexes: {str(e)}")
            return False

    async def _load_organization_credentials(self) -> bool:
        try:
            if not self.organization_id:
                logger.error("No organization ID provided")
                return False

            if not await self.mongo_manager.setup():
                logger.error("Failed to setup MongoDB connection")
                return False

            logger.info(
                f"Loading organization credentials for organization ID: {self.organization_id}"
            )
            org_doc = await self.mongo_manager.find_one(
                "organizations", {"id": self.organization_id}
            )
            logger.info(f"Organization document: {org_doc}")
            if not org_doc:
                logger.error(f"Organization not found: {self.organization_id}")
                return False

            self.api_id = int(org_doc["api_id"])
            self.api_hash = org_doc["api_hash"]
            self.phone = org_doc["phone"]

            logger.info(f"Loaded credentials for organization: {org_doc['name']}")
            return True

        except Exception as e:
            logger.error(f"Error loading organization credentials: {str(e)}")
            return False

    async def _save_session(self, phone: str, session_string: str) -> bool:
        if not session_string or session_string == "None":
            logger.warning("Session string is empty, not saving")
            return False

        session_doc = {
            "organization_id": self.organization_id,
            "phone": phone,
            "session_string": session_string,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        return await self.mongo_manager.update_one(
            "sessions",
            {"organization_id": self.organization_id, "phone": phone},
            session_doc,
            upsert=True,
        )

    async def _load_session(self, phone: str) -> Optional[str]:
        session_doc = await self.mongo_manager.find_one(
            "sessions",
            {"organization_id": self.organization_id, "phone": phone},
        )
        if session_doc:
            session_string = session_doc.get("session_string")
            if session_string and session_string != "null" and session_string != "None":
                logger.info("Session string found in MongoDB")
                return session_string
            else:
                logger.info("Session string is null/empty in MongoDB")
        else:
            logger.info("No existing session found in MongoDB")
        return None

    async def _save_message(self, message_data: Dict) -> Dict[str, int]:
        chat_id = message_data["chat_id"]

        existing_message = await self.mongo_manager.find_one(
            "messages",
            {
                "message_id": message_data["id"],
                "chat_id": chat_id,
                "organization_id": self.organization_id,
            },
        )

        if existing_message:
            return {"saved": 0, "skipped": 1}

        message_doc = {
            "organization_id": self.organization_id,
            "message_id": message_data["id"],
            "chat_id": chat_id,
            "chat_type": message_data.get("chat_type", "unknown"),
            "chat_title": message_data.get("chat_title", "Unknown"),
            "text": message_data["text"],
            "date": message_data["date"],
            "sender_id": message_data["sender_id"],
            "sender_name": message_data["sender_name"],
            "sentiment": message_data.get("sentiment"),
            "polarity": message_data.get("polarity"),
            "is_own_message": message_data.get("is_own_message", False),
            "intelligent_response": message_data.get("intelligent_response"),
            "created_at": datetime.now(timezone.utc),
        }

        if await self.mongo_manager.insert_one("messages", message_doc):
            return {"saved": 1, "skipped": 0}
        else:
            return {"saved": 0, "skipped": 0}

    async def _save_messages_bulk(self, messages_data: List[Dict]) -> Dict[str, int]:
        if not messages_data:
            return {"saved": 0, "skipped": 0}

        # Check for existing messages in bulk
        message_ids = [msg["id"] for msg in messages_data]
        existing_messages = await self.mongo_manager.find_many(
            "messages",
            {
                "message_id": {"$in": message_ids},
                "organization_id": self.organization_id,
            },
        )

        existing_message_ids = {msg["message_id"] for msg in existing_messages}

        # Filter out existing messages and prepare bulk insert
        new_messages = []
        skipped_count = 0

        for msg_data in messages_data:
            if msg_data["id"] in existing_message_ids:
                skipped_count += 1
                continue

            chat_id = msg_data["chat_id"]

            message_doc = {
                "organization_id": self.organization_id,
                "message_id": msg_data["id"],
                "chat_id": chat_id,
                "chat_type": msg_data.get("chat_type", "unknown"),
                "chat_title": msg_data.get("chat_title", "Unknown"),
                "text": msg_data["text"],
                "date": msg_data["date"],
                "sender_id": msg_data["sender_id"],
                "sender_name": msg_data["sender_name"],
                "sentiment": msg_data.get("sentiment"),
                "polarity": msg_data.get("polarity"),
                "is_own_message": msg_data.get("is_own_message", False),
                "intelligent_response": msg_data.get("intelligent_response"),
                "created_at": datetime.now(timezone.utc),
            }
            new_messages.append(message_doc)

        # Bulk insert new messages
        saved_count = 0
        if new_messages:
            saved_count = await self.mongo_manager.insert_many("messages", new_messages)

        return {"saved": saved_count, "skipped": skipped_count}

    async def _update_message_sentiment(
        self, chat_id: int, message_id: int, sentiment: str, polarity: float
    ) -> bool:
        update_doc = {
            "sentiment": sentiment,
            "polarity": polarity,
            "sentiment_updated_at": datetime.now(timezone.utc),
        }

        return await self.mongo_manager.update_one(
            "messages",
            {
                "message_id": message_id,
                "chat_id": chat_id,
                "organization_id": self.organization_id,
            },
            update_doc,
        )

    async def setup_client(self) -> bool:
        try:
            if not await self._load_organization_credentials():
                logger.error("Failed to load organization credentials")
                return False

            if not await self.mongo_manager.setup():
                logger.error("Failed to setup MongoDB connection")
                return False

            if not await self._setup_database_indexes():
                logger.error("Failed to setup database indexes")
                return False

            if not self.api_id or not self.api_hash or not self.phone:
                logger.error("Missing organization credentials")
                return False

            session_string = await self._load_session(self.phone)

            if session_string:
                logger.info("Restoring session from MongoDB...")
                self.client = TelegramClient(
                    StringSession(session_string), self.api_id, self.api_hash
                )
            else:
                logger.info("Creating new session...")
                session = StringSession()
                self.client = TelegramClient(session, self.api_id, self.api_hash)

            if self.phone:
                await self.client.start(phone=self.phone)  # type: ignore
            else:
                await self.client.start()  # type: ignore

            if await self.client.is_user_authorized():
                if not session_string:
                    session_string = self.client.session.save()  # type: ignore
                    if await self._save_session(self.phone, session_string):
                        logger.info("Client setup successful")
                    else:
                        logger.warning("Client setup successful but failed to save session")
                else:
                    logger.info("Client setup successful")
                return True
            else:
                logger.error("Authorization failed")
                return False

        except Exception as e:
            logger.error(f"Client setup error: {str(e)}")
            return False

    def _code_callback(self):
        return input("Enter the code you received: ")

    def add_message_handler(self, group_id: int, handler: Callable[[Dict], None]):
        self.message_handlers[str(group_id)] = handler
        if group_id > 0:
            self.message_handlers[str(-group_id)] = handler
        elif group_id < 0:
            self.message_handlers[str(abs(group_id))] = handler
            channel_format_id = -1000000000000 + abs(group_id)
            self.message_handlers[str(channel_format_id)] = handler
        logger.info(f"Added message handler for group {group_id}")

    def add_global_message_handler(self, handler: Callable[[Dict], None]):
        self.message_handlers["global"] = handler
        logger.info("Added global message handler for all chats")

    def remove_global_message_handler(self):
        if "global" in self.message_handlers:
            del self.message_handlers["global"]
            logger.info("Removed global message handler")

    def remove_message_handler(self, group_id: int):
        group_id_str = str(group_id)
        if group_id_str in self.message_handlers:
            del self.message_handlers[group_id_str]
            logger.info(f"Removed message handler for group {group_id}")

        if group_id > 0:
            neg_group_id_str = str(-group_id)
            if neg_group_id_str in self.message_handlers:
                del self.message_handlers[neg_group_id_str]
        elif group_id < 0:
            pos_group_id_str = str(abs(group_id))
            if pos_group_id_str in self.message_handlers:
                del self.message_handlers[pos_group_id_str]

    def add_allowed_group(self, group_id: int):
        self.allowed_group_ids.add(group_id)
        logger.info(f"Added group {group_id} to monitoring list")

    def add_allowed_groups(self, group_ids: list):
        for group_id in group_ids:
            self.allowed_group_ids.add(group_id)
        logger.info(f"Added groups {group_ids} to monitoring list")

    def remove_allowed_group(self, group_id: int):
        if group_id in self.allowed_group_ids:
            self.allowed_group_ids.remove(group_id)
            logger.info(f"Removed group {group_id} from monitoring list")

    def get_allowed_groups(self) -> list:
        return list(self.allowed_group_ids)

    def clear_allowed_groups(self):
        self.allowed_group_ids.clear()
        logger.info("Cleared all monitored groups")

    def _normalize_group_id(self, group_id: int) -> int:
        if group_id < -1000000000000:
            normalized_id = -(group_id + 1000000000000)
            logger.info(f"Normalized megagroup/channel ID from {group_id} to {normalized_id}")
            return normalized_id
        elif group_id < 0:
            normalized_id = abs(group_id)
            logger.info(f"Normalized regular group ID from {group_id} to {normalized_id}")
            return normalized_id
        else:
            logger.info(f"Group ID {group_id} is already positive, keeping as is")
            return group_id

    def is_group_monitored(self, group_id: int) -> bool:
        if group_id in self.allowed_group_ids:
            return True

        for allowed_id in self.allowed_group_ids:
            if abs(group_id) == abs(allowed_id):
                return True

        return False

    async def update_detailed_analysis(self, group_id: int, message_data: Dict):
        try:
            normalized_group_id = self._normalize_group_id(group_id)

            group_info = await self.mongo_manager.find_one(
                "groups",
                {
                    "organization_id": self.organization_id,
                    "group_id": normalized_group_id,
                },
            )

            group_type = "unknown"
            group_category = "unknown"
            size_category = "unknown"
            if group_info:
                group_type = group_info.get("group_type", "unknown")
                group_category = group_info.get("group_category", "unknown")
                size_category = group_info.get("size_category", "unknown")

            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)

            existing_analysis = await self.mongo_manager.find_one(
                "detailed_analyses",
                {
                    "organization_id": self.organization_id,
                    "group_id": normalized_group_id,
                    "analysis_date": {"$gte": today, "$lt": tomorrow},
                },
            )

            if existing_analysis:
                logger.info(f"Updating existing detailed analysis for group {group_id}")

                summary = existing_analysis.get("summary", {})
                summary["total_messages"] = summary.get("total_messages", 0) + 1

                sentiment_dist = summary.get("sentiment_distribution", {})
                current_sentiment = message_data.get("sentiment", "neutral")
                sentiment_dist[current_sentiment] = sentiment_dist.get(current_sentiment, 0) + 1
                summary["sentiment_distribution"] = sentiment_dist

                total_polarity = summary.get("total_polarity", 0) + message_data.get(
                    "polarity", 0.0
                )
                summary["total_polarity"] = total_polarity
                summary["average_sentiment"] = total_polarity / summary["total_messages"]

                user_activity = existing_analysis.get("user_activity", {})
                user_message_counts = user_activity.get("user_message_counts", {})
                sender_id = str(message_data.get("sender_id", "unknown"))
                user_message_counts[sender_id] = user_message_counts.get(sender_id, 0) + 1
                user_activity["user_message_counts"] = user_message_counts

                top_users = sorted(
                    user_message_counts.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:5]
                user_activity["top_users"] = top_users

                update_doc = {
                    "summary": summary,
                    "user_activity": user_activity,
                    "updated_at": datetime.now(timezone.utc),
                }

                await self.mongo_manager.update_one(
                    "detailed_analyses",
                    {"_id": existing_analysis["_id"]},
                    update_doc,
                )

                logger.info(
                    f"Updated existing detailed analysis for group {group_id} (normalized: {normalized_group_id}) with new message"
                )

            else:
                logger.info(f"Creating new detailed analysis for group {group_id}")

                detailed_analysis = {
                    "organization_id": self.organization_id,
                    "group_id": normalized_group_id,
                    "group_title": message_data.get("chat_title", "Unknown"),
                    "group_type": group_type,
                    "group_category": group_category,
                    "size_category": size_category,
                    "analysis_date": datetime.now(timezone.utc),
                    "time_period_days": 1,  # Real-time analysis
                    "summary": {
                        "total_messages": 1,
                        "unique_users": 1,
                        "average_sentiment": message_data.get("polarity", 0.0),
                        "total_polarity": message_data.get("polarity", 0.0),
                        "sentiment_distribution": {message_data.get("sentiment", "neutral"): 1},
                    },
                    "user_activity": {
                        "user_message_counts": {str(message_data.get("sender_id", "unknown")): 1},
                        "top_users": [(str(message_data.get("sender_id", "unknown")), 1)],
                    },
                }

                await self.mongo_manager.insert_one("detailed_analyses", detailed_analysis)
                logger.info(
                    f"Created new detailed analysis for group {group_id} (normalized: {normalized_group_id}) with first message"
                )

        except Exception as e:
            logger.error(f"Error updating detailed analysis: {str(e)}")

    async def get_message_ownership(self, message: Message) -> bool:
        current_user = None
        is_own_message = False
        try:
            current_user = await self.client.get_me()  # type: ignore
            message_sender_id = getattr(message, "sender_id", None)
            current_user_id = getattr(current_user, "id", None)

            if message_sender_id and current_user_id:
                is_own_message = message_sender_id == current_user_id
                logger.info(
                    f"Message sender ID: {message_sender_id}, Current user ID: {current_user_id}, Is own message: {is_own_message}"
                )
                return is_own_message
            else:
                logger.warning(
                    f"Could not determine message ownership - sender_id: {message_sender_id}, current_user_id: {current_user_id}"
                )
                return False
        except Exception as e:
            logger.error(f"Error getting current user information: {str(e)}")
            return False

    async def get_recent_messages(self, chat_id: int, limit: int = 30) -> List[Dict]:
        try:
            query_filter = {
                "organization_id": self.organization_id,
                "chat_id": chat_id,
            }

            messages = await self.mongo_manager.find_many(
                "messages", query_filter, sort_fields=[("date", -1)], limit=limit
            )

            recent_messages = []
            for msg in messages:
                recent_messages.append(
                    {
                        "text": msg.get("text", ""),
                        "sender_name": msg.get("sender_name", "Unknown"),
                        "date": msg.get("date"),
                        "sender_id": msg.get("sender_id"),
                        "is_own_message": msg.get("is_own_message", False),
                    }
                )

            recent_messages.reverse()

            logger.info(f"Retrieved {len(recent_messages)} recent messages for chat {chat_id}")
            return recent_messages

        except Exception as e:
            logger.error(f"Error fetching recent messages: {str(e)}")
            return []

    async def send_intelligent_response(self, chat_id: int, response_text: str) -> bool:
        try:
            if not self.client or not self.client.is_connected():
                logger.error("Client not connected, cannot send message")
                return False

            await self.client.send_message(chat_id, response_text, parse_mode="html")
            logger.info(f"Sent intelligent response to chat {chat_id}: {response_text[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Error sending intelligent response: {str(e)}")
            return False

    async def process_message(self, message: Message) -> Dict[str, Any]:
        try:
            sender_name = "Unknown"
            if hasattr(message, "sender_id") and message.sender_id:  # type: ignore
                try:
                    sender = await self.client.get_entity(message.sender_id)  # type: ignore
                    sender_name = (
                        getattr(sender, "first_name", "")
                        + " "
                        + getattr(sender, "last_name", "").strip()
                    ).strip()
                except Exception:
                    sender_name = f"User_{getattr(message, 'sender_id', 'unknown')}"

            chat = await message.get_chat()  # type: ignore
            chat_title = getattr(chat, "title", "Unknown Chat")
            chat_type = type(chat).__name__

            message_data = {
                "id": message.id,
                "text": getattr(message, "text", "") or "",
                "date": message.date,
                "sender_id": getattr(message, "sender_id", None),
                "sender_name": sender_name,
                "chat_id": getattr(message, "chat_id", None),
                "chat_title": chat_title,
                "chat_type": chat_type,
                "received_at": datetime.now(timezone.utc),
                "sentiment": None,
                "polarity": None,
                "intelligent_response": None,
            }

            is_own_message = await self.get_message_ownership(message)
            message_data["is_own_message"] = is_own_message
            logger.info(f"Is own message: {is_own_message}")

            if message_data["text"] and not is_own_message:
                logger.info(
                    f"Starting intelligent response for message: {message_data['text'][:50]}..."
                )
                try:
                    # Get recent messages for context
                    chat_id = message_data["chat_id"]
                    recent_messages = await self.get_recent_messages(chat_id, limit=30)

                    # Add current message to the history
                    current_message = {
                        "text": message_data["text"],
                        "sender_name": message_data["sender_name"],
                        "date": message_data["date"],
                        "sender_id": message_data["sender_id"],
                        "is_own_message": is_own_message,
                    }

                    search_results = await self.rag_repo.query_text(
                        query_text=message_data["text"],
                        owner_id=message_data.get("owner_id", None),
                        telegram_group_id=message_data.get("telegram_group_id", None),
                        account_id=message_data.get("account_id", None),
                    )

                    intelligent_response = await self.intelligent_response_handler.handle_message(
                        message_data["text"],
                        recent_messages=recent_messages,
                        current_message=current_message,
                        search_results=search_results,
                    )
                    message_data["intelligent_response"] = intelligent_response

                    if self.is_auto_response_enabled is True and intelligent_response:
                        logger.info(
                            f"The message does not belong to the session owner. Sending intelligent response to chat {chat_id}: {intelligent_response}"
                        )
                        await self.send_intelligent_response(chat_id, intelligent_response[0])

                except Exception as e:
                    logger.error(f"Error in intelligent response: {str(e)}")
            else:
                if not message_data["text"]:
                    logger.info("Message has no text, skipping intelligent response")
                elif is_own_message:
                    logger.info("Message is from own user, skipping intelligent response")
                else:
                    logger.info("Skipping intelligent response for unknown reason")

            result = await self._save_message(message_data)
            logger.info(
                f"Message save result: {result['saved']} saved, {result['skipped']} skipped"
            )
            return message_data

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {}

    async def handle_new_message(self, event):
        try:
            logger.info(f"=== EVENT HANDLER TRIGGERED ===")
            logger.info(f"Event received: {type(event)}")
            message = event.message
            logger.info(
                f"Message from chat_id: {message.chat_id}, text: {message.text[:50] if message.text else 'No text'}"
            )
            if not message.text:
                logger.info("Message has no text, skipping...")
                return

            chat_id = message.chat_id
            logger.info(f"Processing message from chat_id: {chat_id} for intelligence response")

            try:
                chat = await message.get_chat()
                chat_title = getattr(chat, "title", "Unknown Chat")
                chat_type = type(chat).__name__
                logger.info(f"Chat type: {chat_type}, Title: {chat_title}")
            except Exception as e:
                logger.warning(f"Could not get chat info: {e}")
                chat_title = "Unknown Chat"
                chat_type = "Unknown"

            logger.info(f"New message received in {chat_type}: {chat_title} (ID: {chat_id})")

            message_data = await self.process_message(message)
            if not message_data:
                return

            chat_id = message.chat_id
            group_id_str = str(chat_id)
            handler_found = False

            if group_id_str in self.message_handlers:
                try:
                    self.message_handlers[group_id_str](message_data)
                    handler_found = True
                except Exception as e:
                    logger.error(f"Error in message handler: {str(e)}")

            if not handler_found:
                abs_group_id_str = str(abs(chat_id))
                if abs_group_id_str in self.message_handlers:
                    try:
                        self.message_handlers[abs_group_id_str](message_data)
                        handler_found = True
                    except Exception as e:
                        logger.error(f"Error in message handler: {str(e)}")

            if not handler_found and chat_id < -1000000000000:
                regular_chat_id = -(chat_id + 1000000000000)
                regular_chat_id_str = str(regular_chat_id)
                if regular_chat_id_str in self.message_handlers:
                    try:
                        self.message_handlers[regular_chat_id_str](message_data)
                        handler_found = True
                        logger.info(f"Found handler with converted channel ID: {regular_chat_id}")
                    except Exception as e:
                        logger.error(f"Error in message handler: {str(e)}")

            if not handler_found and "global" in self.message_handlers:
                try:
                    self.message_handlers["global"](message_data)
                    handler_found = True
                    logger.info("Using global message handler")
                except Exception as e:
                    logger.error(f"Error in global message handler: {str(e)}")

            logger.info(f"  {message_data['sender_name']}: {message_data['text'][:50]}...")

        except Exception as e:
            logger.error(f"Error handling new message: {str(e)}")

    async def start_listening(self):
        if not self.client:
            logger.error("Client not initialized")
            return False

        try:
            logger.info("Starting real-time message listener for all chats...")

            self.is_running = True

            if not await self.client.is_user_authorized():
                logger.error("Client is not authorized")
                return False

            logger.info("Client is authorized, adding event handler...")

            if not self.client.is_connected():
                logger.info("Client not connected, connecting...")
                await self.client.connect()

            logger.info(f"Client connected: {self.client.is_connected()}")

            self.client.add_event_handler(self.handle_new_message, events.NewMessage())

            logger.info("Event handler registration completed - monitoring all chats")

            await self.client.run_until_disconnected()  # type: ignore

        except KeyboardInterrupt:
            logger.info("Stopping message listener...")
            self.is_running = False
        except Exception as e:
            logger.error(f"Error in message listener: {str(e)}")
            self.is_running = False

    async def stop_listening(self):
        self.is_running = False
        if self.client:
            await self.client.disconnect()  # type: ignore
        self.mongo_manager.close()
        logger.info("Message listener stopped")

    async def get_active_groups(self) -> list:
        try:
            if not self.client:
                return []

            groups = []
            async for dialog in self.client.iter_dialogs():
                entity_type = type(dialog.entity).__name__
                if not isinstance(dialog.entity, (Chat, Channel)):
                    continue
                logger.info(
                    f"Entity type: {entity_type}, ID: {dialog.entity.id}, Title: {dialog.entity.title}"
                )
                # Include both regular groups and megagroups (channels)
                if dialog.is_group or (
                    isinstance(dialog.entity, Channel) and dialog.entity.megagroup
                ):
                    group_info = {
                        "id": dialog.entity.id,
                        "title": dialog.entity.title,
                        "username": getattr(dialog.entity, "username", None),
                        "participants_count": getattr(dialog.entity, "participants_count", 0),
                        "entity_type": entity_type,
                        "is_megagroup": getattr(dialog.entity, "megagroup", False),
                    }
                    groups.append(group_info)

            logger.info(f"Found {len(groups)} groups")
            return groups

        except Exception as e:
            logger.error(f"Error getting groups: {str(e)}")
            return []
