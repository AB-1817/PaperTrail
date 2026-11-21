import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { SearchBar } from "@/components/search/SearchBar";
import { searchPapers, Paper } from "@/lib/api/client";
import Link from "next/link";

interface SearchPageProps {
  searchParams: Promise<{ q?: string; page?: string; strategy?: string }>;
}

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const { q = "", page = "1", strategy = "hybrid_rrf" } = await searchParams;
  const pageNum = parseInt(page, 10) || 1;

  let papers: Paper[] = [];
  let total = 0;
  let errorMsg: string | null = null;

  if (q.trim()) {
    const res = await searchPapers(q, pageNum, strategy);
    if (res.error) {
      errorMsg = res.error.message;
    } else {
      papers = res.data || [];
      total = res.meta?.total || papers.length;
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <SiteHeader />

      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-10">
        <div className="mb-8">
          <SearchBar initialQuery={q} />
        </div>

        {q && (
          <div className="flex items-center justify-between border-b border-hairline pb-3 mb-6 text-xs text-ash">
            <div>
              Found <span className="font-semibold text-ink">{total}</span> results for &ldquo;{q}&rdquo;
            </div>
            <div className="flex items-center gap-2">
              <span className="text-mute">Strategy:</span>
              <span className="font-mono bg-canvas px-2 py-0.5 rounded-sm border border-hairline text-stone">{strategy}</span>
            </div>
          </div>
        )}

        {errorMsg && (
          <div className="p-4 mb-6 text-xs bg-surface border border-error/30 text-error rounded-lg">
            {errorMsg}
          </div>
        )}

        {papers.length > 0 ? (
          <div className="space-y-3">
            {papers.map((paper) => (
              <div
                key={paper.id}
                className="card-hover"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <Link
                      href={`/papers/${paper.id}`}
                      className="text-base font-medium text-ink hover:text-primary transition-colors"
                    >
                      {paper.title}
                    </Link>
                    <div className="text-xs text-ash mt-1 flex flex-wrap items-center gap-2">
                      <span>{paper.authors?.map((a) => a.name).join(", ") || "Unknown authors"}</span>
                      {paper.year && <span>· {paper.year}</span>}
                      {paper.venue && <span>· {paper.venue}</span>}
                    </div>
                  </div>
                  {paper.open_access && (
                    <span className="eyebrow text-[9px] px-2.5 py-1 rounded-full border border-sage-pale bg-canvas text-olive whitespace-nowrap">
                      Open Access
                    </span>
                  )}
                </div>

                {paper.abstract && (
                  <p className="text-xs text-ash mt-3 line-clamp-3 leading-relaxed">
                    {paper.abstract}
                  </p>
                )}

                {paper.explanation?.matched_terms && paper.explanation.matched_terms.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-hairline flex items-center gap-2 text-[11px] text-ash">
                    <span className="font-medium text-stone">Matched:</span>
                    <span>{paper.explanation.matched_terms.join(", ")}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : q ? (
          <div className="text-center py-20 bg-surface border border-hairline rounded-lg">
            <p className="text-sm text-stone">No papers found matching your query.</p>
            <p className="text-xs text-ash mt-1">Try broader terms or verify the spelling.</p>
          </div>
        ) : (
          <div className="text-center py-20 bg-surface border border-hairline rounded-lg">
            <p className="text-sm text-stone">Type a keyword, title, author, or concept above to begin searching.</p>
            <p className="text-xs text-ash mt-1">BM25 keyword search and dense semantic embeddings will rank results.</p>
          </div>
        )}
      </main>

      <SiteFooter />
    </div>
  );
}
