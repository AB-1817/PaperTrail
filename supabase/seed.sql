-- ============================================================
-- seed.sql — reproducible test data for local development / CI
-- PaperTrail v0.3
-- ============================================================
-- NOTE: Auth users must be created via Supabase Auth API or
-- the local dashboard. This seed only inserts application data
-- that references pre-existing auth.users rows.
-- ============================================================

-- Insert a sample paper so search and workspace tests have data
insert into papers (id, doi, title, abstract, year, open_access, has_abstract)
values (
  '00000000-0000-0000-0000-000000000001',
  '10.48550/arxiv.1706.03762',
  'Attention Is All You Need',
  'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.',
  2017,
  true,
  true
) on conflict (doi) do nothing;

insert into paper_sources (paper_id, provider, provider_id, fetched_at)
values (
  '00000000-0000-0000-0000-000000000001',
  'arxiv',
  '1706.03762',
  now()
) on conflict (provider, provider_id) do nothing;

-- Insert a sample evaluation dataset so the Evaluation Lab has something to show
insert into evaluation_datasets (id, name, version, description, domain)
values (
  '00000000-0000-0000-0000-000000000010',
  'papertrail-retrieval-v1',
  '1.0',
  'Initial 20-query benchmark for retrieval evaluation',
  'ai_cs'
) on conflict (name, version) do nothing;
