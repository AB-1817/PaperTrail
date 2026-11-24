"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { getPaper, getPaperReferences, queryRAG, RAGResult } from "@/lib/api/client";
import { createClient } from "@/lib/supabase/client";
import Link from "next/link";

const SUGGESTED_QUESTIONS = [
  "What methodology does this paper use?",
  "What are the key findings?",
  "What are the limitations?",
  "What datasets were used?",
  "How does this compare to prior work?",
];

function Skeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-8 bg-surface rounded w-3/4" />
      <div className="h-4 bg-surface rounded w-1/2" />
      <div className="h-4 bg-surface rounded w-1/3" />
      <div className="h-24 bg-surface rounded mt-6" />
    </div>
  );
}

export default function PaperDetailPage() {
  const params = useParams();
  const id = params?.id;
  const paperId = decodeURIComponent(Array.isArray(id) ? id.join("/") : id ?? "");

  const [paper, setPaper] = useState<any>(null);
  const [references, setReferences] = useState<any[]>([]);
  const [notFound, setNotFound] = useState(false);
  const [abstractExpanded, setAbstractExpanded] = useState(false);
  const [citationsExpanded, setCitationsExpanded] = useState(false);

  // RAG state
  const [question, setQuestion] = useState("");
  const [ragResult, setRagResult] = useState<RAGResult | null>(null);
  const [ragError, setRagError] = useState<string | null>(null);
  const [ragLoading, setRagLoading] = useState(false);
  const [isSignedIn, setIsSignedIn] = useState<boolean | null>(null);

  useEffect(() => {
    async function load() {
      const res: any = await getPaper(paperId);
      const p = res?.data || (res?.id ? res : null);
      if (!p) { setNotFound(true); return; }
      setPaper(p);
      const refRes = await getPaperReferences(paperId);
      setReferences(refRes?.data || []);
    }
    async function checkAuth() {
      try {
        const supabase = createClient();
        const { data } = await supabase.auth.getSession();
        setIsSignedIn(!!data.session?.access_token);
      } catch {
        setIsSignedIn(false);
      }
    }
    if (paperId) { load(); checkAuth(); }
  }, [paperId]);

  async function submitRAG(e: React.FormEvent) {
    e.preventDefault();
    setRagLoading(true);
    setRagError(null);
    setRagResult(null);
    try {
      const supabase = createClient();
      const { data } = await supabase.auth.getSession();
      const token = data.session?.access_token;
      if (!token) { setRagError("Sign in to use the research assistant."); return; }
      const res = await queryRAG(question.trim(), token, [paperId]);
      if (res.error) setRagError(res.error.message);
      else if (res.data) setRagResult(res.data);
    } catch (err) {
      setRagError(err instanceof Error ? err.message : "RAG query failed.");
    } finally {
      setRagLoading(false);
    }
  }

  if (notFound) {
    return (
      <div className="min-h-screen flex flex-col bg-canvas">
        <SiteHeader />
        <main className="flex-1 max-w-4xl w-full mx-auto px-6 py-24 text-center">
          <h1 className="text-4xl font-light text-ink mb-4"
            style={{ fontFamily: "var(--font-fraunces), Fraunces, Georgia, serif" }}>
            Paper Not Found
          </h1>
          <p className="text-sm text-ash mb-8">The requested paper ID does not exist in our library.</p>
          <Link href="/search" className="btn-primary">Back to Search</Link>
        </main>
        <SiteFooter />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <SiteHeader />
      <main className="flex-1 max-w-4xl w-full mx-auto px-6 py-10">
        <Link href="/search" className="text-xs text-ash hover:text-stone transition-colors inline-block mb-8">
          ← Back to Search
        </Link>

        {!paper ? (
          <div className="card shadow-elevated mb-6"><Skeleton /></div>
        ) : (
          <>
            {/* Paper header */}
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
                <span>{paper.authors?.map((a: { name: string }) => a.name).join(", ") || "Unknown authors"}</span>
                {paper.year && <span>· {paper.year}</span>}
                {paper.venue && <span>· {paper.venue}</span>}
              </div>

              {paper.doi && (
                <div className="mt-2 text-xs font-mono text-mute">
                  DOI:{" "}
                  <a href={`https://doi.org/${paper.doi}`} target="_blank" rel="noreferrer" className="text-primary hover:underline">
                    {paper.doi}
                  </a>
                </div>
              )}

              <div className="mt-6 pt-5 border-t border-hairline flex flex-wrap items-center gap-3">
                <Link href={`/graph?seed=${encodeURIComponent(paper.id)}`} className="btn-outline text-xs px-4 py-2">
                  Explore Citation Graph
                </Link>
                {paper.oa_url && (
                  <a href={paper.oa_url} target="_blank" rel="noreferrer" className="btn-primary text-xs px-4 py-2">
                    View PDF
                  </a>
                )}
                <a href="#rag" className="btn-outline text-xs px-4 py-2">
                  Ask Research Assistant ↓
                </a>
              </div>
            </div>

            {/* Abstract — expandable */}
            <div className="card mb-6">
              <p className="eyebrow text-ash mb-4">Abstract</p>
              {paper.abstract ? (
                <>
                  <p className={`text-sm text-stone leading-relaxed ${abstractExpanded ? "" : "line-clamp-4"}`}>
                    {paper.abstract}
                  </p>
                  <button
                    onClick={() => setAbstractExpanded((v) => !v)}
                    className="text-xs text-primary mt-2 hover:underline"
                  >
                    {abstractExpanded ? "Show less" : "Show more"}
                  </button>
                </>
              ) : (
                <p className="text-sm text-stone leading-relaxed">Abstract not provided for this document.</p>
              )}
            </div>

            {/* RAG Research Assistant */}
            <div id="rag" className="card mb-6">
              <p className="eyebrow text-ash mb-1">Research Assistant</p>
              <p className="text-xs text-mute mb-4">Ask a question grounded in this paper's indexed content.</p>

              {isSignedIn === false ? (
                <div className="flex items-center justify-between gap-4 p-3 rounded-lg border border-hairline bg-surface">
                  <p className="text-xs text-stone">Sign in to use the research assistant.</p>
                  <Link href="/login" className="btn-primary text-xs px-4 py-1.5 whitespace-nowrap">Sign in</Link>
                </div>
              ) : (
                <form onSubmit={submitRAG} className="space-y-3">
                  {/* Suggested question chips */}
                  <div className="flex flex-wrap gap-2">
                    {SUGGESTED_QUESTIONS.map((q) => (
                      <button
                        key={q}
                        type="button"
                        onClick={() => setQuestion(q)}
                        className={`text-[11px] px-3 py-1 rounded-full border transition-colors ${
                          question === q
                            ? "border-primary text-primary bg-canvas"
                            : "border-hairline text-stone hover:border-stone hover:text-ink"
                        }`}
                      >
                        {q}
                      </button>
                    ))}
                  </div>

                  <textarea
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    rows={3}
                    minLength={3}
                    maxLength={1000}
                    placeholder={`Ask anything about "${paper.title}"…`}
                    className="input-field resize-y w-full"
                  />
                  <button
                    type="submit"
                    disabled={ragLoading || question.trim().length < 3}
                    className="btn-primary text-xs px-4 py-2"
                  >
                    {ragLoading ? "Grounding answer…" : "Ask"}
                  </button>
                </form>
              )}

              {ragError && (
                <p className="text-xs text-error mt-3">{ragError}</p>
              )}

              {ragResult && (
                <div className="mt-5 space-y-4">
                  <div className="border-t border-hairline pt-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="eyebrow text-ash">Answer</p>
                      <span className="text-xs border border-hairline rounded-full px-3 py-1 text-stone">
                        {ragResult.grounding_status} · {Math.round(ragResult.grounded_claim_fraction * 100)}% grounded
                      </span>
                    </div>
                    <p className="text-sm text-ink leading-relaxed whitespace-pre-wrap">{ragResult.answer}</p>
                  </div>

                  {ragResult.citations.length > 0 && (
                    <div className="border-t border-hairline pt-4">
                      <button
                        onClick={() => setCitationsExpanded((v) => !v)}
                        className="eyebrow text-ash mb-3 flex items-center gap-2 hover:text-stone transition-colors"
                      >
                        Citations ({ragResult.citations.length})
                        <span className="text-[10px]">{citationsExpanded ? "▲" : "▼"}</span>
                      </button>
                      {citationsExpanded && (
                        <div className="space-y-3">
                          {ragResult.citations.map((c, i) => (
                            <div key={`${c.chunk_id}-${i}`} className="text-xs">
                              <div className="flex flex-wrap items-center gap-2 mb-1">
                                <span className="font-mono text-stone">{c.chunk_id}</span>
                                {c.page_number !== null && <span className="text-ash">Page {c.page_number}</span>}
                                <span className={c.is_grounded ? "text-olive" : "text-error"}>
                                  {c.is_grounded ? "Grounded" : "Unverified"}
                                </span>
                              </div>
                              <p className="text-ink mb-1">{c.claim_text}</p>
                              {c.passage && (
                                <blockquote className="text-ash border-l-2 border-hairline pl-3 leading-relaxed">
                                  {c.passage}
                                </blockquote>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* References */}
            <div className="card">
              <p className="eyebrow text-ash mb-4">References ({references.length})</p>
              {references.length > 0 ? (
                <div className="divide-y border-hairline">
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
          </>
        )}
      </main>
      <SiteFooter />
    </div>
  );
}
