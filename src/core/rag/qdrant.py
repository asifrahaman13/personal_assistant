import asyncio
from collections import OrderedDict
from typing import List, Optional
import uuid

import google.genai as genai
from google.genai import types
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct, ScoredPoint

from src.config.config import config
from src.logs.logs import logger


class SemanticEmbeddingService:
    def __init__(self, cache_size: int = 1000) -> None:
        self.embeddings_cache: OrderedDict[str, List[float]] = OrderedDict()
        self.cache_size = cache_size
        self.api_key = config.GEMINI_API_KEY  # type: ignore
        if not self.api_key:
            logger.error("GEMINI_API_KEY not available")
            self.client = None
            return

        try:
            self.client = genai.Client(api_key=self.api_key)
            self.async_client = self.client.aio
            logger.info("Google GenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google GenAI client: {str(e)}")
            self.client = None
            self.async_client = None

    async def get_embeddings(self, text: str) -> List[float]:
        if text in self.embeddings_cache:
            self.embeddings_cache.move_to_end(text)
            return self.embeddings_cache[text]
        else:
            try:
                if not self.client or not self.async_client:
                    logger.error("Google GenAI client not initialized")
                    return []

                # Create content
                content = types.Content(parts=[types.Part(text=text)])

                # Create embedding config
                embedding_config = types.EmbedContentConfig(output_dimensionality=768)

                response = await self.async_client.models.embed_content(
                    model="models/embedding-001", contents=[content], config=embedding_config
                )

                if response.embeddings and len(response.embeddings) > 0:
                    embedding_values = response.embeddings[0].values
                    if embedding_values:
                        embeddings = list(embedding_values)
                        self.embeddings_cache[text] = embeddings
                        logger.info(f"Embedding for text (length: {len(text)}) completed")
                        if len(self.embeddings_cache) > self.cache_size:
                            self.embeddings_cache.popitem(last=False)
                        return embeddings
                    else:
                        logger.error("No values in embedding")
                        return []
                else:
                    logger.error("No embedding in response")
                    return []

            except Exception as e:
                logger.error(f"Error getting embeddings: {str(e)}")
                return []

    async def get_embeddings_async(self, text: str) -> List[float]:
        if text in self.embeddings_cache:
            self.embeddings_cache.move_to_end(text)
            return self.embeddings_cache[text]
        else:
            try:
                if not self.client or not self.async_client:
                    logger.error("Google GenAI client not initialized")
                    return []

                # Create content
                content = types.Content(parts=[types.Part(text=text)])

                # Create embedding config
                embedding_config = types.EmbedContentConfig(output_dimensionality=768)

                response = await self.async_client.models.embed_content(
                    model="models/embedding-001", contents=[content], config=embedding_config
                )

                if response.embeddings and len(response.embeddings) > 0:
                    embedding_values = response.embeddings[0].values
                    if embedding_values:
                        embeddings = list(embedding_values)
                        self.embeddings_cache[text] = embeddings
                        logger.info(f"Async embedding for text (length: {len(text)}) completed")
                        if len(self.embeddings_cache) > self.cache_size:
                            self.embeddings_cache.popitem(last=False)
                        return embeddings
                    else:
                        logger.error("No values in embedding")
                        return []
                else:
                    logger.error("No embedding in response")
                    return []

            except Exception as e:
                logger.error(f"Error getting async embeddings: {str(e)}")
                return []


class SemanticQdrantService:
    def __init__(self, url: str, api_key: str) -> None:
        self.client = QdrantClient(url=url, api_key=api_key)

    def collection_exists(self, collection_name: str) -> bool:
        try:
            response = self.client.get_collection(collection_name)
            return response is not None
        except Exception:
            return False

    def create_collection(self, collection_name: str) -> None:
        if not self.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=768, distance=Distance.COSINE
                ),  # Using 768 dimensions
            )

    def upsert_points(self, collection_name: str, points: list[PointStruct]) -> None:
        self.client.upsert(collection_name=collection_name, points=points)

    def search(
        self,
        query_embedding: list[float],
        owner_id: str,
        telegram_group_id: str,
        account_id: str,
        limit: int = 5,
    ) -> list[ScoredPoint]:
        # For now, search without filters to avoid index issues
        # TODO: Add proper index creation for owner_id, telegram_group_id, and account_id fields
        return self.client.search(
            collection_name="telegram_analyzer",
            query_vector=query_embedding,
            limit=limit,
        )


class SemanticSearchRepo:
    def __init__(
        self,
        embedding_service: SemanticEmbeddingService,
        qdrant_service: SemanticQdrantService,
    ):
        self.embedding_service = embedding_service
        self.qdrant_service = qdrant_service

    async def prepare_points(self, texts: list[str], metadata: list[dict]) -> list[PointStruct]:
        points = []
        for text, meta in zip(texts, metadata):
            embedding = await self.embedding_service.get_embeddings(text)
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={"text": text, **meta},
                )
            )
        return points

    async def prepare_points_async(
        self, texts: list[str], metadata: list[dict], semaphore: Optional[asyncio.Semaphore] = None
    ) -> list[PointStruct]:
        if semaphore is None:
            semaphore = asyncio.Semaphore(25)

        async def process_batch(
            batch_texts: list[str], batch_metadata: list[dict]
        ) -> list[PointStruct]:
            async with semaphore:
                tasks = []
                for text, meta in zip(batch_texts, batch_metadata):
                    task = self.embedding_service.get_embeddings_async(text)
                    tasks.append(task)

                embeddings = await asyncio.gather(*tasks)

                return [
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector=embedding,
                        payload={"text": text, **meta},
                    )
                    for text, meta, embedding in zip(batch_texts, batch_metadata, embeddings)
                ]

        # Process in batches of 25
        batch_size = 25
        all_points = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_metadata = metadata[i : i + batch_size]

            batch_points = await process_batch(batch_texts, batch_metadata)
            all_points.extend(batch_points)

            logger.info(
                f"Processed batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}"
            )

        return all_points

    async def create_collection(self, collection_name: str, embedding_dim: int = 768) -> None:
        collection_exists = self.qdrant_service.client.collection_exists(
            collection_name=collection_name
        )
        if collection_exists is False:
            self.qdrant_service.client.create_collection(
                collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_dim, distance=models.Distance.COSINE
                ),
            )

    async def initialize_qdrant(self, texts: list[str], metadata: list[dict[str, str]]) -> bool:
        try:
            points = await self.prepare_points(texts, metadata)
            result = self.qdrant_service.upsert_points("telegram_analyzer", points)
            logger.info(f"The  upserted points results: {result}")
            return True
        except Exception as e:
            logger.error(f"The error is as follows: {e}")
            return False

    async def initialize_qdrant_async(
        self, texts: list[str], metadata: list[dict[str, str]]
    ) -> bool:
        semaphore = asyncio.Semaphore(25)

        logger.info("Starting async batch processing...")
        start_time = asyncio.get_event_loop().time()

        points = await self.prepare_points_async(texts, metadata, semaphore)

        processing_time = asyncio.get_event_loop().time() - start_time
        logger.info(f"Async embedding processing completed in {processing_time:.2f} seconds")

        result = self.qdrant_service.upsert_points("telegram_analyzer", points)
        logger.info(f"Upsert result: {result}")
        return True

    async def query_text(
        self,
        query_text: str,
        owner_id: str,
        telegram_group_id: str,
        account_id: str,
        threshold: float = 0.5,
    ) -> list[dict]:
        try:
            query_embedding = await self.embedding_service.get_embeddings(query_text)
            response = self.qdrant_service.search(
                query_embedding, owner_id, telegram_group_id, account_id
            )
            logger.info(f"Query: {query_text}")
            result = []

            logger.info(f"Response: {response}")
            for data in response:
                if data.score > threshold and data.payload:
                    result.append(
                        {
                            "score": data.score,
                            "text": data.payload.get("text", ""),
                            "metadata": data.payload,
                        }
                    )
            return result
        except Exception as e:
            logger.error(f"Failed to search: {e}")
            return []
