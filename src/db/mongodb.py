from typing import Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient

from src.config.config import config


class MongoDBManager:
    def __init__(self, mongo_uri: str = config.MONGODB_URI, db_name: str = config.DB_NAME):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.client = AsyncIOMotorClient(self.mongo_uri)
        self.db = self.client[self.db_name]

    async def setup(self) -> bool:
        try:
            self.client = AsyncIOMotorClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            await self.client.admin.command("ping")
            return True
        except Exception as e:
            return False

    async def create_index(self, collection: str, index_fields: List, unique: bool = False) -> bool:
        try:
            if self.db is None:
                return False
            await self.db[collection].create_index(index_fields, unique=unique)
            return True
        except Exception as e:
            return False

    async def insert_one(self, collection: str, document: Dict) -> bool:
        try:
            if self.db is None:
                return False
            result = await self.db[collection].insert_one(document)
            return True
        except Exception as e:
            return False

    async def insert_many(self, collection: str, documents: List[Dict]) -> int:
        try:
            if self.db is None:
                return 0
            result = await self.db[collection].insert_many(documents)
            return len(result.inserted_ids)
        except Exception as e:
            return 0

    async def find_one(self, collection: str, filter_dict: Dict) -> Optional[Dict]:
        try:
            if self.db is None:
                return None
            result = await self.db[collection].find_one(filter_dict)
            return result
        except Exception as e:
            return None

    async def find_many(
        self,
        collection: str,
        filter_dict: Optional[Dict] = None,
        sort_fields: Optional[List] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        try:
            if self.db is None:
                return []

            cursor = self.db[collection].find(filter_dict or {})

            if sort_fields:
                cursor = cursor.sort(sort_fields)

            if limit:
                cursor = cursor.limit(limit)

            return await cursor.to_list(length=None)
        except Exception as e:
            return []

    async def update_one(
        self,
        collection: str,
        filter_dict: Dict,
        update_dict: Dict,
        upsert: bool = False,
    ) -> bool:
        try:
            if self.db is None:
                return False
            result = await self.db[collection].update_one(
                filter_dict, {"$set": update_dict}, upsert=upsert
            )
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            return False

    async def update_many(self, collection: str, filter_dict: Dict, update_dict: Dict) -> int:
        try:
            if self.db is None:
                return 0
            result = await self.db[collection].update_many(filter_dict, {"$set": update_dict})
            return result.modified_count
        except Exception as e:
            return 0

    async def delete_one(self, collection: str, filter_dict: Dict) -> bool:
        try:
            if self.db is None:
                return False
            result = await self.db[collection].delete_one(filter_dict)
            return result.deleted_count > 0
        except Exception:
            return False

    async def delete_many(self, collection: str, filter_dict: Dict) -> int:
        try:
            if self.db is None:
                return 0
            result = await self.db[collection].delete_many(filter_dict)
            return result.deleted_count
        except Exception as e:
            return 0

    async def count_documents(self, collection: str, filter_dict: Optional[Dict] = None) -> int:
        try:
            if self.db is None:
                return 0
            return await self.db[collection].count_documents(filter_dict or {})
        except Exception as e:
            return 0

    async def bulk_write(self, collection: str, operations: List[Dict]) -> int:
        try:
            if self.db is None:
                return 0

            from pymongo import UpdateOne

            bulk_ops = []
            for op in operations:
                bulk_ops.append(UpdateOne(op["filter"], op["update"], upsert=False))

            if bulk_ops:
                result = await self.db[collection].bulk_write(bulk_ops)
                return result.modified_count
            return 0
        except Exception as e:
            return 0

    async def bulk_write_optimized(
        self, collection: str, operations: List[Dict], batch_size: int = 1000
    ) -> int:
        try:
            if self.db is None:
                return 0

            from pymongo import UpdateOne

            total_modified = 0

            for i in range(0, len(operations), batch_size):
                batch = operations[i : i + batch_size]
                bulk_ops = []

                for op in batch:
                    bulk_ops.append(UpdateOne(op["filter"], op["update"], upsert=False))

                if bulk_ops:
                    result = await self.db[collection].bulk_write(bulk_ops)
                    total_modified += result.modified_count

            return total_modified
        except Exception as e:
            return 0

    def close(self):
        if self.client:
            self.client.close()
