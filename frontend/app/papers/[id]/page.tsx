import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { getPaper, getPaperReferences } from "@/lib/api/client";
import Link from "next/link";

interface PaperDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function PaperDetailPage({ params }: PaperDetailPageProps) {
  const { id } = await params;
  const res = await getPaper(id);
  const paper = res.data;
  const refRes = await getPaperReferences(id);
  const references = refRes.data || [];

  if (!paper) {
    return (
      <div className="min-h-screen flex flex-col bg-stone-50">
        <SiteHeader />
        <main className="flex-1 max-w-4xl w-full mx-auto px-6 py-16 text-center">
          <h1 className="text-2xl font-bold text-stone-900">Paper Not Found</h1>
          <p className="text-sm text-stone-500 mt-2">The requested paper ID does not exist in our library.</p>
          <Link href="/search" className="mt-6 inline-block px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold">
            Back to Search
          </Link>
        </main>
        <SiteFooter />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-stone-50">
      <SiteHeader />
      <main className="flex-1 max-w-4xl w-full mx-auto px-6 py-10">
        {/* Back Link */}
        <Link href="/search" className="text-xs text-stone-500 hover:text-stone-900 transition-colors inline-block mb-6">
          &larr; Back to Search
        </Link>

        {/* Paper Header */}
        <div className="bg-white p-8 rounded-xl border border-stone-200 mb-8 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <h1 className="text-2xl font-bold text-stone-900 leading-snug">{paper.title}</h1>
            {paper.open_access && (
              <span className="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold tracking-wide uppercase whitespace-nowrap">
                Open Access
              </span>
            )}
          </div>

          <div className="mt-3 text-sm text-stone-600 flex flex-wrap items-center gap-2">
            <span>{paper.authors?.map((a) => a.name).join(", ") || "Unknown authors"}</span>
            {paper.year && <span>&bull; {paper.year}</span>}
            {paper.venue && <span>&bull; {paper.venue}</span>}
          </div>

          {paper.doi && (
            <div className="mt-2 text-xs font-mono text-stone-400">
              DOI: <a href={`https://doi.org/${paper.doi}`} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">{paper.doi}</a>
            </div>
          )}

          {/* Action Row */}
          <div className="mt-6 pt-6 border-t border-stone-100 flex flex-wrap items-center gap-3">
            <Link
              href={`/graph?seed=${paper.id}`}
              className="px-3.5 py-1.5 rounded-lg border border-stone-300 text-stone-700 text-xs font-medium hover:border-indigo-400 hover:text-indigo-600 transition-all"
            >
              Explore Citation Graph
            </Link>
            {paper.oa_url && (
              <a
                href={paper.oa_url}
                target="_blank"
                rel="noreferrer"
                className="px-3.5 py-1.5 rounded-lg bg-emerald-600 text-white text-xs font-medium hover:bg-emerald-700 transition-colors"
              >
                View PDF
              </a>
            )}
          </div>
        </div>

        {/* Abstract */}
        <div className="bg-white p-8 rounded-xl border border-stone-200 mb-8">
          <h2 className="text-sm uppercase font-semibold text-stone-400 tracking-wider mb-3">Abstract</h2>
          <p className="text-sm text-stone-700 leading-relaxed">
            {paper.abstract || "Abstract not provided for this document."}
          </p>
        </div>

        {/* References */}
        <div className="bg-white p-8 rounded-xl border border-stone-200">
          <h2 className="text-sm uppercase font-semibold text-stone-400 tracking-wider mb-4">
            References ({references.length})
          </h2>
          {references.length > 0 ? (
            <div className="divide-y divide-stone-100">
              {references.map((ref) => (
                <div key={ref.id} className="py-3 text-xs">
                  <p className="font-medium text-stone-900">{ref.cited_title || ref.doi_fallback || "Unresolved Reference"}</p>
                  {ref.cited_year && <span className="text-stone-400">{ref.cited_year}</span>}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-stone-400">No references indexed yet for this paper.</p>
          )}
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
