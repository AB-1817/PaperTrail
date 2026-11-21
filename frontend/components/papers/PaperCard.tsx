import Link from "next/link";
import { Paper } from "@/lib/api/client";

export function PaperCard({ paper }: { paper: Paper }) {
  return (
    <div className="card-hover group">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <Link
            href={`/papers/${paper.id}`}
            className="text-base font-medium text-ink hover:text-primary transition-colors leading-snug"
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

      {paper.explanation && (
        <div className="mt-3 pt-3 border-t border-hairline flex items-center justify-between text-[11px] text-ash">
          <div>
            {paper.explanation.details && paper.explanation.details[0] ? (
              <span className="text-stone">{paper.explanation.details[0]}</span>
            ) : null}
          </div>
          {paper.score !== undefined && (
            <span className="font-mono bg-canvas px-2 py-0.5 rounded-sm text-ash border border-hairline">
              {paper.score}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
