# Atlas Ingestion Core

A high-performance, fault-tolerant data ingestion pipeline designed for the GraphOne / FrontierAtlas Intelligence Graph.

## Architecture Highlights
- **Phase I & V (Scraping & Anti-Bot):** Built on an `asyncio` worker pool. Routes low-priority targets to lightning-fast `aiohttp` sessions, while routing Cloudflare-protected targets to `Playwright Async` Chromium instances with stealth headers.
- **Phase III (LLM Orchestration):** Uses `Instructor` to patch LLM clients, enforcing strict JSON schemas via `Pydantic` v2. Implements a multi-tier fallback chain (Groq Llama 3 -> Gemini Flash -> DeepSeek) to handle failures. Uses `tenacity` for exponential backoff on 429 Rate Limits, and `tiktoken` to preemptively chunk data to avoid 413 Payload Too Large errors.
- **Phase IV (Entity Resolution):** Designed to interface with `RapidFuzz` for lexical mapping and `ChromaDB` for semantic vector matching to canonicalize entities.

## Project Structure
```text
src/
├── models/
│   └── schemas.py             # Pydantic JSON schemas
├── scraper/
│   └── async_worker.py        # Asyncio / Playwright concurrency
├── llm/
│   └── orchestrator.py        # Multi-tier fallback & chunking
└── main.py                    # Pipeline entrypoint
```

## Setup Instructions
1. `pip install -r requirements.txt`
2. Configure `.env` with `GROQ_API_KEY`, `GEMINI_API_KEY`, and `DEEPSEEK_API_KEY`
3. Run `python -m src.main`

