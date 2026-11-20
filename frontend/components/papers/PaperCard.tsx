import Link from "next/link";
import { Paper } from "@/lib/api/client";

export function PaperCard({ paper }: { paper: Paper }) {
  return (
    <div className="bg-white p-5 rounded-xl border border-stone-200 hover:border-indigo-200 hover:shadow-sm transition-all">
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

      {paper.explanation && (
        <div className="mt-3 pt-3 border-t border-stone-100 flex items-center justify-between text-[11px] text-stone-400">
          <div>
            {paper.explanation.details && paper.explanation.details[0] ? (
              <span className="text-stone-600">{paper.explanation.details[0]}</span>
            ) : null}
          </div>
          {paper.score !== undefined && (
            <span className="font-mono bg-stone-100 px-2 py-0.5 rounded text-stone-600">
              Score: {paper.score}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
