# PaperTrail

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15.0+-black.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Qdrant](https://img.shields.io/badge/Qdrant-1.12+-DC2626.svg?logo=qdrant&logoColor=white)](https://qdrant.tech)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org)

> **Production-grade academic discovery, verified literature synthesis, and citation intelligence.**  
> PaperTrail combines multi-provider scholarly ingestion, hybrid reciprocal-rank retrieval, two-layer citation verification, and interactive citation network exploration into a single cohesive platform.

---

## Table of Contents

- [Architectural Overview](#architectural-overview)
- [Key Engineering Pillars](#key-engineering-pillars)
  - [1. Multi-Provider Scholarly Ingestion & Resolution](#1-multi-provider-scholarly-ingestion--resolution)
  - [2. Hybrid Retrieval Engine (BM25 + Dense + RRF + Cross-Encoder)](#2-hybrid-retrieval-engine-bm25--dense--rrf--cross-encoder)
  - [3. Two-Layer Citation Verification Pipeline](#3-two-layer-citation-verification-pipeline)
  - [4. Transactional Outbox Pattern for Vector Indexing](#4-transactional-outbox-pattern-for-vector-indexing)
  - [5. Literature Review Studio & Matrix Builder](#5-literature-review-studio--matrix-builder)
  - [6. Citation Graph Explorer](#6-citation-graph-explorer)
  - [7. Evaluation Lab & Reproducible Benchmarks](#7-evaluation-lab--reproducible-benchmarks)
- [System Architecture Diagram](#system-architecture-diagram)
- [Repository Structure](#repository-structure)
- [API Surface](#api-surface)
- [Database & Security Model](#database--security-model)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Configuration](#environment-configuration)
  - [Infrastructure Startup](#infrastructure-startup)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [License](#license)

---

## Architectural Overview

Academic discovery systems suffer from two core failure modes:
1. **Retrieval Blindspots**: Pure lexical keyword search (BM25) fails when researchers use differing terminology for the same underlying concepts. Conversely, pure dense semantic retrieval (bi-encoders) drifts on exact entity names, author identities, theorem titles, and conference abbreviations.
2. **The Unverified Synthesis Problem**: Modern Large Language Model (LLM) interfaces for literature synthesis routinely hallucinate citations, attribute claims to papers that never made them, or blend real paper metadata with fabricated findings.

**PaperTrail** resolves both failure modes with an engineering-first architecture:
- A **hybrid retrieval pipeline** that fuses inverted-index BM25 lexical ranking with dense HNSW vector search (`bge-base-en-v1.5`) via **Reciprocal Rank Fusion (RRF)**, followed by optional cross-encoder reranking (`ms-marco-MiniLM-L-6-v2`).
- A **two-layer citation validation engine** consisting of a deterministic structural span validator (token overlap and Levenshtein similarity against source PDF chunks) and a semantic NLI entailment verifier (`cross-encoder/nli-deberta-v3-small`). No claim is shown as verified unless both layers pass.
- A **durable transactional outbox pattern** ensuring that writes to the canonical PostgreSQL relational store and the Qdrant vector index never desynchronize, even under network partitions or crashes.

---

## Key Engineering Pillars

### 1. Multi-Provider Scholarly Ingestion & Resolution

PaperTrail interfaces with four major academic upstream providers, backed by an unpaywall resolver:
- **OpenAlex**: Primary metadata source for citation counts, topics, concepts, and institutional affiliations.
- **arXiv**: Real-time preprint ingestion for computer science, physics, and mathematics.
- **Semantic Scholar**: High-quality citation intent classifications and TLDR summaries.
- **Crossref**: Publisher-authoritative DOI resolution and bibliographic metadata.
- **Unpaywall**: Automated detection of legal Open Access PDF endpoints.

**Deduplication & Identity Resolution**: Ingestion jobs normalize raw records into canonical `Paper` entities. Incoming papers are deduplicated hierarchically:
1. Exact DOI match (case-insensitive normalized URL/string).
2. arXiv ID match (version-stripped).
3. Exact normalized title hash combined with first author surname and publication year.

```
Incoming Record ---> [ DOI Normalizer ] ---> Match DB? ---> UPDATE (Merge metadata)
                           | (No match)
                     [ Title+Author Hash ] ---> Match DB? ---> UPDATE
                           | (No match)
                     [ Ingestion Pipeline ] ---> INSERT Paper + Outbox Entry
```

### 2. Hybrid Retrieval Engine (BM25 + Dense + RRF + Cross-Encoder)

Search queries execute through an orchestrated four-stage pipeline:

```
User Query
    │
    ├──> Query Preprocessor (Clean, Tokenize, Filter Extraction)
    │
    ├──┬───────────────────────────────────┬───────────────────────────────────┐
    │  ▼                                   ▼                                   ▼
    │  [BM25 Lexical Retrieval]           [Dense Vector Search]               [Exact Filters]
    │  PostgreSQL Full-Text               Qdrant HNSW Collection              Pre-filtered in
    │  tsvector + websearch_to_tsquery    768d bge-base-en-v1.5               Qdrant payload
    │  (Top-K = 60)                       (Top-K = 60)                        (Year, OA, Field)
    │  │                                   │                                   │
    │  └───────────────────┬───────────────┘                                   │
    │                      ▼                                                   │
    │         [Reciprocal Rank Fusion (RRF)] <─────────────────────────────────┘
    │         Score = Σ (1 / (k + rank_i))  [k=60]
    │                      │
    │                      ▼
    │         [Cross-Encoder Reranker] (Optional / High-Precision Mode)
    │         ms-marco-MiniLM-L-6-v2
    │                      │
    │                      ▼
    │         [Result Explainer & Highlighting]
    │         Match breakdown: Lexical terms matched, Semantic similarity score
    ▼
Ranked Output (Top-N with Explanation Metadata)
```

1. **Query Preprocessing**: Identifies quoted exact-match phrases, publication year filters, author constraints, and Open Access requirements.
2. **Lexical Retrieval**: Uses PostgreSQL full-text search (`tsvector` with `english` dictionary configuration, ranked via `ts_rank_cd`).
3. **Dense Retrieval**: Embeds query via FastEmbed `BAAI/bge-base-en-v1.5` (768 dimensions) and queries Qdrant with cosine similarity. Metadata filters (year ranges, open access status) are pushed **directly into Qdrant index payload filters** prior to distance calculations to avoid post-filtering recall loss.
4. **Reciprocal Rank Fusion (RRF)**: Combines ranked lists without requiring score normalization:
   $$RRF(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
   where $k = 60$ prevents top-ranked outliers from dominating the fused list.
5. **Cross-Encoder Reranking**: The top candidates from RRF are scored using a cross-encoder model for deep token-level query-document interaction.

### 3. Two-Layer Citation Verification Pipeline

Every generated summary, literature review cell, and RAG answer passes through our citation verification engine before presentation:

```
LLM Generated Claim + Cited Passage
                 │
                 ▼
    ┌─────────────────────────────┐
    │  Layer 1: Structural Match   │
    │  • Exact character span     │
    │  • Word-level n-gram overlap│
    │  • Jaccard / Levenshtein    │
    └──────────────┬──────────────┘
                   │
         [Score >= 0.85?]
          ├── YES ──> [Passes Layer 1]
          └── NO  ──> FAIL (FLAGGED_UNVERIFIED_SPAN)
                   │
                   ▼
    ┌─────────────────────────────┐
    │  Layer 2: Semantic NLI Gate │
    │  • DeBERTa-v3 NLI Model     │
    │  • Premise: Document Chunk  │
    │  • Hypothesis: Claim        │
    └──────────────┬──────────────┘
                   │
         [Entailment >= 0.70?]
          ├── YES ──> STATUS: VERIFIED (Grounding verified)
          ├── NEUTRAL -> STATUS: PARTIAL (Incomplete evidence)
          └── CONTRADICTION -> STATUS: REFUTED (Flagged hallucination)
```

- **Layer 1 (Structural)**: Asserts that the claimed source quote exists verbatim or near-verbatim in the indexed PDF document chunk (`pypdf` / `GROBID` parsed sections).
- **Layer 2 (Semantic NLI)**: Checks natural language inference entailment. If an LLM cites a valid chunk but makes an unsupported deductive leap, Layer 2 flags the claim as ungrounded.

### 4. Transactional Outbox Pattern for Vector Indexing

To prevent dual-write inconsistencies between PostgreSQL and Qdrant, PaperTrail uses an asynchronous **Transactional Outbox**:
1. When a paper is ingested or updated, an `indexing_queue` record is committed in the **same database transaction** as the paper entity.
2. An asynchronous worker polls the outbox table using `SELECT ... FOR UPDATE SKIP LOCKED` to allow horizontal worker scaling without row collisions.
3. The worker generates dense embeddings in micro-batches and upserts them to Qdrant.
4. On success, the outbox record is marked `COMPLETED`. On failure, it records the error and executes an exponential backoff retry.

This eliminates ghost records, lost updates, and zombie vector points.

### 5. Literature Review Studio & Matrix Builder

- **Comparative Synthesis**: Groups papers by research questions and builds structured comparison matrices (Problem Statement, Methodology, Datasets, Metrics, Findings, Limitations).
- **Cell-Level Provenance**: Every cell in the comparison matrix links directly to the extracted paper section and source sentence.
- **Export Formats**: One-click export to Markdown tables, CSV, and formatted BibTeX citation files.

### 6. Citation Graph Explorer

- **Graph Topology**: Traverses inbound citations, outbound references, and co-citation linkages up to 3 degrees of separation.
- **Node Metrics**: Computes in-degree influence, year distribution, and cluster hubs.
- **Interactive UI**: Force-directed layout visualizing foundational vs. derivative papers.

### 7. Evaluation Lab & Reproducible Benchmarks

PaperTrail includes an integrated evaluation harness inspired by TREC and BEIR:
- **Metrics Tracked**:
  - **nDCG@10** (Normalized Discounted Cumulative Gain)
  - **MRR** (Mean Reciprocal Rank)
  - **Precision@K** and **Recall@K** ($K \in \{5, 10, 20\}$)
  - **MAP** (Mean Average Precision)
  - **Latency Distribution** (p50, p95, p99 in milliseconds)
- **A/B Strategy Testing**: Allows side-by-side benchmarking of BM25-only, Dense-only, RRF Hybrid, and RRF + Cross-Encoder pipelines against fixed evaluation query sets.

---

## System Architecture Diagram

```
                              ┌────────────────────────────────────────┐
                              │            Web Client (Next.js 15)      │
                              │  Tailwind CSS • TypeScript • Lucide    │
                              └───────────────────┬────────────────────┘
                                                  │ HTTP / JSON
                                                  ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                FastAPI Modular Monolith (Python 3.12)                   │
│                                                                                        │
│  [ Auth / JWKS ]        [ Search Router ]      [ RAG & Reviews ]    [ Graph Router ]   │
│         │                      │                      │                     │          │
│  [ Workspace Router ]   [ Ingestion Router ]   [ Documents Router ] [ Eval Router ]    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  Application Services:                                                                 │
│  • HybridFusion (RRF)    • ClaimExtractor       • OutboxWorker       • SSRF Guard      │
│  • DenseRetriever        • StructuralValidator  • GrobidParser       • Deduplicator    │
│  • BM25Retriever         • SemanticNLIValidator • BatchEmbedder      • MatrixBuilder   │
├────────────────────────────────┬───────────────────────────────┬───────────────────────┤
│                                │                               │                       │
│                                ▼                               ▼                       ▼
│                     ┌─────────────────────┐         ┌─────────────────────┐ ┌─────────┐
│                     │  Supabase Postgres  │         │   Qdrant Vector DB  │ │  Redis  │
│                     │  • Relational Data  │         │   • Dense Embeddings│ │  • Job  │
│                     │  • Row-Level Sec    │         │   • Payload Filters │ │    Queue│
│                     │  • Outbox Queue     │         │   • HNSW Index      │ └─────────┘
│                     └─────────────────────┘         └─────────────────────┘           │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
PaperTrail/
├── backend/
│   ├── app/
│   │   ├── auth/              # Supabase JWT verification & JWKS caching
│   │   ├── core/              # Config (pydantic-settings), DB sessions, logging, errors
│   │   ├── documents/         # PDF fetcher, SSRF guards, PyPDF/GROBID parsers, chunking
│   │   ├── embeddings/        # FastEmbed model wrapper, batching, registry
│   │   ├── evaluation/        # Metrics engine (nDCG, MRR), benchmarks, runner
│   │   ├── graph/             # Citation graph traversal & co-citation edge resolver
│   │   ├── ingestion/         # Upstream normalizers, deduplication, job tracker
│   │   ├── outbox/            # Indexing queue poller & Qdrant sync worker
│   │   ├── papers/            # Paper domain repository, schemas, service
│   │   ├── providers/         # OpenAlex, arXiv, Semantic Scholar, Crossref, Unpaywall
│   │   ├── rag/               # Context builder, ClaimExtractor, Two-Layer Citation Validator
│   │   ├── recommendations/   # Content, citation, and personalized paper rankers
│   │   ├── reviews/           # Literature Review Studio, matrix builder, BibTeX exporter
│   │   ├── search/            # BM25 lexical, Dense, RRF fusion, Reranker, Explainer
│   │   ├── storage/           # S3 / Supabase Storage integration for PDF persistence
│   │   ├── workspace/         # Collections, saved papers, reading notes, progress
│   │   └── main.py            # FastAPI entry point & API route registration (59 endpoints)
│   ├── tests/
│   │   └── unit/              # Unit test suites (search, evaluation, rag, core)
│   └── requirements.txt       # Pinned production Python dependencies
│
├── frontend/
│   ├── app/
│   │   ├── (app)/
│   │   │   ├── evaluation/    # Evaluation Lab UI & Benchmark Runner
│   │   │   ├── recommendations/# Discovery feed & recommendation sliders
│   │   │   ├── reviews/       # Literature Review Studio & Matrix view
│   │   │   └── workspace/     # Collections, notes, reading progress tracker
│   │   ├── (auth)/            # Login & Register views
│   │   ├── graph/             # Interactive Citation Graph Explorer
│   │   ├── papers/[id]/       # Paper details, full-text viewer, citations
│   │   ├── search/            # Advanced hybrid search interface with facets
│   │   ├── layout.tsx         # Root layout with navigation & theme providers
│   │   └── page.tsx           # Landing page with live search & feature demos
│   ├── components/            # Reusable React components (Search, PaperCard, Nav)
│   ├── lib/                   # API client, Supabase browser & server clients
│   └── tailwind.config.ts     # Tailwind CSS design system configuration
│
├── supabase/
│   └── migrations/            # Production migrations, schemas, and RLS policies
├── docs/                      # Technical specifications, schema diagrams, RFCs
├── docker-compose.yml         # Container definitions for Qdrant, Redis, Postgres
└── README.md
```

---

## API Surface

PaperTrail exposes **59 production endpoints** versioned under `/api/v1`:

| Domain | Route Prefix | Key Endpoints | Description |
|---|---|---|---|
| **Search** | `/api/v1/search` | `GET /`, `POST /rerank`, `GET /explain` | Hybrid BM25+Dense retrieval with RRF and cross-encoder |
| **Papers** | `/api/v1/papers` | `GET /`, `GET /{id}`, `GET /{id}/citations`, `GET /{id}/references` | Canonical paper CRUD, citation feeds, and metadata |
| **Ingestion** | `/api/v1/ingestion` | `POST /jobs`, `GET /jobs/{id}`, `POST /resolve` | Trigger async ingestion from arXiv/OpenAlex/SemanticScholar |
| **Documents** | `/api/v1/documents` | `POST /upload`, `POST /parse`, `GET /{id}/chunks` | PDF parsing, section extraction, and chunk retrieval |
| **RAG** | `/api/v1/rag` | `POST /synthesize`, `POST /validate-citation`, `POST /ask` | Evidence-grounded synthesis with 2-layer citation validation |
| **Reviews** | `/api/v1/reviews` | `POST /projects`, `GET /projects/{id}/matrix`, `POST /export` | Literature Review Studio, matrix builder, Markdown/BibTeX export |
| **Graph** | `/api/v1/graph` | `GET /subgraph`, `GET /co-citations`, `GET /paths` | Network traversal, degree metrics, and citation lineage |
| **Workspace** | `/api/v1/workspace`| `GET /collections`, `POST /saved-papers`, `POST /notes` | User collections, notes, reading progress (RLS protected) |
| **Recommendations**| `/api/v1/recommendations` | `GET /feed`, `POST /similar` | Hybrid personalized recommendations based on library activity |
| **Evaluation** | `/api/v1/eval` | `GET /benchmarks`, `POST /run`, `GET /runs/{id}` | Automated IR benchmarking (NDCG@10, MRR, Recall@k) |
| **Auth** | `/api/v1/auth` | `GET /me`, `POST /refresh` | Supabase JWKS token validation and user profile management |
| **System** | `/health`, `/metrics` | `GET /health`, `GET /health/ready` | Liveness, readiness, and subsystem connectivity probes |

Full interactive OpenAPI/Swagger documentation is available at `http://localhost:8000/api/docs`.

---

## Database & Security Model

1. **Row Level Security (RLS)**:
   Every table storing user data (`collections`, `saved_papers`, `notes`, `reading_progress`, `review_projects`) has PostgreSQL RLS enabled. Policies strictly enforce `auth.uid() = user_id`.
2. **Dual-Layer Ownership Enforcement**:
   In addition to database-level RLS, FastAPI route dependencies enforce tenant separation in application code, preventing IDOR (Insecure Direct Object Reference) vulnerabilities even in edge or service-role calls.
3. **SSRF Guard**:
   The PDF fetching pipeline enforces private IP blacklisting (blocking `127.0.0.1`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, and cloud metadata endpoints `169.254.169.254`) with strict scheme validation (`https://` required).

---

## Getting Started

### Prerequisites
- **Docker & Docker Compose** (for Qdrant & Redis)
- **Node.js 20+** and **npm**
- **Python 3.12**
- **Supabase CLI** (optional for local PostgreSQL)

### Environment Configuration

Create your `.env` file from the provided template:

```bash
cp .env.example .env
```

Key environment variables:

```ini
# Application Core
ENVIRONMENT=development
LOG_LEVEL=info
SECRET_KEY=generate-a-secure-random-secret-key-for-production

# PostgreSQL / Supabase
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:54322/postgres
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# Vector Database (Qdrant)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=optional-qdrant-key
QDRANT_COLLECTION=papers_dense_v1

# Redis Cache & Queues
REDIS_URL=redis://localhost:6379/0

# LLM Providers for RAG
OPENAI_API_KEY=your-openai-api-key # or Anthropic / local Ollama endpoint
```

### Infrastructure Startup

Start Qdrant and Redis using Docker Compose:

```bash
docker compose up -d qdrant redis
```

Verify services:
- Qdrant Dashboard: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)
- Redis: `redis-cli ping` (returns `PONG`)

### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI backend in development mode
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend starts at `http://127.0.0.1:8000`. Test the health probe:
```bash
curl http://127.0.0.1:8000/health
# {"status":"ok","database":"connected","qdrant":"connected"}
```

### Frontend Setup

```bash
cd frontend

# Install dependencies (respecting Next.js 15 peer dependencies)
npm install --legacy-peer-deps

# Start Next.js development server
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) to access PaperTrail.

---

## Testing & Quality Assurance

PaperTrail maintains unit and integration test coverage across search algorithms, RAG validators, metric computations, and core utilities.

Run the test suite:

```bash
# From workspace root or backend directory:
pytest backend/tests/unit -v
```

Expected output:
```
backend/tests/unit/core/test_errors.py .                    [  4%]
backend/tests/unit/evaluation/test_metrics.py ....         [ 20%]
backend/tests/unit/rag/test_claim_extractor.py ...         [ 33%]
backend/tests/unit/rag/test_validators.py .....            [ 54%]
backend/tests/unit/search/test_bm25.py .....               [ 75%]
backend/tests/unit/search/test_hybrid_fusion.py ......     [100%]

============================== 24 passed in 0.40s ==============================
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
