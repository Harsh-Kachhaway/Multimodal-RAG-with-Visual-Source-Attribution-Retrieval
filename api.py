import qdrant_client
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

# 1. Initialize FastAPI App
app = FastAPI(title="NCERT Multimodal RAG API")

# 2. Mount the local images folder so the frontend can load them via URL
app.mount("/images", StaticFiles(directory="images"), name="images")

# 3. Setup LlamaIndex connections to your running local services
print("Connecting to local Ollama and Qdrant...")
llm = Ollama(model="qwen2.5", request_timeout=300.0)
embed_model = OllamaEmbedding(model_name="nomic-embed-text")

client = qdrant_client.QdrantClient(url="http://localhost:6333", timeout=60.0)
vector_store = QdrantVectorStore(
    client=client, 
    collection_name="ncert_civics", 
    enable_hybrid=True
)

# Load the existing index from Qdrant
index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store,
    embed_model=embed_model,
)

# Create the query engine (using Qwen2.5 to synthesize the final answer)
query_engine = index.as_query_engine(llm=llm, similarity_top_k=3)

# 4. Define API Schemas
class QueryRequest(BaseModel):
    question: str

# 5. Define the Query Endpoint
@app.post("/query")
async def query_rag(request: QueryRequest):
    # Send the question to LlamaIndex
    response = query_engine.query(request.question)
    
    # Extract the source nodes and their metadata to send to the frontend
    sources = []
    for node in response.source_nodes:
        sources.append({
            "text": node.node.text,
            "metadata": node.node.metadata,
            "score": node.score
        })
        
    return {
        "answer": str(response),
        "sources": sources
    }

print("API is ready! Run with: uvicorn api:app --reload")