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
    <div className="min-h-screen flex flex-col">
      <SiteHeader />

      {/* Hero */}
      <main className="flex-1">
        <section className="max-w-4xl mx-auto px-6 pt-20 pb-16 text-center">
          <h1 className="text-4xl sm:text-5xl font-semibold text-stone-900 leading-tight mb-4">
            Research intelligence,
            <br />
            <span className="text-indigo-600">grounded in evidence.</span>
          </h1>
          <p className="text-lg text-stone-500 max-w-2xl mx-auto mb-10">
            Discover academic research, understand citation relationships,
            organize your literature and synthesize findings — with every claim
            traceable to its source.
          </p>

          <SearchBar />

          {/* Example queries */}
          <div className="mt-6">
            <p className="text-xs text-stone-400 mb-3 uppercase tracking-wide">
              Try an example
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {EXAMPLE_QUERIES.map((q) => (
                <Link
                  key={q}
                  href={`/search?q=${encodeURIComponent(q)}`}
                  className="text-xs px-3 py-1.5 rounded-full border border-stone-200 text-stone-600 hover:border-indigo-300 hover:text-indigo-700 hover:bg-indigo-50 transition-colors"
                >
                  {q}
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* Capabilities */}
        <section className="border-t border-stone-200 bg-white">
          <div className="max-w-5xl mx-auto px-6 py-16">
            <h2 className="text-xl font-semibold text-stone-900 mb-10 text-center">
              Built for serious research workflows
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {CAPABILITIES.map((cap) => (
                <div
                  key={cap.title}
                  className="p-5 rounded-lg border border-stone-200 hover:border-indigo-200 hover:shadow-sm transition-all"
                >
                  <h3 className="text-sm font-semibold text-stone-900 mb-2">
                    {cap.title}
                  </h3>
                  <p className="text-sm text-stone-500 leading-relaxed">
                    {cap.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Data sources */}
        <section className="max-w-4xl mx-auto px-6 py-12 text-center">
          <p className="text-xs text-stone-400 uppercase tracking-wide mb-4">
            Real data from
          </p>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-stone-500">
            {["OpenAlex", "Semantic Scholar", "arXiv", "Crossref", "Unpaywall"].map(
              (src) => (
                <span key={src} className="font-medium">
                  {src}
                </span>
              )
            )}
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
