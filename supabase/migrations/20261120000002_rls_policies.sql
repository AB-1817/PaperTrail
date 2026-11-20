-- ============================================================
-- Migration 002 — Row Level Security policies
-- PaperTrail v0.3
-- ============================================================

alter table profiles                 enable row level security;
alter table collections              enable row level security;
alter table collection_papers        enable row level security;
alter table saved_papers             enable row level security;
alter table notes                    enable row level security;
alter table tags                     enable row level security;
alter table paper_tags               enable row level security;
alter table reading_progress         enable row level security;
alter table literature_reviews       enable row level security;
alter table literature_review_papers enable row level security;
alter table synthesis_sections       enable row level security;
alter table evidence_citations       enable row level security;
alter table recommendation_events    enable row level security;
alter table documents                enable row level security;
alter table document_chunks          enable row level security;
alter table ingestion_jobs           enable row level security;
alter table qdrant_indexing_queue    enable row level security;

-- PROFILES
create policy "profiles_select_own" on profiles
  for select using (id = auth.uid());
create policy "profiles_insert_own" on profiles
  for insert with check (id = auth.uid());
create policy "profiles_update_own" on profiles
  for update using (id = auth.uid()) with check (id = auth.uid());

-- COLLECTIONS
create policy "collections_select_own" on collections
  for select using (user_id = auth.uid());
create policy "collections_insert_own" on collections
  for insert with check (user_id = auth.uid());
create policy "collections_update_own" on collections
  for update using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "collections_delete_own" on collections
  for delete using (user_id = auth.uid());

-- COLLECTION PAPERS
create policy "collection_papers_select_own" on collection_papers
  for select using (
    collection_id in (select id from collections where user_id = auth.uid())
  );
create policy "collection_papers_insert_own" on collection_papers
  for insert with check (
    collection_id in (select id from collections where user_id = auth.uid())
  );
create policy "collection_papers_delete_own" on collection_papers
  for delete using (
    collection_id in (select id from collections where user_id = auth.uid())
  );

-- SAVED PAPERS
create policy "saved_papers_select_own" on saved_papers
  for select using (user_id = auth.uid());
create policy "saved_papers_insert_own" on saved_papers
  for insert with check (user_id = auth.uid());
create policy "saved_papers_delete_own" on saved_papers
  for delete using (user_id = auth.uid());

-- NOTES
create policy "notes_select_own" on notes
  for select using (user_id = auth.uid());
create policy "notes_insert_own" on notes
  for insert with check (user_id = auth.uid());
create policy "notes_update_own" on notes
  for update using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "notes_delete_own" on notes
  for delete using (user_id = auth.uid());

-- TAGS
create policy "tags_select_own" on tags
  for select using (user_id = auth.uid());
create policy "tags_insert_own" on tags
  for insert with check (user_id = auth.uid());
create policy "tags_update_own" on tags
  for update using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "tags_delete_own" on tags
  for delete using (user_id = auth.uid());

-- PAPER TAGS
create policy "paper_tags_select_own" on paper_tags
  for select using (user_id = auth.uid());
create policy "paper_tags_insert_own" on paper_tags
  for insert with check (user_id = auth.uid());
create policy "paper_tags_delete_own" on paper_tags
  for delete using (user_id = auth.uid());

-- READING PROGRESS
create policy "reading_progress_select_own" on reading_progress
  for select using (user_id = auth.uid());
create policy "reading_progress_insert_own" on reading_progress
  for insert with check (user_id = auth.uid());
create policy "reading_progress_update_own" on reading_progress
  for update using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "reading_progress_delete_own" on reading_progress
  for delete using (user_id = auth.uid());

-- LITERATURE REVIEWS
create policy "literature_reviews_select_own" on literature_reviews
  for select using (user_id = auth.uid());
create policy "literature_reviews_insert_own" on literature_reviews
  for insert with check (user_id = auth.uid());
create policy "literature_reviews_update_own" on literature_reviews
  for update using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "literature_reviews_delete_own" on literature_reviews
  for delete using (user_id = auth.uid());

-- LITERATURE REVIEW PAPERS
create policy "review_papers_select_own" on literature_review_papers
  for select using (
    review_id in (select id from literature_reviews where user_id = auth.uid())
  );
create policy "review_papers_insert_own" on literature_review_papers
  for insert with check (
    review_id in (select id from literature_reviews where user_id = auth.uid())
  );
create policy "review_papers_delete_own" on literature_review_papers
  for delete using (
    review_id in (select id from literature_reviews where user_id = auth.uid())
  );

-- SYNTHESIS SECTIONS
create policy "synthesis_sections_select_own" on synthesis_sections
  for select using (
    review_id in (select id from literature_reviews where user_id = auth.uid())
  );
create policy "synthesis_sections_insert_own" on synthesis_sections
  for insert with check (
    review_id in (select id from literature_reviews where user_id = auth.uid())
  );
create policy "synthesis_sections_update_own" on synthesis_sections
  for update using (
    review_id in (select id from literature_reviews where user_id = auth.uid())
  ) with check (
    review_id in (select id from literature_reviews where user_id = auth.uid())
  );
create policy "synthesis_sections_delete_own" on synthesis_sections
  for delete using (
    review_id in (select id from literature_reviews where user_id = auth.uid())
  );

-- EVIDENCE CITATIONS
create policy "evidence_citations_select_own" on evidence_citations
  for select using (
    section_id in (
      select s.id from synthesis_sections s
      join literature_reviews r on r.id = s.review_id
      where r.user_id = auth.uid()
    )
  );
create policy "evidence_citations_insert_own" on evidence_citations
  for insert with check (
    section_id in (
      select s.id from synthesis_sections s
      join literature_reviews r on r.id = s.review_id
      where r.user_id = auth.uid()
    )
  );

-- RECOMMENDATION EVENTS
create policy "recommendation_events_select_own" on recommendation_events
  for select using (user_id = auth.uid());
create policy "recommendation_events_insert_own" on recommendation_events
  for insert with check (user_id = auth.uid());

-- DOCUMENTS / CHUNKS — authenticated users can read; service_role writes
create policy "documents_select_authenticated" on documents
  for select using (auth.role() = 'authenticated');
create policy "document_chunks_select_authenticated" on document_chunks
  for select using (auth.role() = 'authenticated');

-- INGESTION JOBS — authenticated users can read
create policy "ingestion_jobs_select_authenticated" on ingestion_jobs
  for select using (auth.role() = 'authenticated');

-- qdrant_indexing_queue: no policies — service_role only
