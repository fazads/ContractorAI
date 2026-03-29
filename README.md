# Contract AI Assistant — local prototype

This project turns the case study and leadership presentation into a runnable local application.

## What it does

- uploads or pastes contracts
- parses PDF, DOCX, TXT, and images
- chunks the contract into semantic sections with metadata
- extracts normalized clause facts for term, renewal, pricing, payment, SLA, liability, governing law, termination, and data processing
- stores a shared contract state as JSON with citations and agent audit events
- supports natural-language Q&A over the analyzed contract
- flags risky, expiring, or non-compliant clauses using a configurable policy pack
- compares extracted clauses to an **illustrative local benchmark pack** inspired by Spellbook-style coverage and TermScout-style market summaries
- routes simpler inbound contracts through **playbook automation** inspired by Juro-style review workflows: auto-approve, business-review with fallback language, or legal review
- includes a Help page that maps the implementation back to the presentation and documents the public reference sources used for the benchmark/playbook inspiration

## Architecture

### Backend

- **FastAPI** API server
- **OrchestratorAgent** coordinates the workflow
- specialist agents for:
  - ingestion
  - clause extraction and normalization
  - risk and compliance
  - benchmarking
  - playbook automation
  - summarization
  - Q&A
- **LocalRetriever** uses TF-IDF by default and can switch to sentence-transformer embeddings if optional dependencies are installed
- in-memory contract store for local prototyping
- when built with Docker, the backend also serves the compiled React UI so the whole prototype runs as a single web app on one port

### Frontend

- **React + Vite** UI
- reactive policy controls
- benchmark table with clause-level fit scores and fallback positions
- playbook automation panel for simple inbound routing
- citation-driven navigation to source sections
- Q&A history, risk review, and trace panel
- Help page with the key ideas from the presentation and the public vendor-inspiration references

## One-click Docker run

### Prerequisite

Install Docker Desktop for macOS, then confirm Docker is running:

```bash
docker --version
docker compose version
```

### Start the app

From the project root:

```bash
docker compose up --build
```

Then open:

```text
http://localhost:8000
```

The API is available on the same host under `/api/*`.

### Optional environment variables

You can pass these through your shell before starting Docker:

```bash
export OPENAI_API_KEY="your_key_here"
export OPENAI_MODEL="gpt-4.1-mini"
export RETRIEVER_MODE="tfidf"
docker compose up --build
```

### Stop the app

```bash
docker compose down
```

## Local run without Docker

### 1) Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scriptsctivate
pip install -r requirements.txt
# Optional extras for OpenAI, embeddings, and OCR:
# pip install -r requirements-optional.txt
uvicorn app.main:app --reload --port 8000
```

### 2) Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite, usually `http://localhost:5173`.

## Optional configuration

Create `backend/.env` from `backend/.env.example` if you want:

- `OPENAI_API_KEY` and `OPENAI_MODEL` for optional OpenAI-backed summarization / retrieval Q&A
- `RETRIEVER_MODE=embeddings` to use sentence-transformer embeddings instead of TF-IDF

## Notes

- The prototype is intentionally **assistive**, not an autonomous legal approval system.
- The benchmark pack is **illustrative only**. It is designed to mimic the style of benchmark products using public descriptions and local thresholds, not proprietary vendor datasets.
- OCR support is direct for image uploads. Scanned PDFs usually need an added OCR step such as Docling, OCRmyPDF, or pdf-to-image + Tesseract.
- The local retriever is in-memory. A production version would swap this for a persistent vector database such as pgvector, Pinecone, Weaviate, or similar.
- Two sample contracts are bundled:
  - a mixed-risk review sample MSA
  - a simpler inbound vendor agreement that should auto-approve under the default playbook

## Suggested next upgrades

- persistent storage for contracts and embeddings
- stronger legal clause parser / document layout parser
- user auth and role-based review queues
- benchmark calibration with real internal precedent data or licensed market datasets
- playbook packs by contract type, region, and vendor tier
- evaluation suite for answer quality and risk precision/recall
