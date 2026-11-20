-- ============================================================
-- Migration 001 — Initial schema
-- PaperTrail v0.3
-- ============================================================

-- Extensions
create extension if not exists "uuid-ossp";
create extension if not exists "pg_trgm";

-- ============================================================
-- PROFILES
-- ============================================================
create table if not exists profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  bio          text,
  interests    text[] not null default '{}',
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

-- Auto-create profile on user signup
create or replace function handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into profiles (id) values (new.id)
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure handle_new_user();

-- ============================================================
-- GLOBALLY SHARED ACADEMIC DATA
-- ============================================================
create table if not exists papers (
  id             uuid primary key default uuid_generate_v4(),
  doi            text,
  title          text not null,
  abstract       text,
  year           smallint check (year > 1000 and year <= 2100),
  venue          text,
  volume         text,
  issue          text,
  pages          text,
  open_access    boolean not null default false,
  oa_url         text,
  has_abstract   boolean not null default false,
  has_references boolean not null default false,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  constraint papers_doi_unique unique (doi),
  constraint papers_doi_format check (doi is null or doi not like 'https://%')
);

create index if not exists papers_year_idx on papers (year);
create index if not exists papers_oa_idx on papers (open_access);
create index if not exists papers_fts_idx on papers using gin (
  to_tsvector('english', coalesce(title,'') || ' ' || coalesce(abstract,''))
);
create index if not exists papers_title_lower_idx on papers (lower(title) text_pattern_ops);

create table if not exists authors (
  id          uuid primary key default uuid_generate_v4(),
  name        text not null,
  family_name text,
  orcid       text,
  created_at  timestamptz not null default now()
);

create unique index if not exists authors_orcid_notnull
  on authors (orcid) where orcid is not null;
create index if not exists authors_name_trgm_idx
  on authors using gin (name gin_trgm_ops);

create table if not exists institutions (
  id      uuid primary key default uuid_generate_v4(),
  name    text not null,
  ror_id  text,
  country text,
  constraint institutions_name_unique unique (name),
  constraint institutions_ror_unique unique (ror_id)
);

create table if not exists paper_authors (
  paper_id  uuid not null references papers(id) on delete cascade,
  author_id uuid not null references authors(id) on delete restrict,
  position  smallint not null check (position >= 1),
  primary key (paper_id, author_id),
  constraint paper_authors_position_unique unique (paper_id, position)
);

create index if not exists paper_authors_author_idx on paper_authors (author_id);

create table if not exists paper_sources (
  id           uuid primary key default uuid_generate_v4(),
  paper_id     uuid not null references papers(id) on delete cascade,
  provider     text not null,
  provider_id  text not null,
  raw_metadata jsonb not null default '{}',
  fetched_at   timestamptz not null default now(),
  constraint paper_sources_provider_id_unique unique (provider, provider_id)
);

create index if not exists paper_sources_paper_idx on paper_sources (paper_id);
create index if not exists paper_sources_provider_idx on paper_sources (provider, provider_id);

create table if not exists paper_references (
  id              uuid primary key default uuid_generate_v4(),
  citing_paper_id uuid not null references papers(id) on delete cascade,
  cited_paper_id  uuid references papers(id) on delete set null,
  doi_fallback    text,
  source          text not null,
  constraint paper_references_has_target check (
    cited_paper_id is not null or doi_fallback is not null
  )
);

create index if not exists paper_refs_citing_idx on paper_references (citing_paper_id);
create index if not exists paper_refs_cited_idx on paper_references (cited_paper_id);
create index if not exists paper_refs_doi_idx
  on paper_references (doi_fallback) where doi_fallback is not null;

create table if not exists paper_topics (
  paper_id uuid not null references papers(id) on delete cascade,
  topic    text not null,
  source   text not null,
  score    real,
  primary key (paper_id, topic, source)
);

create index if not exists paper_topics_topic_idx on paper_topics (topic);

-- ============================================================
-- DOCUMENTS AND CHUNKS
-- ============================================================
create table if not exists documents (
  id            uuid primary key default uuid_generate_v4(),
  paper_id      uuid not null references papers(id) on delete cascade,
  source_url    text not null,
  access_type   text not null check (
    access_type in ('arxiv_oa','unpaywall_oa','user_upload')
  ),
  storage_path  text,
  file_checksum text,
  parse_status  text not null default 'pending' check (
    parse_status in ('pending','processing','complete','failed')
  ),
  parser_used   text,
  page_count    int check (page_count > 0),
  parsed_at     timestamptz,
  created_at    timestamptz not null default now(),
  constraint documents_checksum_unique unique (file_checksum)
);

create index if not exists documents_paper_idx on documents (paper_id);
create index if not exists documents_status_idx on documents (parse_status);

create table if not exists document_chunks (
  id          uuid primary key default uuid_generate_v4(),
  document_id uuid not null references documents(id) on delete cascade,
  paper_id    uuid not null references papers(id) on delete cascade,
  chunk_index int not null check (chunk_index >= 0),
  text        text not null,
  page_number int check (page_number >= 1),
  char_offset int check (char_offset >= 0),
  section     text,
  token_count int check (token_count > 0),
  qdrant_id   uuid,
  created_at  timestamptz not null default now(),
  constraint document_chunks_unique unique (document_id, chunk_index)
);

create unique index if not exists document_chunks_qdrant_id_idx
  on document_chunks (qdrant_id) where qdrant_id is not null;
create index if not exists document_chunks_paper_idx on document_chunks (paper_id);
create index if not exists document_chunks_doc_idx on document_chunks (document_id, chunk_index);

-- ============================================================
-- USER-OWNED WORKSPACE DATA
-- ============================================================
create table if not exists collections (
  id          uuid primary key default uuid_generate_v4(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  name        text not null check (length(trim(name)) > 0),
  description text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  constraint collections_user_name_unique unique (user_id, name)
);

create index if not exists collections_user_idx on collections (user_id);

create table if not exists collection_papers (
  collection_id uuid not null references collections(id) on delete cascade,
  paper_id      uuid not null references papers(id) on delete cascade,
  added_at      timestamptz not null default now(),
  primary key (collection_id, paper_id)
);

create index if not exists collection_papers_paper_idx on collection_papers (paper_id);

create table if not exists saved_papers (
  id       uuid primary key default uuid_generate_v4(),
  user_id  uuid not null references auth.users(id) on delete cascade,
  paper_id uuid not null references papers(id) on delete cascade,
  saved_at timestamptz not null default now(),
  constraint saved_papers_unique unique (user_id, paper_id)
);

create index if not exists saved_papers_user_idx on saved_papers (user_id);

create table if not exists notes (
  id         uuid primary key default uuid_generate_v4(),
  user_id    uuid not null references auth.users(id) on delete cascade,
  paper_id   uuid not null references papers(id) on delete cascade,
  content    text not null check (length(content) > 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists notes_user_paper_idx on notes (user_id, paper_id);

create table if not exists tags (
  id      uuid primary key default uuid_generate_v4(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name    text not null check (length(trim(name)) > 0),
  constraint tags_user_name_unique unique (user_id, name)
);

create index if not exists tags_user_idx on tags (user_id);

create table if not exists paper_tags (
  paper_id  uuid not null references papers(id) on delete cascade,
  tag_id    uuid not null references tags(id) on delete cascade,
  user_id   uuid not null references auth.users(id) on delete cascade,
  tagged_at timestamptz not null default now(),
  primary key (paper_id, tag_id, user_id)
);

create index if not exists paper_tags_user_paper_idx on paper_tags (user_id, paper_id);

create table if not exists reading_progress (
  id         uuid primary key default uuid_generate_v4(),
  user_id    uuid not null references auth.users(id) on delete cascade,
  paper_id   uuid not null references papers(id) on delete cascade,
  status     text not null check (status in ('to_read','reading','read','archived')),
  updated_at timestamptz not null default now(),
  constraint reading_progress_unique unique (user_id, paper_id)
);

create index if not exists reading_progress_user_status_idx on reading_progress (user_id, status);

-- ============================================================
-- LITERATURE REVIEWS
-- ============================================================
create table if not exists literature_reviews (
  id          uuid primary key default uuid_generate_v4(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  title       text not null check (length(trim(title)) > 0),
  description text,
  status      text not null default 'draft' check (
    status in ('draft','generating','complete','error')
  ),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create index if not exists lit_reviews_user_idx on literature_reviews (user_id, updated_at desc);

create table if not exists literature_review_papers (
  review_id uuid not null references literature_reviews(id) on delete cascade,
  paper_id  uuid not null references papers(id) on delete cascade,
  added_at  timestamptz not null default now(),
  primary key (review_id, paper_id)
);

create table if not exists synthesis_sections (
  id               uuid primary key default uuid_generate_v4(),
  review_id        uuid not null references literature_reviews(id) on delete cascade,
  section_type     text not null check (section_type in (
    'overview','themes','methodologies','findings',
    'similarities','contradictions','limitations','gaps','future_directions'
  )),
  content          text,
  generated_at     timestamptz,
  model_id         text,
  model_version    text,
  is_abstract_only boolean not null default false,
  constraint synthesis_sections_unique unique (review_id, section_type)
);

create index if not exists synthesis_sections_review_idx on synthesis_sections (review_id);

create table if not exists evidence_citations (
  id               uuid primary key default uuid_generate_v4(),
  section_id       uuid not null references synthesis_sections(id) on delete cascade,
  chunk_id         uuid references document_chunks(id) on delete set null,
  paper_id         uuid not null references papers(id) on delete cascade,
  passage          text not null,
  claim_text       text not null,
  page_number      int,
  section_ref      text,
  structural_valid boolean,
  semantic_valid   boolean,
  semantic_score   real,
  validation_note  text,
  validated_at     timestamptz
);

create index if not exists evidence_citations_section_idx on evidence_citations (section_id);
create index if not exists evidence_citations_paper_idx on evidence_citations (paper_id);
create index if not exists evidence_citations_chunk_idx
  on evidence_citations (chunk_id) where chunk_id is not null;

-- ============================================================
-- EVALUATION
-- ============================================================
create table if not exists evaluation_datasets (
  id          uuid primary key default uuid_generate_v4(),
  name        text not null,
  version     text not null,
  description text,
  domain      text not null default 'ai_cs',
  created_at  timestamptz not null default now(),
  constraint evaluation_datasets_unique unique (name, version)
);

create table if not exists relevance_judgments (
  id         uuid primary key default uuid_generate_v4(),
  dataset_id uuid not null references evaluation_datasets(id) on delete cascade,
  query      text not null,
  paper_id   uuid not null references papers(id) on delete cascade,
  relevance  smallint not null check (relevance in (0,1,2)),
  annotator  text not null,
  source     text not null,
  judged_at  timestamptz not null default now(),
  constraint relevance_judgments_unique unique (dataset_id, query, paper_id, annotator)
);

create index if not exists relevance_judgments_dataset_idx
  on relevance_judgments (dataset_id, query);

create table if not exists retrieval_experiments (
  id              uuid primary key default uuid_generate_v4(),
  name            text not null,
  strategy        text not null check (
    strategy in ('bm25_only','dense_only','hybrid_rrf','hybrid_rerank')
  ),
  config          jsonb not null,
  dataset_id      uuid references evaluation_datasets(id),
  embedding_model text not null,
  reranker_model  text,
  index_version   text,
  status          text not null default 'pending' check (
    status in ('pending','running','complete','failed')
  ),
  created_at      timestamptz not null default now(),
  completed_at    timestamptz
);

create table if not exists evaluation_results (
  id            uuid primary key default uuid_generate_v4(),
  experiment_id uuid not null references retrieval_experiments(id) on delete cascade,
  metric        text not null,
  value         numeric not null,
  k             smallint,
  computed_at   timestamptz not null default now(),
  constraint evaluation_results_unique unique (experiment_id, metric, k)
);

create index if not exists eval_results_experiment_idx on evaluation_results (experiment_id);

-- ============================================================
-- INGESTION JOBS
-- ============================================================
create table if not exists ingestion_jobs (
  id              uuid primary key default uuid_generate_v4(),
  provider        text not null,
  query_or_scope  text,
  status          text not null default 'pending' check (
    status in ('pending','running','partial_failure','completed','failed')
  ),
  papers_found    int not null default 0,
  papers_inserted int not null default 0,
  papers_updated  int not null default 0,
  errors          jsonb not null default '[]',
  started_at      timestamptz,
  completed_at    timestamptz,
  created_at      timestamptz not null default now()
);

create index if not exists ingestion_jobs_status_idx on ingestion_jobs (status, created_at desc);

-- ============================================================
-- RECOMMENDATION EVENTS
-- ============================================================
create table if not exists recommendation_events (
  id         uuid primary key default uuid_generate_v4(),
  user_id    uuid not null references auth.users(id) on delete cascade,
  paper_id   uuid not null references papers(id) on delete cascade,
  event_type text not null check (
    event_type in ('view','save','dismiss','click','not_relevant')
  ),
  source     text,
  created_at timestamptz not null default now()
);

create index if not exists rec_events_user_idx on recommendation_events (user_id, created_at desc);
create index if not exists rec_events_user_paper_idx on recommendation_events (user_id, paper_id);
