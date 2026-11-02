from typing import Any
import re
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

# 1. Define Metadata Schema
class NCERTMetadata(BaseModel):
    chapter_name: str = Field(description="The main chapter name.")
    topic: str = Field(description="The primary topic being discussed.")
    subtopic: str = Field(description="The specific subtopic or concept.")
    image_referenced: bool = Field(description="True if an image like ![alt](path) is in the text.")

# 2. Custom Local LLM Extractor
class LocalOllamaExtractor(BaseExtractor):
    # Declare llm as a Pydantic field instead of using __init__
    llm: Any = Field(description="Local Ollama instance")

    async def aextract(self, nodes):
        for node in nodes:
            prompt = (
                f"Analyze this textbook section and extract the chapter name, topic, and subtopic.\n"
                f"Text: {node.text[:1000]}...\n\n"
                f"Return ONLY valid JSON matching this schema: "
                f"{{\"chapter_name\": \"...\", \"topic\": \"...\", \"subtopic\": \"...\", \"image_referenced\": true/false}}"
            )
            response = self.llm.complete(prompt)
            try:
                import json
                json_str = re.search(r'\{.*\}', response.text, re.DOTALL).group()
                metadata_dict = json.loads(json_str)
                node.metadata.update(metadata_dict)
            except Exception as e:
                print(f"Failed to parse LLM JSON: {e}")
        return nodes
def main():
    # 3. Read the cleaned markdown
    with open("ncert_chapter.md", "r", encoding="utf-8") as f:
        document = Document(text=f.read())

    # 4. Initialize Local Models
    llm = Ollama(model="qwen2.5", request_timeout=120.0)
    embed_model = OllamaEmbedding(model_name="nomic-embed-text") # Standard fast local embedding

    # 5. Initialize Qdrant Client (Hybrid Search Enabled)
    client = qdrant_client.QdrantClient(url="http://localhost:6333", timeout=60.0)
    vector_store = QdrantVectorStore(
        client=client, 
        collection_name="ncert_civics", 
        enable_hybrid=True, # Enables Sparse Vectors (BM25) natively
        batch_size=20
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # 6. Build the Pipeline
    pipeline = IngestionPipeline(
        transformations=[
            MarkdownNodeParser(),
            LocalOllamaExtractor(llm=llm),
            embed_model,
        ]
    )

    print("Chunking, extracting metadata, and generating embeddings...")
    nodes = pipeline.run(documents=[document])

    print(f"Successfully processed {len(nodes)} nodes. Pushing to Qdrant...")
    
    # ULTIMATE FIX: Strip the poisoned metadata dictionary down to pure, safe data
    clean_nodes = []
    for node in nodes:
        # Only copy over safe, primitive data types (strings, numbers, booleans)
        safe_metadata = {}
        for key, value in node.metadata.items():
            if isinstance(value, (str, int, float, bool)):
                safe_metadata[key] = value
        
        # Create a pure node with no hidden LlamaIndex baggage
        clean_node = TextNode(
            text=node.text,
            metadata=safe_metadata,
            embedding=node.embedding
        )
        clean_nodes.append(clean_node)
    
    # 7. Ingest into Qdrant using the clean nodes
    index = VectorStoreIndex(
        clean_nodes,
        storage_context=storage_context,
        embed_model=embed_model
    )
    print("Ingestion Complete! Database is ready for Hybrid Search.")

if __name__ == "__main__":
    main()