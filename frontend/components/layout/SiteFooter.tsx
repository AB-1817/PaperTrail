import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="bg-ink-band-soft text-on-primary text-xs">
      <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col sm:flex-row items-center justify-between gap-6">
        <div>
          <span
            className="font-semibold text-sm text-white"
            style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif" }}
          >
            PaperTrail
          </span>
          <span className="text-mute ml-2">— Research Intelligence &amp; Discovery</span>
        </div>

        <div className="flex items-center gap-4 text-mute">
          <span>OpenAlex</span>
          <span className="text-ash">·</span>
          <span>Semantic Scholar</span>
          <span className="text-ash">·</span>
          <span>arXiv</span>
          <span className="text-ash">·</span>
          <span>Crossref</span>
          <span className="text-ash">·</span>
          <span>Unpaywall</span>
        </div>

        <div className="text-mute">
          &copy; 2026 PaperTrail. Evidence-grounded.
        </div>
      </div>
    </footer>
  );
}
