Step 1: Ensure Ollama is Running

Make sure Ollama is active on your machine and has the required models:

powershell
ollama list

(You should see qwen2.5 and nomic-embed-text. If Ollama is closed, open the Ollama app from your Start menu).

Step 2: Start Qdrant Vector Database

Start the existing Qdrant container:

powershell
docker start ncert_qdrant

If the container does not exist yet, start it with:

powershell
docker compose up -d qdrant

Verify it is running by visiting: http://localhost:6333/dashboard

Step 3: Run the Ingestion Pipeline (Only needed once)

If you are running on a fresh Qdrant instance:

powershell
python scripts/ingest.py

(This parses Chapter 1, extracts metadata, computes embeddings, and stores vectors in Qdrant).

Step 4: Start the FastAPI Backend Server

In your first terminal window, run:

powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
Verify the health check in your browser: http://localhost:8000/health

(It should show "status": "healthy" and "database_connected": true).
Modern Web Research Station (HTML/CSS/JS) is live immediately at:
👉 http://localhost:8000/
Step 5: (Optional) Start the Streamlit Interface

If you also want the Streamlit dashboard, open a second terminal window and run:

powershell
streamlit run ui/app.py

👉 http://localhost:8501/

Alternative: Run Everything with One Command (Docker Compose)

If you prefer everything containerized without running multiple terminal windows:

powershell
docker compose up --build
Web Research Station & API: http://localhost:8000/
Streamlit Dashboard: http://localhost:8501/
Qdrant Vector DB Dashboard: http://localhost:6333/dashboard