import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import Link from "next/link";

const STAT_CARDS = [
  { label: "Saved Papers", value: "0" },
  { label: "Collections", value: "0" },
  { label: "Notes", value: "0" },
  { label: "Reading Queue", value: "0" },
];

export default function WorkspacePage() {
  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <SiteHeader />
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-12">
        {/* Page Header */}
        <div className="border-b border-hairline pb-6 mb-10">
          <p className="eyebrow text-ash mb-2">Your Library</p>
          <h1
            className="text-4xl font-light text-ink"
            style={{ fontFamily: "var(--font-fraunces), Fraunces, Georgia, serif" }}
          >
            Research Workspace
          </h1>
          <p className="text-sm text-ash mt-2">
            Organize your papers, curate collections, record synthesis notes, and track your reading queue.
          </p>
        </div>

        {/* Stat Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10">
          {STAT_CARDS.map((s) => (
            <div key={s.label} className="card text-center">
              <p className="eyebrow text-ash mb-2">{s.label}</p>
              <p
                className="text-4xl font-light text-stone"
                style={{ fontFamily: "var(--font-fraunces), Fraunces, Georgia, serif" }}
              >
                {s.value}
              </p>
            </div>
          ))}
        </div>

        {/* Empty State */}
        <div className="card shadow-elevated flex flex-col items-center justify-center min-h-[320px] text-center">
          <div className="w-14 h-14 rounded-full bg-canvas border border-hairline flex items-center justify-center text-2xl mb-5">
            📚
          </div>
          <h3 className="text-base font-medium text-ink mb-1">Your workspace is ready</h3>
          <p className="text-xs text-ash max-w-sm mb-8 leading-relaxed">
            Search genuine academic papers and click &ldquo;Save to Workspace&rdquo; or start by discovering new research.
          </p>
          <Link href="/search" className="btn-primary">
            Explore Literature
          </Link>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
