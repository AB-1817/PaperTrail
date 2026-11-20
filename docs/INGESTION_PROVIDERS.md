# Academic Ingestion Providers

| Provider | Access Method | Rate Limits [U] | Status |
| :--- | :--- | :--- | :--- |
| **OpenAlex** | REST API with polite pool `mailto=` | 10 req/s polite pool | Active |
| **arXiv** | Atom XML API & PDF direct | 3 req/s polite | Active |
| **Semantic Scholar** | Graph API with optional API key | 1 req/s (10 req/s keyed) | Active |
| **Crossref** | REST API with `mailto=` | 50 req/s polite pool | Active |
| **Unpaywall** | REST API with email param | 100k req/day | Active |
