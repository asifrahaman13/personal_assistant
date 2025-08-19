from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Channel, Chat, PeerChannel, PeerChat

from src.db.mongodb import MongoDBManager
from src.llm import LLMManager
from src.logs.logs import logger


class ProductionTelegramAnalyzer:
    def __init__(self, organization_id: Optional[str] = None):
        self.organization_id = organization_id
        self.api_id: Optional[int] = None
        self.api_hash: Optional[str] = None
        self.phone: Optional[str] = None
        self.client: Optional[TelegramClient] = None
        self.mongo_manager = MongoDBManager()
        self.llm_manager = LLMManager()

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

    async def _setup_database_indexes(self) -> bool:
        try:
            await self.mongo_manager.create_index("organizations", [("id", 1)], unique=True)
            await self.mongo_manager.create_index("organizations", [("name", 1)], unique=True)
            await self.mongo_manager.create_index("sessions", [("phone", 1)], unique=True)
            await self.mongo_manager.create_index("groups", [("group_id", 1)], unique=True)
            await self.mongo_manager.create_index("groups", [("group_type", 1)])
            await self.mongo_manager.create_index("groups", [("group_category", 1)])
            await self.mongo_manager.create_index("groups", [("size_category", 1)])
            await self.mongo_manager.create_index(
                "messages",
                [("group_id", 1), ("date", -1)],
            )
            await self.mongo_manager.create_index(
                "messages",
                [("group_type", 1), ("date", -1)],
            )
            await self.mongo_manager.create_index(
                "messages",
                [("group_category", 1), ("date", -1)],
            )
            await self.mongo_manager.create_index(
                "detailed_analyses",
                [
                    ("group_type", 1),
                    ("analysis_date", -1),
                ],
            )
            await self.mongo_manager.create_index(
                "detailed_analyses",
                [
                    ("group_category", 1),
                    ("analysis_date", -1),
                ],
            )
            await self.mongo_manager.create_index(
                "detailed_analyses",
                [
                    ("size_category", 1),
                    ("analysis_date", -1),
                ],
            )
            return True
        except Exception as e:
            logger.error(f"Failed to setup database indexes: {str(e)}")
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

    async def _save_group(self, group: Dict) -> bool:
        # Determine group type and category
        entity_type = group.get("entity_type", "Chat")
        is_megagroup = group.get("is_megagroup", False)
        participants_count = group.get("participants_count", 0)

        # Categorize the group
        if is_megagroup or entity_type == "Channel":
            group_type = "megagroup"
            group_category = "channel"
        else:
            group_type = "group"
            group_category = "chat"

        # Add size classification
        if participants_count > 10000:
            size_category = "super_large"
        elif participants_count > 5000:
            size_category = "large"
        elif participants_count > 1000:
            size_category = "medium"
        elif participants_count > 100:
            size_category = "small"
        else:
            size_category = "tiny"

        group_doc = {
            "group_id": group["id"],
            "title": group["title"],
            "username": group.get("username"),
            "participants_count": participants_count,
            "entity_type": entity_type,
            "is_megagroup": is_megagroup,
            "group_type": group_type,  # "group" or "megagroup"
            "group_category": group_category,  # "chat" or "channel"
            "size_category": size_category,  # "tiny", "small", "medium", "large", "super_large"
            "created_at": datetime.now(timezone.utc),
            "last_updated": datetime.now(timezone.utc),
        }

        return await self.mongo_manager.update_one(
            "groups",
            {"group_id": group["id"]},
            group_doc,
            upsert=True,
        )

    async def _save_messages(self, group_id: int, messages: List[Dict]) -> Dict[str, int]:
        if not messages:
            return {"saved": 0, "skipped": 0}

        # Get group info once for all messages
        group_info = await self.mongo_manager.find_one(
            "groups",
            {"group_id": group_id},
        )

        group_type = "unknown"
        group_category = "unknown"
        if group_info:
            group_type = group_info.get("group_type", "unknown")
            group_category = group_info.get("group_category", "unknown")

        # Check for existing messages in bulk
        message_ids = [msg["id"] for msg in messages]
        existing_messages = await self.mongo_manager.find_many(
            "messages",
            {
                "message_id": {"$in": message_ids},
                "group_id": group_id,
            },
        )

        existing_message_ids = {msg["message_id"] for msg in existing_messages}

        # Filter out existing messages and prepare bulk insert
        new_messages = []
        skipped_count = 0

        for msg in messages:
            if msg["id"] in existing_message_ids:
                skipped_count += 1
                continue

            message_doc = {
                "message_id": msg["id"],
                "group_id": group_id,
                "group_type": group_type,
                "group_category": group_category,
                "text": msg["text"],
                "date": msg["date"],
                "sender_id": msg["sender_id"],
                "sender_name": msg["sender_name"],
                "sentiment": None,
                "polarity": None,
                "created_at": datetime.now(timezone.utc),
            }
            new_messages.append(message_doc)

        # Bulk insert new messages
        saved_count = 0
        if new_messages:
            saved_count = await self.mongo_manager.insert_many("messages", new_messages)

        return {"saved": saved_count, "skipped": skipped_count}

    async def _get_cached_messages(self, group_id: int, days: int = 30) -> List[Dict]:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        return await self.mongo_manager.find_many(
            "messages",
            {
                "group_id": group_id,
                "date": {"$gte": start_date},
            },
            sort_fields=[("date", -1)],
        )

    async def _get_group_info(self, group_id: int) -> Optional[Dict]:
        """Get group information from database or fetch from Telegram"""
        try:
            logger.info(f"Looking for group info for group_id: {group_id}")

            # Try to get from database first - try both the original ID and its absolute value
            group_info = await self.mongo_manager.find_one(
                "groups",
                {"group_id": group_id},
            )

            if group_info:
                logger.info(f"Found group info in database for {group_id}")
            else:
                logger.info(f"Group {group_id} not found in database, trying with absolute value")
                # If not found, try with absolute value (for megagroups)
                group_info = await self.mongo_manager.find_one(
                    "groups",
                    {
                        "group_id": abs(group_id),
                    },
                )
                if group_info:
                    logger.info(
                        f"Found group info in database for abs({group_id}) = {abs(group_id)}"
                    )

            if group_info:
                # Check if this is actually a megagroup based on the entity type
                entity_type = group_info.get("entity_type", "Chat")
                is_megagroup = group_info.get("is_megagroup", False)

                # If entity type is Channel, it's likely a megagroup
                if entity_type == "Channel" and not is_megagroup:
                    is_megagroup = True

                # Additional check: if we have a large participants count and it's stored as Chat,
                # it might actually be a megagroup that was incorrectly categorized
                participants_count = group_info.get("participants_count", 0)
                if entity_type == "Chat" and participants_count > 200 and not is_megagroup:
                    logger.warning(
                        f"Group {group_info['group_id']} has {participants_count} participants but is stored as Chat. This might be a megagroup."
                    )
                    # Try to verify this by attempting to get the entity as a channel
                    if self.client:
                        try:
                            negative_id = -abs(group_info["group_id"])
                            test_entity = await self.client.get_entity(PeerChannel(negative_id))
                            if isinstance(test_entity, Channel):
                                logger.info(
                                    f"Confirmed: Group {group_info['group_id']} is actually a megagroup"
                                )
                                entity_type = "Channel"
                                is_megagroup = True
                                # Update the database with correct information
                                await self.mongo_manager.update_one(
                                    "groups",
                                    {
                                        "group_id": group_info["group_id"],
                                    },
                                    {
                                        "entity_type": "Channel",
                                        "is_megagroup": True,
                                        "last_updated": datetime.now(timezone.utc),
                                    },
                                )
                        except Exception as e:
                            logger.debug(f"Could not verify megagroup status: {e}")

                result = {
                    "id": group_info["group_id"],
                    "title": group_info["title"],
                    "username": group_info.get("username"),
                    "participants_count": participants_count,
                    "entity_type": entity_type,
                    "is_megagroup": is_megagroup,
                }
                logger.info(f"Returning group info: {result}")
                return result

            # If not in database, try to fetch from Telegram
            if self.client:
                logger.info(f"Group {group_id} not in database, trying to fetch from Telegram")
                try:
                    # For negative IDs (megagroups), we need to use the negative ID directly
                    # For positive IDs, we try both positive and negative
                    if group_id < 0:
                        # This is already a megagroup ID, try it directly
                        test_ids = [group_id]
                        logger.info(f"Using negative ID for megagroup: {test_ids}")
                    else:
                        # Try both positive and negative IDs
                        test_ids = [group_id, -abs(group_id)]
                        logger.info(f"Trying both positive and negative IDs: {test_ids}")

                    for test_id in test_ids:
                        try:
                            logger.info(f"Attempting to get entity with ID: {test_id}")
                            entity = await self.client.get_entity(test_id)

                            # Check if it's a channel with megagroup attribute
                            if isinstance(entity, Channel):
                                is_megagroup = getattr(entity, "megagroup", False)
                            else:
                                is_megagroup = False

                            group_info = {
                                "id": getattr(entity, "id", test_id),
                                "title": getattr(entity, "title", "Unknown"),
                                "username": getattr(entity, "username", None),
                                "participants_count": getattr(entity, "participants_count", 0),
                                "entity_type": type(entity).__name__,
                                "is_megagroup": is_megagroup,
                            }

                            # Save to database for future use
                            await self._save_group(group_info)
                            logger.info(
                                f"Successfully fetched and saved group info: {group_info['title']} (ID: {group_info['id']})"
                            )
                            return group_info
                        except Exception as e:
                            logger.debug(f"Failed to get entity with ID {test_id}: {e}")
                            continue
                except Exception as e:
                    logger.warning(f"Could not fetch group info for {group_id}: {e}")

            logger.error(f"Failed to find group info for group_id: {group_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting group info: {e}")
            return None

    async def send_code_request(self, phone: str) -> bool:
        try:
            if not await self._load_organization_credentials():
                logger.error("Failed to load organization credentials")
                return False

            if not self.api_id or not self.api_hash:
                logger.error("Missing API credentials")
                return False

            session = StringSession()
            self.client = TelegramClient(session, self.api_id, self.api_hash)

            await self.client.connect()
            await self.client.send_code_request(phone)

            logger.info(f"Code request sent to {phone}")
            return True

        except Exception as e:
            logger.error(f"Error sending code request: {str(e)}")
            if self.client:
                try:
                    await self.client.close()  # type: ignore
                except Exception:
                    pass
            return False

    async def verify_code(self, phone: str, code: str) -> Optional[str]:
        try:
            if not self.client:
                logger.error("No client available for code verification")
                return None

            await self.client.sign_in(phone, code)

            if await self.client.is_user_authorized():
                if hasattr(self.client, "session") and self.client.session:
                    session_string = self.client.session.save()
                    logger.info(f"Successfully authenticated {phone}")
                    return session_string
                else:
                    logger.error("No session available")
                    return None
            else:
                logger.error("Code verification failed")
                return None

        except Exception as e:
            logger.error(f"Error during code verification: {str(e)}")
            return None

    async def validate_session(self, phone: str) -> bool:
        try:
            if not await self._load_organization_credentials():
                logger.error("Failed to load organization credentials")
                return False

            session_string = await self._load_session(phone)
            if not session_string:
                return False

            if not self.api_id or not self.api_hash:
                logger.error("Missing API credentials")
                return False

            self.client = TelegramClient(StringSession(session_string), self.api_id, self.api_hash)

            await self.client.connect()
            is_authorized = await self.client.is_user_authorized()

            # Don't disconnect here - keep the client connected for subsequent operations
            if not is_authorized:
                await self.client.disconnect()  # type: ignore
                self.client = None

            return is_authorized

        except Exception as e:
            logger.warning(f"Error validating session: {str(e)}")
            if self.client:
                await self.client.disconnect()  # type: ignore
                self.client = None
            return False

    async def cleanup_client(self):
        if self.client:
            try:
                await self.client.disconnect()  # type: ignore
            except Exception as e:
                logger.error(f"Error disconnecting client: {str(e)}")
            finally:
                self.client = None

    async def login(self) -> bool:
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

            if not self.phone:
                logger.error("No phone number available")
                return False

            session_string = await self._load_session(self.phone)

            if session_string:
                logger.info("Found existing session in MongoDB, attempting to restore...")
                if not self.api_id or not self.api_hash:
                    logger.error("Missing API credentials")
                    return False

                self.client = TelegramClient(
                    StringSession(session_string), self.api_id, self.api_hash
                )

                try:
                    await self.client.start(phone=self.phone)  # type: ignore
                    if await self.client.is_user_authorized():
                        logger.info("Successfully restored session from MongoDB")
                        return True
                    else:
                        logger.warning("Session expired, need to login again")
                        session_string = None
                except Exception as e:
                    logger.warning(f"Error restoring session: {str(e)}")
                    session_string = None
            else:
                logger.info("No valid session found in MongoDB")
                session_string = None

            if not session_string:
                logger.info("Starting new login process...")
                if not self.api_id or not self.api_hash:
                    logger.error("Missing API credentials")
                    return False

                session = StringSession()
                self.client = TelegramClient(session, self.api_id, self.api_hash)
                # await self.client.start(
                #     phone=self.phone, code_callback=self._code_callback
                # )  # type: ignore

                if await self.client.is_user_authorized():
                    session_string = session.save()
                    logger.debug(f"Session string type: {type(session_string)}")
                    logger.debug(
                        f"Session string length: {len(session_string) if session_string else 0}"
                    )

                    if session_string:
                        if await self._save_session(self.phone, session_string):
                            logger.info("Successfully logged in to Telegram")
                        else:
                            logger.warning("Login successful but failed to save session")
                    else:
                        logger.warning("Could not extract session string, but login successful")

                    return True
                else:
                    logger.error("Failed to login. Please check your credentials")
                    return False

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False

        return False

    def _code_callback(self):
        return input("Enter the code you received: ")

    async def get_user_groups(self) -> List[Dict]:
        try:
            if not self.client:
                logger.error("Client not initialized")
                return []

            logger.info("Fetching user groups...")
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

                    if await self._save_group(group_info):
                        logger.info(f"  {group_info['title']} (ID: {group_info['id']})")
                    else:
                        logger.warning(f"Failed to save group: {group_info['title']}")

            logger.info(f"Found {len(groups)} groups")
            return groups

        except Exception as e:
            logger.error(f"Error fetching groups: {str(e)}")
            return []

    async def get_group_messages_by_date_range(
        self,
        group: Dict,
        start_date: datetime,
        end_date: datetime,
        chunk_size: int = 1000,
    ) -> List[Dict]:
        try:
            if not self.client:
                logger.error("Client not initialized")
                return []

            logger.info(f"Getting messages for group: {group}")
            logger.info(
                f"Fetching messages from {start_date.strftime('%Y-%m-%d %H:%M:%S')} to {end_date.strftime('%Y-%m-%d %H:%M:%S')} in chunks of {chunk_size}..."
            )

            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)

            logger.info(
                f"Date range: {start_date.strftime('%Y-%m-%d %H:%M:%S')} to {end_date.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            try:
                is_megagroup = group.get("is_megagroup", False)
                entity_type = group.get("entity_type", "Chat")

                if entity_type == "Channel":
                    is_megagroup = True

                logger.info(
                    f"Group info - ID: {group['id']}, Entity Type: {entity_type}, Is Megagroup: {is_megagroup}"
                )

                if is_megagroup or entity_type == "Channel":
                    entity_id = -abs(group["id"])
                    logger.info(f"Using PeerChannel with negative ID: {entity_id}")
                    channel = await self.client.get_entity(PeerChannel(entity_id))
                else:
                    logger.info(f"Using PeerChat with positive ID: {group['id']}")
                    channel = await self.client.get_entity(PeerChat(group["id"]))
            except Exception as e:
                logger.warning(f"Error getting entity with specific peer type: {e}")
                try:
                    channel = await self.client.get_entity(group["id"])
                except Exception as fallback_error1:
                    logger.warning(f"Failed to get entity with original ID: {fallback_error1}")
                    try:
                        negative_id = -abs(group["id"])
                        logger.info(f"Trying with negative ID: {negative_id}")
                        channel = await self.client.get_entity(negative_id)
                    except Exception as fallback_error2:
                        logger.error(f"Failed to get entity with negative ID: {fallback_error2}")
                        try:
                            logger.info("Trying final fallback with PeerChannel")
                            channel = await self.client.get_entity(PeerChannel(-abs(group["id"])))
                        except Exception as final_error:
                            logger.error(f"All attempts to get entity failed: {final_error}")
                            return []

            logger.info(f"Channel: {channel}")

            all_messages = []
            total_message_count = 0
            chunk_count = 0

            try:
                offset_id = 0

                while True:
                    chunk_messages = []
                    chunk_message_count = 0

                    logger.info(f"Fetching chunk {chunk_count + 1} (offset_id: {offset_id})")

                    async for message in self.client.iter_messages(
                        channel,  # type: ignore
                        limit=chunk_size,
                        offset_id=offset_id if offset_id > 0 else 0,
                    ):
                        chunk_message_count += 1
                        total_message_count += 1

                        message_date = message.date
                        if message_date.tzinfo is None:
                            message_date = message_date.replace(tzinfo=timezone.utc)

                        if message_date < start_date:
                            logger.info(
                                f"Reached messages older than start date {start_date.strftime('%Y-%m-%d %H:%M:%S')}, stopping fetch"
                            )
                            break

                        if start_date <= message_date <= end_date:
                            if message.text:
                                message_info = {
                                    "id": message.id,
                                    "text": message.text,
                                    "date": message.date,
                                    "sender_id": message.sender_id,
                                    "sender_name": None,
                                }

                                if message.sender:
                                    first_name = (
                                        getattr(message.sender, "first_name", "") or ""
                                    ).strip()
                                    last_name = (
                                        getattr(message.sender, "last_name", "") or ""
                                    ).strip()
                                    message_info["sender_name"] = (
                                        f"{first_name} {last_name}".strip()
                                        or f"User_{message.sender_id}"
                                    )
                                elif message.sender_id:
                                    try:
                                        sender = await self.client.get_entity(message.sender_id)
                                        first_name = (
                                            getattr(sender, "first_name", "") or ""
                                        ).strip()
                                        last_name = (getattr(sender, "last_name", "") or "").strip()
                                        message_info["sender_name"] = (
                                            f"{first_name} {last_name}".strip()
                                            or f"User_{message.sender_id}"
                                        )
                                    except Exception as e:
                                        logger.debug(
                                            f"Could not resolve sender for ID {message.sender_id}: {e}"
                                        )
                                        message_info["sender_name"] = f"User_{message.sender_id}"
                                else:
                                    message_info["sender_name"] = "Unknown"

                                chunk_messages.append(message_info)

                        offset_id = message.id

                    if chunk_messages:
                        chunk_count += 1
                        logger.info(
                            f"Processing chunk {chunk_count} with {len(chunk_messages)} messages"
                        )

                        result = await self._save_messages(group["id"], chunk_messages)
                        logger.info(
                            f"Chunk {chunk_count}: Saved {result['saved']} new messages, skipped {result['skipped']} existing messages"
                        )

                        all_messages.extend(chunk_messages)

                        logger.info(f"Total messages processed so far: {len(all_messages)}")

                    if chunk_message_count < chunk_size:
                        logger.info(
                            f"Reached end of available messages (got {chunk_message_count} messages)"
                        )
                        break

                    if not chunk_messages:
                        logger.info("No more messages to fetch")
                        break

                logger.info(
                    f"Retrieved {len(all_messages)} total messages from {total_message_count} total messages processed"
                )

                return all_messages

            except Exception as e:
                logger.warning(f"Error fetching fresh messages: {str(e)}")
                try:
                    logger.info("Trying fallback: fetching recent messages without date filter...")
                    messages = []
                    async for message in self.client.iter_messages(
                        channel,  # type: ignore
                        limit=50,
                    ):
                        logger.info(f"Message: {message}")
                        if message.text:
                            message_info = {
                                "id": message.id,
                                "text": message.text,
                                "date": message.date,
                                "sender_id": message.sender_id,
                                "sender_name": None,
                            }

                            if message.sender:
                                first_name = (
                                    getattr(message.sender, "first_name", "") or ""
                                ).strip()
                                last_name = (getattr(message.sender, "last_name", "") or "").strip()
                                message_info["sender_name"] = (
                                    f"{first_name} {last_name}".strip()
                                    or f"User_{message.sender_id}"
                                )
                            elif message.sender_id:
                                try:
                                    sender = await self.client.get_entity(message.sender_id)
                                    first_name = (getattr(sender, "first_name", "") or "").strip()
                                    last_name = (getattr(sender, "last_name", "") or "").strip()
                                    message_info["sender_name"] = (
                                        f"{first_name} {last_name}".strip()
                                        or f"User_{message.sender_id}"
                                    )
                                except Exception as e:
                                    logger.debug(
                                        f"Could not resolve sender for ID {message.sender_id}: {e}"
                                    )
                                    message_info["sender_name"] = f"User_{message.sender_id}"
                            else:
                                message_info["sender_name"] = "Unknown"

                            messages.append(message_info)

                    if messages:
                        logger.info(f"Retrieved {len(messages)} messages (fallback method)")
                        result = await self._save_messages(group["id"], messages)
                        logger.info(
                            f"Saved {result['saved']} new messages, skipped {result['skipped']} existing messages"
                        )
                        return messages
                    else:
                        logger.error("No messages found even with fallback")
                        return []

                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {str(fallback_error)}")
                    return []

        except Exception as e:
            logger.error(f"Error in get_group_messages_by_date_range: {str(e)}")
            return []

    async def get_group_messages(
        self, group: Dict, days: int = 60, chunk_size: int = 100
    ) -> List[Dict]:
        try:
            if not self.client:
                logger.error("Client not initialized")
                return []

            logger.info(f"Getting messages for group: {group}")
            logger.info(f"Fetching messages from the last {days} days in chunks of {chunk_size}...")

            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)

            logger.info(
                f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            )

            cached_messages = await self._get_cached_messages(group["id"], days)

            try:
                is_megagroup = group.get("is_megagroup", False)
                entity_type = group.get("entity_type", "Chat")

                if entity_type == "Channel":
                    is_megagroup = True

                logger.info(
                    f"Group info - ID: {group['id']}, Entity Type: {entity_type}, Is Megagroup: {is_megagroup}"
                )

                if is_megagroup or entity_type == "Channel":
                    entity_id = -abs(group["id"])
                    logger.info(f"Using PeerChannel with negative ID: {entity_id}")
                    channel = await self.client.get_entity(PeerChannel(entity_id))
                else:
                    logger.info(f"Using PeerChat with positive ID: {group['id']}")
                    channel = await self.client.get_entity(PeerChat(group["id"]))
            except Exception as e:
                logger.warning(f"Error getting entity with specific peer type: {e}")
                try:
                    channel = await self.client.get_entity(group["id"])
                except Exception as fallback_error1:
                    logger.warning(f"Failed to get entity with original ID: {fallback_error1}")
                    try:
                        negative_id = -abs(group["id"])
                        logger.info(f"Trying with negative ID: {negative_id}")
                        channel = await self.client.get_entity(negative_id)
                    except Exception as fallback_error2:
                        logger.error(f"Failed to get entity with negative ID: {fallback_error2}")
                        try:
                            logger.info("Trying final fallback with PeerChannel")
                            channel = await self.client.get_entity(PeerChannel(-abs(group["id"])))
                        except Exception as final_error:
                            logger.error(f"All attempts to get entity failed: {final_error}")
                            return []

            logger.info(f"Channel: {channel}")

            all_messages = []
            total_message_count = 0
            chunk_count = 0

            try:
                offset_id = 0

                while True:
                    chunk_messages = []
                    chunk_message_count = 0

                    logger.info(f"Fetching chunk {chunk_count + 1} (offset_id: {offset_id})")

                    async for message in self.client.iter_messages(
                        channel,  # type: ignore
                        limit=chunk_size,
                        offset_id=offset_id if offset_id > 0 else 0,
                    ):
                        chunk_message_count += 1
                        total_message_count += 1

                        message_date = message.date
                        if message_date.tzinfo is None:
                            message_date = message_date.replace(tzinfo=timezone.utc)

                        if message_date < start_date:
                            logger.info(f"Reached messages older than {days} days, stopping fetch")
                            break

                        if message.text:
                            message_info = {
                                "id": message.id,
                                "text": message.text,
                                "date": message.date,
                                "sender_id": message.sender_id,
                                "sender_name": None,
                            }

                            if message.sender:
                                first_name = (
                                    getattr(message.sender, "first_name", "") or ""
                                ).strip()
                                last_name = (getattr(message.sender, "last_name", "") or "").strip()
                                message_info["sender_name"] = (
                                    f"{first_name} {last_name}".strip()
                                    or f"User_{message.sender_id}"
                                )
                            elif message.sender_id:
                                try:
                                    sender = await self.client.get_entity(message.sender_id)
                                    first_name = (getattr(sender, "first_name", "") or "").strip()
                                    last_name = (getattr(sender, "last_name", "") or "").strip()
                                    message_info["sender_name"] = (
                                        f"{first_name} {last_name}".strip()
                                        or f"User_{message.sender_id}"
                                    )
                                except Exception as e:
                                    logger.debug(
                                        f"Could not resolve sender for ID {message.sender_id}: {e}"
                                    )
                                    message_info["sender_name"] = f"User_{message.sender_id}"
                            else:
                                message_info["sender_name"] = "Unknown"

                            chunk_messages.append(message_info)

                            offset_id = message.id

                    if chunk_messages:
                        chunk_count += 1
                        logger.info(
                            f"Processing chunk {chunk_count} with {len(chunk_messages)} messages"
                        )

                        result = await self._save_messages(group["id"], chunk_messages)
                        logger.info(
                            f"Chunk {chunk_count}: Saved {result['saved']} new messages, skipped {result['skipped']} existing messages"
                        )

                        all_messages.extend(chunk_messages)

                        logger.info(f"Total messages processed so far: {len(all_messages)}")

                    if chunk_message_count < chunk_size:
                        logger.info(
                            f"Reached end of available messages (got {chunk_message_count} messages)"
                        )
                        break

                    if not chunk_messages:
                        logger.info("No more messages to fetch")
                        break

                logger.info(
                    f"Retrieved {len(all_messages)} total messages from {total_message_count} total messages processed"
                )

                return all_messages

            except Exception as e:
                logger.warning(f"Error fetching fresh messages: {str(e)}")
                try:
                    logger.info("Trying fallback: fetching recent messages without date filter...")
                    messages = []
                    async for message in self.client.iter_messages(
                        channel,  # type: ignore
                        limit=50,
                    ):
                        logger.info(f"Message: {message}")
                        if message.text:
                            message_info = {
                                "id": message.id,
                                "text": message.text,
                                "date": message.date,
                                "sender_id": message.sender_id,
                                "sender_name": None,
                            }

                            if message.sender:
                                first_name = (
                                    getattr(message.sender, "first_name", "") or ""
                                ).strip()
                                last_name = (getattr(message.sender, "last_name", "") or "").strip()
                                message_info["sender_name"] = (
                                    f"{first_name} {last_name}".strip()
                                    or f"User_{message.sender_id}"
                                )
                            elif message.sender_id:
                                try:
                                    sender = await self.client.get_entity(message.sender_id)
                                    first_name = (getattr(sender, "first_name", "") or "").strip()
                                    last_name = (getattr(sender, "last_name", "") or "").strip()
                                    message_info["sender_name"] = (
                                        f"{first_name} {last_name}".strip()
                                        or f"User_{message.sender_id}"
                                    )
                                except Exception as e:
                                    logger.debug(
                                        f"Could not resolve sender for ID {message.sender_id}: {e}"
                                    )
                                    message_info["sender_name"] = f"User_{message.sender_id}"
                            else:
                                message_info["sender_name"] = "Unknown"

                            messages.append(message_info)

                    if messages:
                        logger.info(f"Retrieved {len(messages)} messages (fallback method)")
                        result = await self._save_messages(group["id"], messages)
                        logger.info(
                            f"Saved {result['saved']} new messages, skipped {result['skipped']} existing messages"
                        )
                        return messages
                    else:
                        logger.error("No messages found even with fallback")
                        return []

                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {str(fallback_error)}")
                    if cached_messages:
                        logger.info("Using cached messages from MongoDB")
                        return cached_messages
                    else:
                        logger.error("No messages available")
                        return []

        except Exception as e:
            logger.error(f"Error in get_group_messages: {str(e)}")
            return []

    async def select_group(self, groups: List[Dict]) -> Optional[Dict]:
        if not groups:
            logger.error("No groups available")
            return None

        logger.info("Available groups:")
        for i, group in enumerate(groups, 1):
            logger.info(f"  {i}. {group['title']}")

        while True:
            try:
                choice = 0
                if 0 <= choice < len(groups):
                    selected_group = groups[choice]
                    logger.info(f"Selected: {selected_group['title']}")
                    return selected_group
                else:
                    logger.error("Invalid choice. Please try again.")
            except ValueError:
                logger.error("Please enter a valid number.")

    async def _get_group_metadata(self, group_id: int) -> Dict:
        """Get group metadata from the groups collection"""
        try:
            group_info = await self.mongo_manager.find_one(
                "groups",
                {"group_id": group_id},
            )

            if group_info:
                return {
                    "group_title": group_info.get("title", "Unknown"),
                    "group_type": group_info.get("group_type", "unknown"),
                    "group_category": group_info.get("group_category", "unknown"),
                    "size_category": group_info.get("size_category", "unknown"),
                }
            else:
                return {
                    "group_title": "Unknown",
                    "group_type": "unknown",
                    "group_category": "unknown",
                    "size_category": "unknown",
                }
        except Exception as e:
            logger.error(f"Error getting group metadata: {str(e)}")
            return {
                "group_title": "Unknown",
                "group_type": "unknown",
                "group_category": "unknown",
                "size_category": "unknown",
            }
