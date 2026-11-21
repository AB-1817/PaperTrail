import Link from "next/link";
import { SearchBar } from "@/components/search/SearchBar";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";

const EXAMPLE_QUERIES = [
  "Methods for evaluating hallucinations in retrieval augmented generation",
  "Transformer attention mechanisms for long document understanding",
  "Contrastive learning for visual representation without labels",
  "Federated learning privacy guarantees differential privacy",
  "Graph neural networks molecular property prediction",
];

const CAPABILITIES = [
  {
    title: "Hybrid Search",
    description:
      "BM25 keyword retrieval combined with dense semantic search, fused and reranked for precision.",
  },
  {
    title: "Citation Graph",
    description:
      "Explore real citation relationships between papers. Discover what cites what and why.",
  },
  {
    title: "Literature Review Studio",
    description:
      "Generate structured syntheses across multiple papers with every claim linked to its source passage.",
  },
  {
    title: "Evidence-Grounded RAG",
    description:
      "Ask questions about research documents. Every answer cites the exact passage it came from.",
  },
  {
    title: "Smart Recommendations",
    description:
      "Content-based, citation-based and personalized recommendations with transparent explanations.",
  },
  {
    title: "Evaluation Lab",
    description:
      "Measure retrieval quality with Precision@K, nDCG and MRR on a human-judged benchmark.",
  },
];

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <SiteHeader />

      <main className="flex-1">
        {/* ── Hero ── */}
        <section className="max-w-4xl mx-auto px-6 pt-24 pb-20 text-center">
          <p className="eyebrow text-stone mb-6">Research Intelligence</p>
          <h1
            className="text-5xl sm:text-6xl font-light text-ink leading-[1.08] mb-6"
            style={{ fontFamily: "var(--font-fraunces), Fraunces, Georgia, serif" }}
          >
            Research intelligence,
            <br />
            <span className="italic">grounded in evidence.</span>
          </h1>
          <p className="text-base text-ash max-w-2xl mx-auto mb-12 leading-relaxed">
            Discover academic research, understand citation relationships,
            organize your literature and synthesize findings — with every claim
            traceable to its source.
          </p>

          <SearchBar />

          {/* Example queries as outline pills */}
          <div className="mt-8">
            <p className="eyebrow text-ash mb-4">Try an example</p>
            <div className="flex flex-wrap justify-center gap-2">
              {EXAMPLE_QUERIES.map((q) => (
                <Link
                  key={q}
                  href={`/search?q=${encodeURIComponent(q)}`}
                  className="text-xs px-4 py-2 rounded-full border border-hairline text-stone bg-canvas hover:border-stone hover:bg-surface transition-colors"
                >
                  {q}
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* ── Capabilities — white card band ── */}
        <section className="bg-surface border-t border-hairline">
          <div className="max-w-5xl mx-auto px-6 py-20">
            <p className="eyebrow text-ash text-center mb-3">Platform</p>
            <h2
              className="text-3xl font-light text-ink text-center mb-14"
              style={{ fontFamily: "var(--font-fraunces), Fraunces, Georgia, serif" }}
            >
              Built for serious research workflows
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {CAPABILITIES.map((cap) => (
                <div
                  key={cap.title}
                  className="card-hover"
                >
                  <h3 className="text-sm font-semibold text-ink mb-2">
                    {cap.title}
                  </h3>
                  <p className="text-sm text-ash leading-relaxed">
                    {cap.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Data sources band ── */}
        <section className="max-w-4xl mx-auto px-6 py-16 text-center">
          <p className="eyebrow text-ash mb-5">Real data from</p>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-stone font-medium">
            {["OpenAlex", "Semantic Scholar", "arXiv", "Crossref", "Unpaywall"].map(
              (src) => (
                <span key={src}>{src}</span>
              )
            )}
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
