# PaperTrail Implementation Audit & Progress Log (CHANGES.md)

## Production Fixes — 22 November 2026

- Made the outbox worker fail gracefully while Qdrant is unavailable; it retries every 15 seconds and logs a single warning until recovery instead of repeatedly raising connection-refused errors.

- Removed frontend seed/fallback paper records and all mock paper detail, PDF, reference, and recommendation fallbacks.
- Search now always combines database records with live OpenAlex/arXiv provider results and performs provider deduplication.
- Paper detail resolution now uses the requested DOI/arXiv/provider ID and resolves open-access PDF URLs through live provider metadata and Unpaywall.
- Added real Qdrant paper/chunk upsert and delete handling to the indexing outbox worker.
- Added OpenAI and Anthropic LLM providers and corrected the configured provider setting name.
- Citation semantic validation now uses the configured LLM as an NLI-style fail-closed verifier instead of token overlap.
- Fixed missing-auth responses to return `401` with `WWW-Authenticate: Bearer`.
- Fixed the initial migration order for the Qdrant outbox table.

## Phase 0 - Baseline Audit Findings

### 1. Ruff Lint Check (`ruff check app tests`)
- **Total Errors**: 207 errors found across `app/` and `tests/`.
- **Key Categories**:
  - `B008`: Do not perform function call `Depends` in argument defaults (FastAPI dependency convention).
  - `S608`: Possible SQL injection vector via string-based query construction.
  - `B904`: Missing `raise ... from err` or `raise ... from None` inside except clauses.
  - `F401`: Unused imports across multiple modules.
  - `I001`: Unsorted/unformatted import blocks.
  - `E501`: Line length exceedances (>100 chars).

### 2. Ruff Format Check (`ruff format --check app tests`)
- **Status**: 31 files would be reformatted, 87 files formatted.

### 3. Mypy Type Check (`mypy app`)
- **Status**: Found 30 errors in 14 files (checked 102 source files).
- **Key Failures**:
  - `app/rag/llm_provider.py`: `"Settings" has no attribute "llm_provider"` (AttributeError).
  - `app/workspace/router.py`: `Name "HTTPException" is not defined` (NameError).
  - `app/papers/service.py`: `Argument "id" to "PaperResponse" has incompatible type "str"; expected "UUID"`.
  - `app/workspace/repository.py` & `app/reviews/projects.py`: `Result[Any]` has no attribute `rowcount`.
  - `app/providers/`: Type parameter mismatches and `str | None` assignment errors.

### 4. Pytest Suite (`pytest tests -v`)
- **Status**: 32 passed, 1 failed.
- **Failing Test**:
  - `tests/security/test_auth_enforcement.py::test_me_without_token_returns_401`: FastAPI `HTTPBearer` returned `403 Forbidden` instead of `401 Unauthorized` with `WWW-Authenticate` header when credentials are missing.

---

## Phase 1 & 2 - Crash Bugs & Seamless Live Fetch Remediations

- **Seamless Live-Fetch & Persistence**:
  - Implemented automatic resolution in `papers/service.py` via `app/ingestion/live_fetch.py`: if a paper is not in the database, it live-fetches metadata from OpenAlex (by DOI) or arXiv (by arXiv ID), persists to Postgres, and returns instantly.
  - Search endpoint (`POST/GET /api/v1/search`) searches local Postgres DB first; if empty, it queries OpenAlex and arXiv live, persists the results for future requests, ranks them with the requested strategy, and returns real papers.
  - Removed all fabricated seed data and manual ingestion panels.
- **Frontend Crash Bugs Resolved**:
  - Fixed `SiteHeader.tsx` importing `@/lib/supabase/server` with `cookies` from `next/headers`, which broke all client-side pages (`/graph`, `/reviews`, `/recommendations`, `/evaluation`, `/workspace`). Converted `SiteHeader.tsx` to a robust client component.
  - Resolved `next/font` variable font axis failure (`Axes can only be defined for variable fonts`) in `app/layout.tsx` by using standard web fonts with Inter and Fraunces fallbacks.
  - Added `<Suspense>` boundaries around `useSearchParams()` in `app/graph/page.tsx` and `app/(auth)/login/page.tsx`.
  - Patched Next.js `recursive-delete.js` to handle OneDrive cloud reparse points gracefully on Windows (`EINVAL` readlink error).
  - All 12 Next.js routes now build with 0 errors (`next build` passes).
- **Backend Architecture & Routes**:
  - Reordered routes in `papers/router.py`: `GET ""` (list) and `GET "/{paper_id}/references"` registered before `GET "/{paper_id:path}"` catch-all.
  - Implemented `get_paper_by_doi` in `papers/repository.py`.
  - Added `llm_provider` setting with `PAPERTRAIL_LLM_PROVIDER` alias in `core/config.py`.
  - Converted FastAPI `startup`/`shutdown` handlers to modern `@asynccontextmanager` `lifespan(app)` in `main.py`.
  - Fixed Python 3.10 `datetime.UTC` compatibility in ingestion adapters.
  - All 35 pytest unit and security tests pass with 100% success rate.

