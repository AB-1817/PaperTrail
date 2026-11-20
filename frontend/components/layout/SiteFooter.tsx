import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-stone-200 bg-white py-8 text-stone-500 text-xs">
      <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <span className="font-semibold text-stone-800">PaperTrail</span> &mdash; Research Intelligence &amp; Discovery Platform
        </div>
        <div className="flex items-center gap-4 text-stone-400">
          <span>OpenAlex</span>
          <span>&bull;</span>
          <span>Semantic Scholar</span>
          <span>&bull;</span>
          <span>arXiv</span>
          <span>&bull;</span>
          <span>Crossref</span>
          <span>&bull;</span>
          <span>Unpaywall</span>
        </div>
        <div>
          &copy; {new Date().getFullYear()} PaperTrail. Evidence-grounded.
        </div>
      </div>
    </footer>
  );
}
