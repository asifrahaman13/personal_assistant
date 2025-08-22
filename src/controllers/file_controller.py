from pathlib import Path
import re
import shutil
from typing import Any, Dict, Optional

from fastapi import UploadFile
import PyPDF2

from src.config.config import config
from src.core import SemanticEmbeddingService, SemanticQdrantService, SemanticSearchRepo
from src.db.mongodb import MongoDBManager
from src.logs.logs import logger
from src.voice.transcription import DeepgramTranscription


class FileController:
    def __init__(self) -> None:
        self.upload_docs_dir = Path("src/uploads/docs")
        self.upload_docs_dir.mkdir(parents=True, exist_ok=True)

        self.upload_image_dir = Path("src/uploads/images")
        self.upload_image_dir.mkdir(parents=True, exist_ok=True)

        self.upload_video_dir = Path("src/uploads/videos")
        self.upload_video_dir.mkdir(parents=True, exist_ok=True)

        self.upload_audio_dir = Path("src/uploads/audios")
        self.upload_audio_dir.mkdir(parents=True, exist_ok=True)

        self.upload_dirs = {
            "docs": self.upload_docs_dir,
            "image": self.upload_image_dir,
            "video": self.upload_video_dir,
            "audio": self.upload_audio_dir,
        }

        self.mongo_manager = MongoDBManager()
        self.embedding_service = SemanticEmbeddingService()
        self.qdrant_service = SemanticQdrantService(
            url=config.QDRANT_API_URL, api_key=config.QDRANT_API_KEY
        )
        self.search_repo = SemanticSearchRepo(self.embedding_service, self.qdrant_service)
        self.deepgram_transcription = DeepgramTranscription()

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
            if not organization:
                logger.warning("Organization not found")
                return False

            org_id = organization.get("id", "")
            file_name = f"{org_id}_{file.filename}"

            if file_type not in self.upload_dirs:
                logger.error(f"Unsupported file type: {file_type}")
                return False

            file_path = self.upload_dirs[file_type] / file_name
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            logger.info(f"Saved {file_type} file: {file_path}")

            sample_texts = []
            if file_type == "docs":
                pdf_text = self.extract_text_from_pdf(file_path)  # type: ignore
                sample_texts = self.chunk_text(pdf_text, chunk_size=50)

            elif file_type == "image":
                sample_texts = [description or file.filename]

            elif file_type == "audio":
                transcription = await self.deepgram_transcription.transcribe(file_path)  # type: ignore
                sample_texts = self.chunk_text(transcription, chunk_size=50)
                sample_texts.extend([description])  # type: ignore

            elif file_type == "video":
                transcription = await self.deepgram_transcription.transcribe(file_path)  # type: ignore
                sample_texts = self.chunk_text(transcription, chunk_size=50)
                sample_texts.extend([description or file.filename])  # type: ignore

            else:
                logger.error(f"Unhandled file type: {file_type}")
                return False

            sample_metadata = [
                {
                    "account_id": org_id,
                    "type": file_type,
                    "path": str(file_path),
                }
            ] * len(sample_texts)

            collection_name = "personal_assistant"
            if not self.qdrant_service.collection_exists(collection_name):
                logger.info(f"Creating collection '{collection_name}'...")
                self.qdrant_service.create_collection(collection_name)
                logger.info(f"✓ Collection '{collection_name}' created successfully")
            else:
                logger.info(f"✓ Collection '{collection_name}' already exists")

            await self.search_repo.initialize_qdrant_async(sample_texts, sample_metadata)  # type: ignore
            logger.info(f"✓ Successfully upserted {len(sample_texts)} chunks for {file_type}")

            return True

        except Exception as e:
            logger.error(f"Error in process_embeddings: {e}", exc_info=True)
            return False
