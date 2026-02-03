# DOJ Document Explorer (Epstein Files Edition)

A professional-grade investigation platform designed to handle millions of pages from massive document leaks.

## Quick Start (Docker)

1. **Place your data**:
   - Put PDFs/Images in `./data/files`
   - Put Zips in `./data/zips`

2. **Launch Services**:
   ```bash
   docker-compose up --build -d
   ```

3. **Run Ingestion**:
   ```bash
   docker-compose exec api python /app/../ingestion/main.py
   ```

4. **Access**:
   - Web UI: http://localhost:3000
   - API: http://localhost:8000

## Architecture

- **Frontend**: Next.js 15, Tailwind CSS, TypeScript. Dramatic aesthetic with 18+ safety gate and PII protection.
- **Backend**: FastAPI (Python). High-performance asynchronous API for metadata and search orchestration.
- **Search**: OpenSearch with KNN support for hybrid (BM25 + Semantic) search.
- **AI Engine**: spaCy (NER) for person/org/place extraction + sentence-transformers for semantic embeddings.

## Safety & Compliance

- **PII Automasking**: During ingestion, potential emails, phone numbers, and addresses are replaced with tags (e.g., `[EMAIL]`) in the indexed text.
- **18+ Gate**: Mandatory click-through disclaimer required before accessing any records.
- **Sensitive Content Banner**: Persistent warning banner throughout the application.
- **Page-Level Results**: Search returns specific pages with contextual snippets.

## Features

- **Country Hub**: Aggregates all documents mentioning a specific nation. Lists top co-mentioned people.
- **Person Hub**: Track mentions of specific individuals across millions of pages.
- **Hybrid Search**: Combine keyword matches with AI-powered semantic understanding.
