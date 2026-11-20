-- ============================================================
-- Migration 003 — Qdrant indexing outbox
-- PaperTrail v0.3
-- ============================================================

create table if not exists qdrant_indexing_queue (
  id           uuid primary key default uuid_generate_v4(),
  entity_type  text not null check (entity_type in ('paper','chunk')),
  entity_id    uuid not null,
  operation    text not null check (operation in ('upsert','delete')),
  status       text not null default 'pending' check (
    status in ('pending','processing','done','failed')
  ),
  attempts     int not null default 0,
  last_error   text,
  created_at   timestamptz not null default now(),
  processed_at timestamptz
);

-- Partial index: only pending/failed rows need to be polled
create index if not exists qdrant_queue_pending_idx
  on qdrant_indexing_queue (status, created_at)
  where status in ('pending','failed');
