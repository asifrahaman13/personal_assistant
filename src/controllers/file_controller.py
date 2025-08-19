from pathlib import Path
import re
import shutil
from typing import Any, Dict, Optional

from fastapi import UploadFile
import PyPDF2

from src.config.config import config
from src.core.rag.qdrant import SemanticEmbeddingService, SemanticQdrantService, SemanticSearchRepo
from src.db.mongodb import MongoDBManager
from src.logs.logs import logger


class FileController:
    def __init__(self) -> None:
        self.upload_docs_dir = Path("src/uploads/docs")
        self.upload_docs_dir.mkdir(parents=True, exist_ok=True)

        self.upload_image_dir = Path("src/uploads/images")
        self.upload_image_dir.mkdir(parents=True, exist_ok=True)

        self.mongo_manager = MongoDBManager()
        self.embedding_service = SemanticEmbeddingService()
        self.qdrant_service = SemanticQdrantService(
            url=config.QDRANT_API_URL, api_key=config.QDRANT_API_KEY
        )
        self.search_repo = SemanticSearchRepo(self.embedding_service, self.qdrant_service)

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        text = ""
        with open(pdf_file, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text

    def chunk_text(self, text: str, chunk_size: int = 50) -> list[str]:
        words = re.split(r"\s+", text.strip())
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i : i + chunk_size])
            if chunk:  # skip empty chunks
                chunks.append(chunk)
        return chunks

    async def process_embeddings(
        self,
        current_org: Dict[str, Any],
        file: UploadFile,
        file_type: str,
        description: Optional[str] = None,
    ) -> bool:
        try:
            organization = await self.mongo_manager.find_one(
                "organizations", {"email": current_org["email"]}
            )

            logger.info(f"The organizatin is: {current_org}")

            if organization is None:
                return False

            organization_id = organization.get("id", "")
            file_name = f"{organization_id}_{file.filename}"

            logger.info(f"The file name is: {file_name}")

            if file_type == "image":
                file_path = self.upload_image_dir / f"{file_name}"

                sample_metadata = [
                    {
                        "image_id": "9374162095873412",
                        "account_id": organization.get("id"),
                        "type": "image",
                        "path": file_path,
                    }
                ]  # replicate metadata for each chunk

                print("=== Sample Use Cases for Semantic Search ===")

                try:
                    collection_name = "personal_assistant"
                    if not self.qdrant_service.collection_exists(collection_name):
                        print(f"Creating collection '{collection_name}'...")
                        self.qdrant_service.create_collection(collection_name)
                        print(f"✓ Collection '{collection_name}' created successfully")
                    else:
                        print(f"✓ Collection '{collection_name}' already exists")
                    await self.search_repo.initialize_qdrant_async([description], sample_metadata)  # type: ignore
                    print("✓ Successfully upserted PDF chunks to Qdrant")
                except Exception as e:
                    print(f"✗ Error upserting texts: {e}")

                return True

            else:
                file_path = self.upload_docs_dir / f"{file_name}"  # type: ignore
                logger.info(f"The file path is: {file_path}")
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                print(f"Extracting text from {file_path}...")
                pdf_text = self.extract_text_from_pdf(file_path)  # type: ignore

                sample_texts = self.chunk_text(pdf_text, chunk_size=50)
                print(f"Extracted {len(sample_texts)} chunks from PDF")

                sample_metadata = [
                    {
                        "pdf_id": "8374162095873412",
                        "account_id": organization.get("id"),
                        "type": "docs",
                        "path": file_path,
                    }
                ] * len(sample_texts)  # replicate metadata for each chunk

                print("=== Sample Use Cases for Semantic Search ===")

                try:
                    collection_name = "personal_assistant"
                    if not self.qdrant_service.collection_exists(collection_name):
                        print(f"Creating collection '{collection_name}'...")
                        self.qdrant_service.create_collection(collection_name)
                        print(f"✓ Collection '{collection_name}' created successfully")
                    else:
                        print(f"✓ Collection '{collection_name}' already exists")
                    await self.search_repo.initialize_qdrant_async(sample_texts, sample_metadata)
                    print("✓ Successfully upserted PDF chunks to Qdrant")
                except Exception as e:
                    print(f"✗ Error upserting texts: {e}")

                return True

        except Exception as e:
            return False
