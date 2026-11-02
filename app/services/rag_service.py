import os
import re
import urllib.parse
from llama_index.core import VectorStoreIndex
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from app.core.config import settings
from app.core.logging import logger
from app.models.schemas import SourceItem, QueryResponse
from app.services.qdrant_service import database_manager


class KnowledgeQueryEngine:
    def __init__(self):
        self.language_model = None
        self.embedding_model = None
        self.knowledge_index = None
        self.query_engine = None
        self.initialize_models()

    def initialize_models(self):
        try:
            self.language_model = Ollama(
                model=settings.llm_model,
                base_url=settings.ollama_base_url,
                request_timeout=settings.llm_request_timeout
            )
            self.embedding_model = OllamaEmbedding(
                model_name=settings.embedding_model,
                base_url=settings.ollama_base_url
            )
            self.knowledge_index = VectorStoreIndex.from_vector_store(
                vector_store=database_manager.vector_store,
                embed_model=self.embedding_model
            )
            self.query_engine = self.knowledge_index.as_query_engine(
                llm=self.language_model,
                similarity_top_k=settings.similarity_top_k
            )
            logger.info("Knowledge query engine initialized successfully")
        except Exception as setup_error:
            logger.error(f"Failed to initialize query engine: {setup_error}")

    def clean_image_link(self, raw_link: str) -> str:
        if not raw_link:
            return ""
        decoded_link = urllib.parse.unquote(raw_link).strip()
        cleaned_filename = decoded_link.split("/")[-1].split("\\")[-1].strip()
        if not cleaned_filename or cleaned_filename == "local_path_placeholder":
            return ""

        candidates = [
            cleaned_filename,
            f"{cleaned_filename}.png",
            f"{cleaned_filename}).png",
            f"{cleaned_filename}.jpg"
        ]
        actual_file = None
        for candidate in candidates:
            if os.path.exists(os.path.join(settings.images_dir, candidate)):
                actual_file = candidate
                break

        if not actual_file:
            digit_match = re.search(r'\((\d+)\)', decoded_link) or re.search(r'(\d+)', decoded_link)
            if digit_match:
                digit = digit_match.group(1)
                fallback = f"images ({digit}).png"
                if os.path.exists(os.path.join(settings.images_dir, fallback)):
                    actual_file = fallback

        if not actual_file:
            return ""

        quoted_filename = urllib.parse.quote(actual_file)
        return f"{settings.image_base_url}/images/{quoted_filename}"

    def extract_image_details(self, node_text: str, metadata: dict):
        found_url = None
        found_caption = None
        
        if metadata.get("image_url"):
            found_url = self.clean_image_link(str(metadata.get("image_url")))
        if metadata.get("image_caption"):
            found_caption = str(metadata.get("image_caption"))

        markdown_match = re.search(
            r'!\[(.*?)\]\((.+?\.(?:png|jpg|jpeg|webp|svg|gif|bmp)|[^\s\)]+)\)',
            node_text
        )
        if markdown_match:
            caption_text = markdown_match.group(1).strip()
            image_target = markdown_match.group(2).strip()
            cleaned_target = self.clean_image_link(image_target)
            if cleaned_target:
                found_url = found_url or cleaned_target
                found_caption = found_caption or caption_text

        return found_url, found_caption

    async def search_and_synthesize(self, user_question: str, top_k: int = None) -> QueryResponse:
        if not self.query_engine:
            self.initialize_models()

        k_value = top_k or settings.similarity_top_k
        active_engine = self.knowledge_index.as_query_engine(
            llm=self.language_model,
            similarity_top_k=k_value
        )

        query_result = await active_engine.aquery(user_question)
        
        gathered_sources = []
        collected_images = []

        for source_node in getattr(query_result, "source_nodes", []):
            snippet_text = source_node.node.text
            node_metadata = source_node.node.metadata or {}
            node_score = float(source_node.score) if source_node.score is not None else None

            image_address, image_label = self.extract_image_details(snippet_text, node_metadata)
            
            if image_address and image_address not in collected_images:
                collected_images.append(image_address)

            clean_metadata = {
                key: value for key, value in node_metadata.items()
                if isinstance(value, (str, int, float, bool))
            }

            source_item = SourceItem(
                text=snippet_text,
                metadata=clean_metadata,
                score=node_score,
                image_url=image_address,
                image_caption=image_label
            )
            gathered_sources.append(source_item)

        final_answer = str(query_result)

        return QueryResponse(
            question=user_question,
            answer=final_answer,
            sources=gathered_sources,
            images=collected_images
        )


rag_system = KnowledgeQueryEngine()
