import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.db.mongodb import MongoDBManager


@pytest_asyncio.fixture
async def mongo_manager():
    with patch("src.db.mongodb.AsyncIOMotorClient", autospec=True):
        mongo_manager = MongoDBManager(mongo_uri="mongodb://test", db_name="test_db")
        mongo_manager.db = AsyncMock()
        mongo_manager = mongo_manager.db["test"]
        yield mongo_manager


@pytest.mark.asyncio
async def test_insert_one_success(mongo_manager):
    mongo_manager.insert_one = AsyncMock(return_value=True)
    result = await mongo_manager.insert_one("test", {"a": 1})
    assert result is True


@pytest.mark.asyncio
async def test_insert_many_success(mongo_manager):
    mongo_manager.insert_many = AsyncMock(return_value=0)
    documents = [{"name": "Francisco", "age": 23}, {"name": "Jonathon", "age": 26}]
    result = await mongo_manager.insert_many("test", documents)
    assert result == 0


@pytest.mark.asyncio
async def test_find_one_success(mongo_manager):
    document = {"name": "Francisco", "age": 23}
    mongo_manager.find_one = AsyncMock(return_value=document)
    filter = {"name", "Francisco"}
    result = await mongo_manager.find_one("test", filter)
    assert result == document


@pytest.mark.asyncio
async def test_update_one_success(mongo_manager):
    mongo_manager.update_one = AsyncMock(return_value=True)
    result = await mongo_manager.update_one("test", {"name": "Francisco"}, {"age": 24})
    assert result is True


@pytest.mark.asyncio
async def test_update_many_success(mongo_manager):
    mongo_manager.update_many = AsyncMock(return_value=2)
    result = await mongo_manager.update_many("test", {"age": {"$lt": 30}}, {"active": True})
    assert result == 2


@pytest.mark.asyncio
async def test_delete_one_success(mongo_manager):
    mongo_manager.delete_one = AsyncMock(return_value=True)
    result = await mongo_manager.delete_one("test", {"name": "Francisco"})
    assert result is True


@pytest.mark.asyncio
async def test_delete_many_success(mongo_manager):
    mongo_manager.delete_many = AsyncMock(return_value=3)
    result = await mongo_manager.delete_many("test", {"active": False})
    assert result == 3


@pytest.mark.asyncio
async def test_count_documents_success(mongo_manager):
    mongo_manager.count_documents = AsyncMock(return_value=5)
    result = await mongo_manager.count_documents("test", {"active": True})
    assert result == 5


@pytest.mark.asyncio
async def test_bulk_write_success(mongo_manager):
    mongo_manager.bulk_write = AsyncMock(return_value=2)
    operations = [{"filter": {"name": "Francisco"}, "update": {"$set": {"age": 25}}}]
    result = await mongo_manager.bulk_write("test", operations)
    assert result == 2


@pytest.mark.asyncio
async def test_bulk_write_optimized_success(mongo_manager):
    mongo_manager.bulk_write_optimized = AsyncMock(return_value=2)
    operations = [{"filter": {"name": "Francisco"}, "update": {"$set": {"age": 25}}}]
    result = await mongo_manager.bulk_write_optimized("test", operations, batch_size=1)
    assert result == 2


def test_close_success(mongo_manager):
    mongo_manager.close = Mock()
    mongo_manager.close()
    mongo_manager.close.assert_called_once()
