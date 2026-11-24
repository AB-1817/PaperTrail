"use client";

import { useState } from "react";
import Link from "next/link";
import { Paper } from "@/lib/api/client";

export function SearchResultCard({ paper }: { paper: Paper }) {
  const [abstractExpanded, setAbstractExpanded] = useState(false);
  const paperHref = `/papers/${encodeURIComponent(paper.doi || paper.id)}`;
  const isLong = (paper.abstract?.length ?? 0) > 240;

  return (
    <div className="card-hover">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <Link
            href={paperHref}
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
        <div className="mt-3">
          <p className={`text-xs text-ash leading-relaxed ${abstractExpanded ? "" : "line-clamp-3"}`}>
            {paper.abstract}
          </p>
          {isLong && (
            <button
              onClick={() => setAbstractExpanded((v) => !v)}
              className="text-[11px] text-primary mt-1 hover:underline"
            >
              {abstractExpanded ? "Show less" : "Show more"}
            </button>
          )}
        </div>
      )}

      <div className="mt-3 pt-3 border-t border-hairline flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-[11px] text-ash">
          {paper.explanation?.matched_terms && paper.explanation.matched_terms.length > 0 && (
            <>
              <span className="font-medium text-stone">Matched:</span>
              <span>{paper.explanation.matched_terms.join(", ")}</span>
            </>
          )}
        </div>
        <Link
          href={`${paperHref}#rag`}
          className="text-[11px] text-primary hover:underline whitespace-nowrap"
        >
          Ask Research Assistant →
        </Link>
      </div>
    </div>
  );
}
