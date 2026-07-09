# RAG Portfolio Assistant Backend

This backend powers the portfolio chatbot with Retrieval-Augmented Generation over Dimitrios Markoulis' GitHub project documentation.

## What it does

- Fetches selected GitHub project files from `project_sources.json`
- Chunks README/project documentation
- Creates OpenAI embeddings
- Stores a local vector index in `data/project_vector_index.json`
- Retrieves the most relevant project chunks for each visitor question
- Calls the OpenAI Responses API to generate grounded portfolio answers
- Returns both the answer and source metadata to the frontend chatbot

## Architecture

```text
GitHub Pages chatbot UI
        |
        v
FastAPI backend /api/chat
        |
        v
Vector retrieval over GitHub project docs
        |
        v
OpenAI model response
```

## Files

```text
rag-backend/
├── app.py                 # FastAPI app and API endpoints
├── github_loader.py       # GitHub file ingestion and chunking
├── retriever.py           # Embeddings, vector index, cosine retrieval
├── prompts.py             # Portfolio assistant system prompt
├── project_sources.json   # Repositories and files to index
├── requirements.txt       # Python dependencies
└── .env.example           # Required environment variables
```

## Local setup

```bash
cd rag-backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Set your `OPENAI_API_KEY` in `.env`.

## Run locally

```bash
uvicorn app:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/api/health
```

Build the vector index:

```bash
curl -X POST http://localhost:8000/api/reindex
```

Ask a question:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Which project best demonstrates machine learning deployment readiness?"}'
```

## Deployment notes

Deploy this backend separately from GitHub Pages, for example on Render, Railway, Fly.io, or another platform that supports Python web services.

Required environment variables:

```text
OPENAI_API_KEY=...
ALLOWED_ORIGINS=https://dimitriosmarkoulis.github.io
OPENAI_CHAT_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
INDEX_PATH=data/project_vector_index.json
```

After deployment:

1. Run `POST /api/reindex` once.
2. Set the frontend `RAG_BACKEND_URL` in `chatbot.js` to the deployed backend URL.
3. Test the chatbot from the live portfolio page.

## Security

Do not expose the OpenAI API key in frontend JavaScript. The browser calls only this backend. The backend reads `OPENAI_API_KEY` from environment variables.

## Future improvements

- Add scheduled reindexing from GitHub Actions or a backend cron job
- Add source citations in the chatbot UI
- Add project filtering by category/status
- Add CV ingestion
- Add README quality scoring
- Add conversation memory by session ID
