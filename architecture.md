# Architecture & Production Design: Atlas Ingestion Core

## Executive Summary
This document outlines the system architecture for the Atlas Ingestion Core, a highly scalable, fault-tolerant data pipeline designed to acquire, normalize, and enrich multi-dimensional datasets for the AI and venture ecosystem. The system is built on an asynchronous microservices architecture, ensuring high fidelity and low-latency processing across hundreds of thousands of records.

## 1. Scale Strategy: Acquiring 500,000+ Records
To achieve massive scale without manual intervention, the scraping infrastructure is decoupled from the data extraction and processing logic.

- **Asynchronous Message Queues:** The system utilizes a distributed task queue (e.g., Celery with RabbitMQ or AWS SQS) to manage crawling tasks. URLs are pushed to the queue and consumed by horizontally scaling worker nodes.
- **Dual-Engine Scraping:**
  - *Standard Nodes:* Use Python's `asyncio` and `aiohttp` for lightweight, rapid extraction of unprotected endpoints.
  - *Evasion Nodes:* High-value targets protected by Cloudflare or Datadome are routed to specialized worker pools running headless Playwright browsers integrated with residential proxy networks (e.g., BrightData) and automated CAPTCHA-solving middlewares.
- **Horizontal Scaling:** By containerizing the worker nodes using Docker, the infrastructure can dynamically scale up resources via Kubernetes (HPA) during massive one-time bulk extraction runs and scale down during routine daily polling.

## 2. LLM Orchestration: Handling 413s & 429s
Structuring raw HTML into strict JSON schemas at scale requires robust handling of LLM context limitations and API rate limits.

- **Intelligent Semantic Chunking (Mitigating 413 Errors):**
Before routing to the LLM, raw text is processed through a token-aware middleware (using libraries like `tiktoken`). If a payload exceeds the model's context window, it is sliced into overlapping semantic chunks. The LLM processes these chunks sequentially, and a final map-reduce chain aggregates the extracted JSON entities, guaranteeing payloads never trigger a 413 Payload Too Large error.
- **Resilient Fallback Chain & Backoff (Mitigating 429 Errors):**
To avoid bottlenecks from a single provider, the system implements a multi-tier fallback router via a unified API layer. The primary extraction hits a fast, cost-effective model (e.g., Groq Llama 3). If a 429 Too Many Requests error occurs, the orchestrator triggers an exponential backoff with jitter. If the request fails after 3 retries, it automatically falls back to Gemini Flash, and subsequently to DeepSeek.

## 3. Freshness Tracking Across Distributed Nodes
To maintain extreme 24-hour freshness for News and Job postings without reprocessing the same data across multiple distributed crawler nodes, the architecture employs a centralized, high-speed caching layer.

- **Redis Bloom Filters & Hashing:**
When a worker node identifies a URL or article title, it generates a SHA-256 hash. Before downloading the payload, it checks this hash against a centralized Redis instance. To maintain optimal memory efficiency over millions of records, a Redis Bloom Filter is utilized.
- **Atomic Operations:**
If the hash is new, the worker atomically sets the key in Redis with a 24-hour Time-To-Live (TTL) and proceeds with extraction. If the hash exists, the worker immediately drops the task, ensuring strictly zero duplication across the distributed network.

## 4. Storage Strategy & Entity Mapping
A hybrid database approach is necessary to manage the raw influx of unstructured data while mapping complex, canonical relationships.

- **Data Lake / Raw Dump (Amazon S3):**
All raw HTML and unparsed JSON payloads are immediately dumped into scalable object storage. This ensures data is never lost during pipeline failures and allows for future re-processing without re-scraping the target.
- **Primary Document Store (MongoDB / PostgreSQL):**
The cleaned, structured JSON entities (Startups, Products, Papers, Jobs, News) are stored in a primary database.
- **Vector & Graph Relationships (Neo4j):**
To power the Deterministic Entity Resolution engine, organization names are embedded into dense vectors. These are compared using cosine similarity to canonicalize messy strings (e.g., "OpenAI, Inc." to "OpenAI"). The final, canonical entities and their relationships (e.g., Founder -> Startup -> Product) are persisted in a Graph Database like Neo4j, enabling the complex, multi-hop queries required for a premier Intelligence Graph.

