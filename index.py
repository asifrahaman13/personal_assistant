import asyncio
from collections import OrderedDict
import logging
import os
from typing import List
import uuid

from dotenv import load_dotenv
import google.genai as genai
from google.genai import types
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct, ScoredPoint
from openai import OpenAI

load_dotenv()


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


QDRANT_API_URL = os.getenv("QDRANT_API_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class SemanticEmbeddingService:
    def __init__(self, cache_size: int = 1000) -> None:
        self.embeddings_cache: OrderedDict[str, List[float]] = OrderedDict()
        self.cache_size = cache_size

        if not OPENAI_API_KEY:
            logging.error("OPENAI_API_KEY not available")
            self.client = None
            return

        try:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            logging.info("OpenAI client initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize OpenAI client: {str(e)}")
            self.client = None

    async def get_embeddings(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """Fetch embeddings from OpenAI asynchronously with caching"""
        if text in self.embeddings_cache:
            self.embeddings_cache.move_to_end(text)
            return self.embeddings_cache[text]

        if not self.client:
            logging.error("OpenAI client not initialized")
            return []

        try:
            response = await asyncio.to_thread(
                self.client.embeddings.create, model=model, input=text
            )

            if response and response.data and len(response.data) > 0:
                embeddings = response.data[0].embedding
                self.embeddings_cache[text] = embeddings
                logging.info(f"Embedding for text (length: {len(text)}) completed")

                if len(self.embeddings_cache) > self.cache_size:
                    self.embeddings_cache.popitem(last=False)

                return embeddings
            else:
                logging.error("No embedding in response")
                return []

        except Exception as e:
            logging.error(f"Error getting embeddings: {str(e)}")
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
                    size=1536, distance=Distance.COSINE
                ),  # Using 1536 dimensions
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
            collection_name="personal_assistant",
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
        self, texts: list[str], metadata: list[dict], semaphore: asyncio.Semaphore
    ) -> list[PointStruct]:
        async def process_batch(
            batch_texts: list[str], batch_metadata: list[dict]
        ) -> list[PointStruct]:
            async with semaphore:
                tasks = []
                for text, meta in zip(batch_texts, batch_metadata):
                    task = self.embedding_service.get_embeddings(text)
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

            logging.info(
                f"Processed batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}"
            )

        return all_points

    async def create_collection(self, collection_name: str, embedding_dim: int = 1536) -> None:
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
        points = await self.prepare_points(texts, metadata)
        result = self.qdrant_service.upsert_points("personal_assistant", points)
        print(result)
        return True

    async def initialize_qdrant_async(
        self, texts: list[str], metadata: list[dict[str, str]]
    ) -> bool:
        # Create semaphore to limit concurrent requests to 25
        semaphore = asyncio.Semaphore(25)

        print("Starting async batch processing...")
        start_time = asyncio.get_event_loop().time()

        points = await self.prepare_points_async(texts, metadata, semaphore)

        processing_time = asyncio.get_event_loop().time() - start_time
        print(f"Async embedding processing completed in {processing_time:.2f} seconds")

        result = self.qdrant_service.upsert_points("personal_assistant", points)
        print(f"Upsert result: {result}")
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
            logging.info(f"Query: {query_text}")
            result = []

            logging.info(f"Response: {response}")
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
            logging.error(f"Failed to search: {e}")
            return []


from pathlib import Path
import re
import PyPDF2


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    text = ""
    with open(pdf_file, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text


def chunk_text(text: str, chunk_size: int = 50) -> list[str]:
    """Split text into chunks of `chunk_size` words."""
    words = re.split(r"\s+", text.strip())
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk:  # skip empty chunks
            chunks.append(chunk)
    return chunks


async def main():
    # Initialize services
    embedding_service = SemanticEmbeddingService()
    qdrant_service = SemanticQdrantService(
        url=QDRANT_API_URL,  # Replace with your Qdrant URL # type: ignore
        api_key=QDRANT_API_KEY,  # Replace with your Qdrant API key # type: ignore
    )
    search_repo = SemanticSearchRepo(embedding_service, qdrant_service)

    # === Extract text from PDF ===
    pdf_path = "src/uploads/Recommendation Letter.pdf"
    print(f"Extracting text from {pdf_path}...")
    pdf_text = extract_text_from_pdf(pdf_path)

    # === Chunk text into 50-word segments ===
    sample_texts = chunk_text(pdf_text, chunk_size=50)
    print(f"Extracted {len(sample_texts)} chunks from PDF")

    # Metadata (same for all chunks here, you can customize if needed)
    sample_metadata = [
        {
            "pdf_id": "8374162095873412",
            "account_id": "d29ea384-d96b-46be-aef4-6d3c31b299dd",
        }
    ] * len(sample_texts)  # replicate metadata for each chunk

    print("=== Sample Use Cases for Semantic Search ===")

    # Use Case 1: Initialize Qdrant with PDF chunks
    print("\n1. Initializing Qdrant with PDF chunks...")
    try:
        collection_name = "personal_assistant"
        if not qdrant_service.collection_exists(collection_name):
            print(f"Creating collection '{collection_name}'...")
            qdrant_service.create_collection(collection_name)
            print(f"✓ Collection '{collection_name}' created successfully")
        else:
            print(f"✓ Collection '{collection_name}' already exists")

        await search_repo.initialize_qdrant_async(sample_texts, sample_metadata)
        print("✓ Successfully upserted PDF chunks to Qdrant")
    except Exception as e:
        print(f"✗ Error upserting texts: {e}")

    # Use Case 2: Search for similar texts (owner1, group1)
    print("\n2. Searching for 'machine learning' in owner1's group1...")
    try:
        results = await search_repo.query_text(
            query_text="What is the contact informatin of Tycho",
            owner_id="2847630159284756",
            telegram_group_id="8374162095873412",
            account_id="550e8400-e29b-41d4-a716-446655440000",
            threshold=0.3,
        )
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. Score: {result['score']:.3f}")
            print(f"     Text: {result['text'][:100]}...")
            print(f"     Owner ID: {result['metadata'].get('owner_id', 'N/A')}")
    except Exception as e:
        print(f"✗ Error searching: {e}")

    print("\n=== Sample Use Cases Completed ===")


if __name__ == "__main__":
    asyncio.run(main())
