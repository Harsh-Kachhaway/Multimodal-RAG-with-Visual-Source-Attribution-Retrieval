import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import re
import json
import urllib.parse
from typing import Any
import qdrant_client
from pydantic import BaseModel, Field
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.extractors import BaseExtractor
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.ingestion import IngestionPipeline
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.schema import TextNode
from app.core.config import settings
from app.core.logging import logger


class NCERTMetadata(BaseModel):
    chapter_name: str = Field(description="The main chapter name")
    topic: str = Field(description="The primary topic being discussed")
    subtopic: str = Field(description="The specific subtopic or concept")
    image_referenced: bool = Field(description="True if an image is referenced in the text")


class LocalOllamaExtractor(BaseExtractor):
    llm: Any = Field(description="Local Ollama instance")

    async def aextract(self, nodes):
        for node in nodes:
            prompt = (
                f"Analyze this textbook section and extract the chapter name, topic, and subtopic.\n"
                f"Text: {node.text[:1000]}...\n\n"
                f"Return ONLY valid JSON matching this schema: "
                f'{{"chapter_name": "...", "topic": "...", "subtopic": "...", "image_referenced": true/false}}'
            )
            try:
                response = self.llm.complete(prompt)
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                    node.metadata.update(extracted_data)
            except Exception as extraction_error:
                logger.warning(f"Could not extract metadata via LLM: {extraction_error}")
        return nodes


def locate_textbook_file() -> str:
    candidate_paths = [
        settings.data_file,
        "data/ncert_chapter.md",
        "ncert_chapter.md"
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("Could not find ncert_chapter.md in data or root folder")


def run_ingestion_pipeline():
    book_file_path = locate_textbook_file()
    logger.info(f"Loading textbook content from {book_file_path}")
    
    with open(book_file_path, "r", encoding="utf-8") as book_file:
        book_document = Document(text=book_file.read())

    language_model = Ollama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
        request_timeout=settings.llm_request_timeout
    )
    embedding_model = OllamaEmbedding(
        model_name=settings.embedding_model,
        base_url=settings.ollama_base_url
    )

    if settings.qdrant_url and not settings.qdrant_url.startswith("local"):
        database_client = qdrant_client.QdrantClient(
            url=settings.qdrant_url,
            timeout=settings.qdrant_timeout
        )
    else:
        os.makedirs(settings.qdrant_storage_path, exist_ok=True)
        database_client = qdrant_client.QdrantClient(
            path=settings.qdrant_storage_path,
            timeout=settings.qdrant_timeout
        )

    vector_store = QdrantVectorStore(
        client=database_client,
        collection_name=settings.qdrant_collection,
        enable_hybrid=settings.enable_hybrid_search,
        batch_size=20
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    pipeline = IngestionPipeline(
        transformations=[
            MarkdownNodeParser(),
            LocalOllamaExtractor(llm=language_model),
            embedding_model,
        ]
    )

    logger.info("Processing markdown chunks, extracting metadata, and computing embeddings")
    raw_nodes = pipeline.run(documents=[book_document])
    logger.info(f"Processed {len(raw_nodes)} raw nodes")

    clean_nodes = []
    for raw_node in raw_nodes:
        safe_metadata = {}
        for key, value in raw_node.metadata.items():
            if isinstance(value, (str, int, float, bool)):
                safe_metadata[key] = value

        image_match = re.search(
            r'!\[(.*?)\]\((.+?\.(?:png|jpg|jpeg|webp|svg|gif|bmp)|[^\s\)]+)\)',
            raw_node.text
        )
        if image_match:
            caption_text = image_match.group(1).strip()
            target_file = urllib.parse.unquote(image_match.group(2).strip())
            file_name = target_file.split("/")[-1].strip()
            if file_name.count("(") > file_name.count(")"):
                file_name = f"{file_name})"
            valid_extensions = [".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".bmp"]
            if not any(file_name.endswith(ext) for ext in valid_extensions):
                file_name = f"{file_name}.png"
            safe_metadata["image_referenced"] = True
            safe_metadata["image_caption"] = caption_text
            if file_name and file_name != "local_path_placeholder":
                safe_metadata["image_url"] = f"/images/{file_name}"

        clean_node = TextNode(
            text=raw_node.text,
            metadata=safe_metadata,
            embedding=raw_node.embedding
        )
        clean_nodes.append(clean_node)

    logger.info(f"Pushing {len(clean_nodes)} sanitized nodes to Qdrant")
    VectorStoreIndex(
        clean_nodes,
        storage_context=storage_context,
        embed_model=embedding_model
    )
    logger.info("Ingestion completed successfully")


if __name__ == "__main__":
    run_ingestion_pipeline()

