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
    <div className="min-h-screen flex flex-col bg-stone-50">
      <SiteHeader />

      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8">
        <div className="mb-8">
          <SearchBar initialQuery={q} />
        </div>

        {q && (
          <div className="flex items-center justify-between border-b border-stone-200 pb-3 mb-6 text-xs text-stone-500">
            <div>
              Found <span className="font-semibold text-stone-900">{total}</span> results for &ldquo;{q}&rdquo;
            </div>
            <div className="flex items-center gap-2">
              <span className="text-stone-400">Strategy:</span>
              <span className="font-mono bg-stone-100 px-2 py-0.5 rounded text-stone-700">{strategy}</span>
            </div>
          </div>
        )}

        {errorMsg && (
          <div className="p-4 mb-6 text-xs bg-red-50 border border-red-200 text-red-700 rounded-lg">
            {errorMsg}
          </div>
        )}

        {papers.length > 0 ? (
          <div className="space-y-4">
            {papers.map((paper) => (
              <div
                key={paper.id}
                className="bg-white p-5 rounded-xl border border-stone-200 hover:border-indigo-200 hover:shadow-sm transition-all"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <Link
                      href={`/papers/${paper.id}`}
                      className="text-base font-semibold text-stone-900 hover:text-indigo-600 transition-colors"
                    >
                      {paper.title}
                    </Link>
                    <div className="text-xs text-stone-500 mt-1 flex flex-wrap items-center gap-2">
                      <span>{paper.authors?.map((a) => a.name).join(", ") || "Unknown authors"}</span>
                      {paper.year && <span>&bull; {paper.year}</span>}
                      {paper.venue && <span>&bull; {paper.venue}</span>}
                    </div>
                  </div>
                  {paper.open_access && (
                    <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-semibold tracking-wide uppercase whitespace-nowrap">
                      Open Access
                    </span>
                  )}
                </div>

                {paper.abstract && (
                  <p className="text-xs text-stone-600 mt-3 line-clamp-3 leading-relaxed">
                    {paper.abstract}
                  </p>
                )}

                {paper.explanation?.matched_terms && paper.explanation.matched_terms.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-stone-100 flex items-center gap-2 text-[11px] text-stone-400">
                    <span className="font-medium text-stone-500">Matched:</span>
                    <span className="text-stone-600">{paper.explanation.matched_terms.join(", ")}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : q ? (
          <div className="text-center py-16 bg-white border border-stone-200 rounded-xl">
            <p className="text-sm text-stone-500">No papers found matching your query.</p>
            <p className="text-xs text-stone-400 mt-1">Try broader terms or verify the spelling.</p>
          </div>
        ) : null}
      </main>

      <SiteFooter />
    </div>
  );
}
