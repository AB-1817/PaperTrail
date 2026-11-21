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
      <div className="min-h-screen flex flex-col bg-canvas">
        <SiteHeader />
        <main className="flex-1 max-w-4xl w-full mx-auto px-6 py-24 text-center">
          <h1 className="text-4xl font-light text-ink mb-4"
            style={{ fontFamily: "var(--font-fraunces), Fraunces, Georgia, serif" }}>
            Paper Not Found
          </h1>
          <p className="text-sm text-ash mb-8">The requested paper ID does not exist in our library.</p>
          <Link href="/search" className="btn-primary">
            Back to Search
          </Link>
        </main>
        <SiteFooter />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <SiteHeader />
      <main className="flex-1 max-w-4xl w-full mx-auto px-6 py-10">
        {/* Back Link */}
        <Link href="/search" className="text-xs text-ash hover:text-stone transition-colors inline-block mb-8">
          ← Back to Search
        </Link>

        {/* Paper Header */}
        <div className="card shadow-elevated mb-6">
          <div className="flex items-start justify-between gap-4">
            <h1
              className="text-3xl font-light text-ink leading-snug"
              style={{ fontFamily: "var(--font-fraunces), Fraunces, Georgia, serif" }}
            >
              {paper.title}
            </h1>
            {paper.open_access && (
              <span className="eyebrow text-[9px] px-2.5 py-1 rounded-full border border-sage-pale bg-canvas text-olive whitespace-nowrap">
                Open Access
              </span>
            )}
          </div>

          <div className="mt-3 text-sm text-ash flex flex-wrap items-center gap-2">
            <span>{paper.authors?.map((a) => a.name).join(", ") || "Unknown authors"}</span>
            {paper.year && <span>· {paper.year}</span>}
            {paper.venue && <span>· {paper.venue}</span>}
          </div>

          {paper.doi && (
            <div className="mt-2 text-xs font-mono text-mute">
              DOI:{" "}
              <a
                href={`https://doi.org/${paper.doi}`}
                target="_blank"
                rel="noreferrer"
                className="text-primary hover:underline"
              >
                {paper.doi}
              </a>
            </div>
          )}

          {/* Action Row */}
          <div className="mt-6 pt-5 border-t border-hairline flex flex-wrap items-center gap-3">
            <Link href={`/graph?seed=${paper.id}`} className="btn-outline text-xs px-4 py-2">
              Explore Citation Graph
            </Link>
            {paper.oa_url && (
              <a
                href={paper.oa_url}
                target="_blank"
                rel="noreferrer"
                className="btn-primary text-xs px-4 py-2"
              >
                View PDF
              </a>
            )}
          </div>
        </div>

        {/* Abstract */}
        <div className="card mb-6">
          <p className="eyebrow text-ash mb-4">Abstract</p>
          <p className="text-sm text-stone leading-relaxed">
            {paper.abstract || "Abstract not provided for this document."}
          </p>
        </div>

        {/* References */}
        <div className="card">
          <p className="eyebrow text-ash mb-4">References ({references.length})</p>
          {references.length > 0 ? (
            <div className="divide-y divide-hairline">
              {references.map((ref) => (
                <div key={ref.id} className="py-3 text-xs">
                  <p className="font-medium text-ink">{ref.cited_title || ref.doi_fallback || "Unresolved Reference"}</p>
                  {ref.cited_year && <span className="text-ash">{ref.cited_year}</span>}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-mute italic">No references indexed yet for this paper.</p>
          )}
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
