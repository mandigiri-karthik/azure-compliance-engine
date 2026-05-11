# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state

This repo is in **initial scaffolding**. Code does not yet exist — `requirements.txt` and `README.md` are empty, and `project.pdf` is the source-of-truth planning document. The current branch `feature/phase1-blob-upload` indicates Phase 1 work is starting (see Phased plan below).

When implementing, follow the folder layout in `project.pdf` §3 — do not invent a different structure.

> Note: `.gitignore` currently contains literal heredoc syntax (`cat > .gitignore << EOF ... EOF`) instead of the intended rules. Fix this before relying on it — the file does not actually ignore `.env`, `__pycache__/`, `*.pem`, etc. as written.

## What this project is

A multi-modal compliance ingestion engine: ingests YouTube videos via `yt-dlp` → streams to Azure Blob → indexes with Azure Video Indexer → embeds transcripts → stores in Azure AI Search → queries via a LangGraph pipeline with a Compliance Auditor agent → exposed through FastAPI and a `main.py` CLI.

## Architecture (the parts that span multiple files)

Four layers — read `project.pdf` §1.2 and §3 before structural changes.

1. **Entry points**: `main.py` (CLI) and `app/main.py` (FastAPI). Both invoke the same pipeline graph; don't duplicate logic between them.
2. **Pipeline (`pipeline/`)**: a LangGraph graph defined in `pipeline/graph.py`, with shared state in `pipeline/state.py` (TypedDict or Pydantic). Each step is a node in `pipeline/nodes/`:
   - `ingestion.py` — yt-dlp + Blob upload + Video Indexer submit/poll
   - `rag_workflow.py` — transcript/OCR extraction, chunking, embedding, upsert to AI Search
   - `retrieval.py` — vector + keyword hybrid search against AI Search
   - `compliance_auditor.py` — LLM agent that checks retrieved content against compliance rules
3. **Services (`services/`)**: thin Azure SDK wrappers (`blob_service`, `video_indexer`, `ai_search`, `openai_service`). Nodes call services; services do not call each other.
4. **External**: Azure OpenAI (GPT-4 + embeddings), LangSmith (graph tracing), Azure App Insights (logs/metrics).

The pipeline diagram → node mapping is fixed in `project.pdf` §6.3.

## Non-negotiable design constraints

These come from `project.pdf` §1.3 and §5 and shape almost every implementation choice:

- **No local file storage.** Videos must never touch disk. yt-dlp extracts the CDN stream URL (`extract_info(download=False)`), and bytes are uploaded to Blob in **4 MB chunks** via `iter_content`. Only 4 MB is in RAM at a time. Anything that writes a video to a temp file is wrong.
- **Blob is staging only.** Generate a SAS URL (default **2-hour** expiry; 3–4h for >30min videos), submit to Video Indexer, poll to completion, then **delete the blob**. A lifecycle policy deletes orphans after 24 h as a fallback.
- **Stateless across compute instances.** No process-local state that another instance couldn't reconstruct.
- **Secrets**: `.env` for local dev only. Production reads from **Azure Key Vault via Managed Identity** (Phase 4).
- **Observability is not optional**: structured logs to App Insights and `LANGCHAIN_TRACING_V2=true` for LangSmith are part of the spec, not nice-to-haves.

The Phase 1 ingestion flow (canonical pseudocode) is in `project.pdf` §6.1 — match it.

## Phased plan (work sequentially)

`project.pdf` §2 defines four phases; **do not start a phase until the previous one runs end-to-end**.

| Phase | Deliverable |
|---|---|
| 1 — Foundation & Ingestion | `python main.py --url <youtube_url>` streams to Blob, indexes via Video Indexer, deletes blob. |
| 2 — RAG Pipeline | Natural-language query returns ranked transcript segments with timestamps from AI Search. |
| 3 — Compliance & Orchestration | Full LangGraph pipeline runs from CLI with LangSmith traces and App Insights logs. |
| 4 — API, Polish & Deployment | FastAPI (`/ingest`, `/status/{job_id}`, `/query`), Dockerised, Key Vault secrets, deployed to App Service or Container Apps. |

The current branch (`feature/phase1-blob-upload`) is Phase 1 work. Default new branches to `feature/phaseN-<topic>` (see `project.pdf` §7).

## Commands (planned — not yet wired)

These don't run yet because the code isn't written. As Phase 1 lands, the canonical commands will be:

```bash
# Setup (once the venv/requirements exist)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Phase 1+: CLI ingestion
python main.py --url <youtube_url>

# Phase 3+: CLI with query
python main.py --url <youtube_url> --query "..."

# Phase 4+: FastAPI server
uvicorn app.main:app --reload
```

Tooling specified in the plan but not yet configured: `ruff` for linting, `pre-commit` hooks, `pytest` against `tests/test_ingestion.py | test_retrieval.py | test_api.py`. When you set these up, update this section with the actual invocations.
