import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { SearchBar } from "@/components/search/SearchBar";
import { SearchResultCard } from "@/components/papers/SearchResultCard";
import { searchPapers, Paper } from "@/lib/api/client";

interface SearchPageProps {
  searchParams: Promise<{ q?: string; page?: string; strategy?: string }>;
}

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const { q = "", page = "1", strategy = "hybrid_rrf" } = await searchParams;
  const pageNum = parseInt(page, 10) || 1;

  let papers: Paper[] = [];
  let total = 0;
  let errorMsg: string | null = null;
  let liveSourced = false;

  if (q.trim()) {
    const res = await searchPapers(q, pageNum, strategy);
    if (res.error) {
      errorMsg = res.error.message;
    } else {
      papers = res.data || [];
      total = res.meta?.total || papers.length;
      liveSourced = res.meta?.live_sourced === true;
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
            <div className="flex items-center gap-3">
              <span>
                Found <span className="font-semibold text-ink">{total}</span> results for &ldquo;{q}&rdquo;
              </span>
              {liveSourced && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-sage-pale bg-canvas text-olive text-[10px] font-medium">
                  ✦ Live fetched &amp; saved
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-mute">Strategy:</span>
              <span className="font-mono bg-canvas px-2 py-0.5 rounded-sm border border-hairline text-stone">
                {strategy}
              </span>
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
              <SearchResultCard key={paper.id} paper={paper} />
            ))}
          </div>
        ) : q ? (
          <div className="text-center py-20 bg-surface border border-hairline rounded-lg">
            <p className="text-sm text-stone">No papers found matching your query.</p>
            <p className="text-xs text-ash mt-1">
              Try broader terms or verify the spelling.
              {errorMsg == null && " The backend may be offline."}
            </p>
          </div>
        ) : (
          <div className="text-center py-20 bg-surface border border-hairline rounded-lg">
            <p className="text-sm text-stone">
              Type a keyword, title, author, or concept above to begin searching.
            </p>
            <p className="text-xs text-ash mt-1">
              Results are fetched live from OpenAlex &amp; arXiv and cached for instant future access.
            </p>
          </div>
        )}
      </main>

      <SiteFooter />
    </div>
  );
}
