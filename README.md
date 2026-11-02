# NCERT Multimodal Knowledge Explorer & Visual RAG

A production-grade, 100% local, multimodal Retrieval-Augmented Generation (RAG) system and interactive research station for NCERT textbooks (text and diagrams).

Built with **FastAPI**, **Qdrant**, **LlamaIndex**, **Ollama**, **Streamlit**, and a **custom modern HTML/CSS/JS Research Station**.

---

## Why This Project Exists

Most textbook RAG tutorials build basic text-only chat bubbles using proprietary cloud APIs (like OpenAI or Anthropic). This project solves three real-world industrial challenges:

1. **100% Local & Privacy-Preserving**: Runs completely on your own machine. No external cloud API calls, no monthly subscription fees, and no student data leaves your hardware.
2. **True Multimodal Retrieval**: Extracts and correlates political cartoons, historical photographs, and linguistic maps embedded in the textbook alongside text passages.
3. **Dedicated Research Station UI (Not a Chatbot)**: Replaces generic conversational chat bubbles with a dual-pane academic workstation featuring instant concept discovery chips, structured knowledge synthesis, relevance meters, and a diagram lightbox inspector.

---

## Main Libraries & Their Roles

| Library / Tool | Role in Architecture | Why It Was Chosen |
| :--- | :--- | :--- |
| **FastAPI** | Backend Microservice Framework | Provides high-performance asynchronous REST endpoints (`/query`, `/health`, `/images/{path}`), automatic OpenAPI documentation (`/docs`), static asset mounting, and custom global exception handling. |
| **Qdrant** | Local Vector Search Engine | Production-ready vector database running in Docker or local file persistence. Provides native **hybrid search** combining dense vector similarity with sparse BM25 lexical keyword matching. |
| **LlamaIndex** | RAG Orchestration Framework | Handles markdown structural parsing (`MarkdownNodeParser`), custom metadata extraction, vector store abstraction (`QdrantVectorStore`), and asynchronous query engines (`aquery`). |
| **Ollama** | Local LLM & Embedding Runtime | Manages and serves local models locally on CPU or GPU without cloud dependencies: `qwen2.5` (for conceptual synthesis and metadata extraction) and `nomic-embed-text` (for 768-dimensional embeddings). |
| **Streamlit** | Interactive Python Dashboard | Provides an interactive visual research interface with sidebar controls, concept inquiry buttons, excerpt accordions, and native local image rendering. |
| **Vanilla HTML5 / CSS3 / JavaScript** | Embedded Web Station | A lightweight, zero-dependency alternative frontend served directly by FastAPI at `http://localhost:8000/`. Features a dark glassmorphism theme, responsiveness, and an interactive image lightbox modal. |
| **Ragas (v1.0)** | Automated RAG Evaluation | Benchmarks RAG pipeline performance using metrics: `Faithfulness`, `AnswerRelevancy`, and `ContextPrecision` against ground-truth references using local models. |
| **Pydantic (v2) & Pydantic-Settings** | Data Validation & Settings | Enforces strict schemas for requests, responses, and metadata, while managing environment variables via `.env` without hardcoded connection strings. |
| **Gunicorn + Uvicorn Workers** | Production Application Server | Manages multiple asynchronous worker processes inside the backend container to ensure non-blocking concurrent request handling. |
| **Docker & Docker Compose** | Multi-Container Orchestration | Networks Qdrant, FastAPI backend, and Streamlit UI across isolated container networks while connecting to the host machine's Ollama instance. |

---

## System Architecture

```mermaid
flowchart TD
    User["Student / Researcher"] -->|Queries| WebUI["Web Research Station (HTML/CSS/JS) :8000"]
    User -->|Queries| StreamlitUI["Streamlit Dashboard :8501"]
    
    WebUI -->|Async HTTP POST /query| Backend["FastAPI Backend (Gunicorn + Uvicorn) :8000"]
    StreamlitUI -->|Async HTTP POST /query| Backend
    
    subgraph Data Layer
        Backend -->|Dense Embeddings| OllamaEmbed["Ollama (nomic-embed-text) :11434"]
        Backend -->|Synthesis & Reasoning| OllamaLLM["Ollama (qwen2.5) :11434"]
        Backend -->|Hybrid Search (Dense + BM25)| VectorDB["Qdrant Vector Database :6333"]
        Backend -->|Dynamic Diagram Delivery| ImageServer["FastAPI Image Router (/images)"]
    end

    subgraph Offline Ingestion Pipeline
        TextbookMD["NCERT Markdown Document"] --> MarkdownParser["MarkdownNodeParser"]
        MarkdownParser --> OllamaExtractor["LocalOllamaExtractor"]
        OllamaExtractor --> NodeSanitizer["Node Sanitizer (Circular Ref Stripper)"]
        NodeSanitizer --> QdrantIndex["Qdrant Hybrid Vector Store"]
    end
```

---

## Solved Engineering Edge Cases

During prototyping and production refactoring, several critical bugs were resolved:

### 1. LlamaIndex Circular Reference Bug
- **Problem**: When chunking markdown with `MarkdownNodeParser`, LlamaIndex creates recursive node relationships (`parent_node`, `child_nodes`, `prev_node`, `next_node`). Pydantic's JSON serializer crashes with infinite recursion when pushing to Qdrant.
- **Solution**: The ingestion pipeline in `scripts/ingest.py` strips all non-primitive fields by reconstructing brand-new `TextNode` objects containing only primitive metadata types `(str, int, float, bool)`.

### 2. Pydantic Class Attributes in BaseExtractor
- **Problem**: Subclassing `BaseExtractor` while initializing `self.llm` inside `__init__` violates Pydantic v2 model validation.
- **Solution**: `LocalOllamaExtractor` declares `llm: Any = Field(description="Local Ollama instance")` as a class attribute.

### 3. Parentheses in Image Filenames
- **Problem**: Textbook diagrams are named with parentheses (e.g. `images (2).png`). Standard markdown image regex `!\[(.*?)\]\((.*?)\)` truncated filenames at the first closing parenthesis `(2`, returning `images (2` and causing HTTP 404 errors.
- **Solution**: Implemented strict extension-aware regex matching `r'!\[(.*?)\]\((.+?\.(?:png|jpg|jpeg|webp|svg|gif|bmp)|[^\s\)]+)\)'` and built a multi-stage image resolver in both FastAPI and Streamlit that automatically recovers truncated names and matches them to physical disk files.

### 4. Streamlit Request Loop & Timeout Protection
- **Problem**: Streamlit reruns scripts from top to bottom on every user interaction (such as opening an accordion), re-firing heavy 120-second LLM queries and causing `Read timed out` crashes on local hardware.
- **Solution**: Implemented `st.session_state` caching for query results, aligned HTTP timeouts to 300 seconds across all services, and separated user trigger actions from script re-renders.

### 5. Multi-Container Docker Network DNS
- **Problem**: Inside Docker Compose, containers communicate via internal DNS names (`http://api:8000`), but images in browser `<img>` tags must be loaded from the user's host machine (`http://localhost:8000`).
- **Solution**: Configured separate variables: `API_BASE_URL=http://api:8000` for backend-to-backend calls, and `IMAGE_BASE_URL=http://localhost:8000` for browser asset delivery. Added `COPY images/ ./images/` directly to `Dockerfile.ui` for instant zero-latency image rendering.

### 6. Ragas v1.0 Schema Alignment
- **Problem**: Ragas v1.0 deprecates string metric imports and nested ground-truth lists.
- **Solution**: Instantiated metric objects (`Faithfulness()`, `AnswerRelevancy()`, `ContextPrecision()`) and formatted ground-truth references as flattened strings under dataset keys `user_input`, `response`, `retrieved_contexts`, `reference`.

---

## Project Structure

```text
NCERT/
├── .env.example                # Template configuration file
├── .env                        # Local environment settings
├── requirements.txt            # Production dependencies
├── docker-compose.yml          # Container orchestration (Qdrant + API + UI)
├── Dockerfile                  # Unified Dockerfile for Hugging Face Spaces
├── Dockerfile.api              # Backend Dockerfile (Gunicorn + Uvicorn)
├── Dockerfile.ui               # Streamlit UI Dockerfile
├── app/
│   ├── main.py                 # FastAPI application & image file server
│   ├── api/
│   │   ├── dependencies.py     # Dependency injection providers
│   │   └── v1/
│   │       ├── router.py       # API v1 router
│   │       └── endpoints/
│   │           ├── health.py   # Health probe endpoint
│   │           └── query.py    # Async query & multimodal synthesis endpoint
│   ├── core/
│   │   ├── config.py           # Pydantic-Settings environment configuration
│   │   └── logging.py          # Structured logging configuration
│   ├── models/
│   │   └── schemas.py          # Pydantic data schemas (Request, Response, SourceItem)
│   └── services/
│       ├── qdrant_service.py   # Qdrant client manager (local & network modes)
│       └── rag_service.py      # LlamaIndex query engine & diagram resolver
├── frontend/                   # Modern Interactive Web Interface (HTML/CSS/JS)
│   ├── index.html              # Research Station template
│   ├── css/
│   │   └── style.css           # Modern dark responsive theme
│   └── js/
│       └── app.js              # Vanilla JS client & image lightbox
├── ui/
│   └── app.py                  # Streamlit visual dashboard
├── scripts/
│   ├── clean_textbook.py       # Preprocessing for raw NCERT markdown
│   ├── ingest.py               # Offline ingestion pipeline
│   └── evaluate.py             # Ragas v1.0 evaluation script
├── data/
│   ├── ncert_chapter.md        # Cleaned textbook chapter
│   └── raw_ncert.md            # Raw textbook chapter
└── images/                     # Textbook maps, diagrams, and photos
    ├── images (1).png
    ├── ...
    └── images (7).png
```

---

## Local Installation & Quickstart

### Prerequisites

1. **Python 3.11+**
2. **Ollama**: Download from [ollama.com](https://ollama.com) and pull models:
   ```bash
   ollama pull qwen2.5
   ollama pull nomic-embed-text
   ```
3. **Docker Desktop** (for containerized execution)

---

### Option 1: Run with Docker Compose (Recommended)

Start the full stack with one command:

```bash
docker compose up --build
```

Access the interfaces:
- **Interactive Web Research Station**: [http://localhost:8000/](http://localhost:8000/)
- **Streamlit Visual Dashboard**: [http://localhost:8501/](http://localhost:8501/)
- **Interactive API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Qdrant Vector Database Dashboard**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

To stop the containers:
```bash
docker compose down
```

---

### Option 2: Run Directly on Your Machine

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Qdrant**:
   ```bash
   docker run -d -p 6333:6333 -p 6334:6334 -v qdrant_data:/qdrant/storage qdrant/qdrant:latest
   ```

3. **Ingest Textbook Content**:
   ```bash
   python scripts/ingest.py
   ```

4. **Start the FastAPI Backend**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Open [http://localhost:8000/](http://localhost:8000/) in your browser.

5. **Start Streamlit Dashboard** (in another terminal):
   ```bash
   streamlit run ui/app.py
   ```
   Open [http://localhost:8501/](http://localhost:8501/) in your browser.

---

## Ingestion Pipeline Details

The ingestion script (`scripts/ingest.py`) processes the textbook:

1. **Document Loading**: Reads `data/ncert_chapter.md`.
2. **Markdown Parsing**: `MarkdownNodeParser` splits text along logical headings (`#`, `##`).
3. **Metadata Extraction**: `LocalOllamaExtractor` prompts `qwen2.5` to extract `chapter_name`, `topic`, and `subtopic`.
4. **Diagram Detection**: Regex extracts image references and maps them to local files in `images/`.
5. **Node Sanitization**: Strips circular references into primitive-only metadata.
6. **Vector Indexing**: Computes dense embeddings with `nomic-embed-text` and sparse BM25 indices, then pushes points to Qdrant collection `ncert_civics`.

Run manually:
```bash
python scripts/ingest.py
```

---

## Automated Evaluation (Ragas v1.0)

Benchmark system accuracy using local models:

```bash
python scripts/evaluate.py
```

Evaluated metrics:
- **Faithfulness**: Verifies that the answer is grounded purely in retrieved textbook context.
- **Answer Relevancy**: Measures how directly the response addresses the prompt.
- **Context Precision**: Measures the ratio of relevant text in the retrieved chunks.

Output format:
```text
                                user_input  faithfulness  answer_relevancy  context_precision
0   What is the ethnic composition of Belgium?          1.00              0.96               1.00
1  Why is power sharing desirable according...          1.00              0.94               1.00
```

---

## Deploying to Hugging Face Spaces

The repository is pre-configured for **Hugging Face Spaces** via the root `Dockerfile`.

### Step 1: Create Space
1. Go to [huggingface.co/new-space](https://huggingface.co/new-space).
2. Choose **Docker** SDK (Blank template).
3. Select hardware (Free CPU Basic or upgraded GPU).

### Step 2: Set Environment Variables
In Space Settings > **Variables and secrets**, add:
- `PORT`: `7860`
- `QDRANT_URL`: `local` *(uses embedded local file storage in `/workspace/data/qdrant_storage`)*
- `OLLAMA_BASE_URL`: Address of your remote Ollama server or tunnel (e.g., via `ngrok http 11434`).

### Step 3: Push Repository
```bash
git remote add space https://huggingface.co/spaces/<YOUR_USERNAME>/<SPACE_NAME>
git add .
git commit -m "Deploy NCERT Multimodal RAG"
git push space main
```

Your Space will build and serve the application on port `7860`.

---

## API Endpoints Reference

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the interactive Web Research Station (HTML/CSS/JS). |
| `GET` | `/health` | Returns health status of the application and Qdrant connection. |
| `POST` | `/query` | Submits a question and returns synthesized answer, source excerpts, and diagram URLs. |
| `GET` | `/images/{image_path}` | Dynamically resolves and streams textbook diagrams and maps. |
| `GET` | `/docs` | Interactive Swagger / OpenAPI documentation. |

### Sample Query Request

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the ethnic composition of Belgium?"}'
```

### Sample Query Response

```json
{
  "question": "What is the ethnic composition of Belgium?",
  "answer": "In Belgium, the ethnic composition is complex. 59% lives in the Flemish region speaking Dutch, 40% in the Wallonia region speaking French, and 1% speaks German. In the capital Brussels, 80% speak French and 20% speak Dutch.",
  "sources": [
    {
      "text": "## Belgium and Sri Lanka...",
      "metadata": {
        "chapter_name": "Power-sharing",
        "topic": "Belgium and Sri Lanka",
        "subtopic": "Ethnic composition",
        "image_referenced": true
      },
      "score": 0.892,
      "image_url": "http://localhost:8000/images/images%20%282%29.png",
      "image_caption": "map: Communities and regions of Belgium"
    }
  ],
  "images": [
    "http://localhost:8000/images/images%20%282%29.png"
  ]
}
```

---

## Troubleshooting & FAQ

- **Timeout Error (`Read timed out`)**:
  Local model generation on CPU can take between 30 and 90 seconds. Timeouts across FastAPI, Qdrant, and Streamlit are configured to 300s. If requests still time out, ensure your GPU is detected by Ollama.
- **Images Not Rendering**:
  Ensure image requests point to `http://localhost:8000/images/...` (or local files inside the UI container). FastAPI's `/images` router automatically resolves filenames containing parentheses.
- **Qdrant Connection Refused**:
  Verify the Qdrant container is active (`docker ps`). If offline, run `docker start ncert_qdrant` or `docker compose up -d qdrant`.
