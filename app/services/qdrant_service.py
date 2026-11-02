import os
import qdrant_client
from llama_index.vector_stores.qdrant import QdrantVectorStore
from app.core.config import settings
from app.core.logging import logger


class VectorDatabaseManager:
    def __init__(self):
        self.sync_client = None
        self.async_client = None
        self.vector_store = None
        self.setup_clients()

    def setup_clients(self):
        try:
            if settings.qdrant_url and not settings.qdrant_url.startswith("local"):
                self.sync_client = qdrant_client.QdrantClient(
                    url=settings.qdrant_url,
                    timeout=settings.qdrant_timeout,
                    check_compatibility=False
                )
                self.async_client = qdrant_client.AsyncQdrantClient(
                    url=settings.qdrant_url,
                    timeout=settings.qdrant_timeout,
                    check_compatibility=False
                )
                logger.info(f"Connected to Qdrant cluster at {settings.qdrant_url}")
            else:
                os.makedirs(settings.qdrant_storage_path, exist_ok=True)
                self.sync_client = qdrant_client.QdrantClient(
                    path=settings.qdrant_storage_path,
                    timeout=settings.qdrant_timeout,
                    check_compatibility=False
                )
                self.async_client = qdrant_client.AsyncQdrantClient(
                    path=settings.qdrant_storage_path,
                    timeout=settings.qdrant_timeout,
                    check_compatibility=False
                )
                logger.info(f"Using local file-based Qdrant storage at {settings.qdrant_storage_path}")

            self.vector_store = QdrantVectorStore(
                client=self.sync_client,
                aclient=self.async_client,
                collection_name=settings.qdrant_collection,
                enable_hybrid=settings.enable_hybrid_search
            )
        except Exception as error:
            logger.error(f"Failed to initialize Qdrant vector store: {error}")
            self.sync_client = qdrant_client.QdrantClient(
                location=":memory:",
                timeout=settings.qdrant_timeout,
                check_compatibility=False
            )
            self.vector_store = QdrantVectorStore(
                client=self.client,
                collection_name=self.collection_name,
                enable_hybrid=False # Add this if you don't want fastembed sparse vectors
            )
            logger.warning("Fell back to in-memory Qdrant instance")

    async def is_healthy(self) -> bool:
        try:
            if self.async_client:
                collections_response = await self.async_client.get_collections()
                collection_names = [col.name for col in collections_response.collections]
                return settings.qdrant_collection in collection_names
            collections_response = self.sync_client.get_collections()
            collection_names = [col.name for col in collections_response.collections]
            return settings.qdrant_collection in collection_names
        except Exception as check_error:
            logger.warning(f"Health check failed on Qdrant: {check_error}")
            return False


database_manager = VectorDatabaseManager()
