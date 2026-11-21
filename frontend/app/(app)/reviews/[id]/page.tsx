"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { createClient } from "@/lib/supabase/client";
import { API_BASE_URL } from "@/lib/api/client";

const SECTIONS = [
  "overview", "themes", "methodologies", "findings",
  "similarities", "contradictions", "limitations", "gaps", "future_directions",
];

export default function ReviewDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  const [review, setReview] = useState<any>(null);
  const [papers, setPapers] = useState<any[]>([]);
  const [sections, setSections] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"sections" | "papers">("sections");
  const [generating, setGenerating] = useState<string | null>(null);

  async function loadData() {
    const supabase = createClient();
    const { data: s } = await supabase.auth.getSession();
    const token = s.session?.access_token;
    if (!token) return;

    const [rRes, pRes, sRes] = await Promise.all([
      fetch(`${API_BASE_URL}/api/v1/reviews/${id}`, { headers: { Authorization: `Bearer ${token}` } }),
      fetch(`${API_BASE_URL}/api/v1/reviews/${id}/papers`, { headers: { Authorization: `Bearer ${token}` } }),
      fetch(`${API_BASE_URL}/api/v1/reviews/${id}/sections`, { headers: { Authorization: `Bearer ${token}` } }),
    ]);
    const [rJson, pJson, sJson] = await Promise.all([rRes.json(), pRes.json(), sRes.json()]);
    setReview(rJson);
    setPapers(pJson.data || []);
    setSections(sJson.data || []);
  }

  useEffect(() => { loadData(); }, [id]);

  async function handleGenerate(sectionType: string) {
    setGenerating(sectionType);
    const supabase = createClient();
    const { data: s } = await supabase.auth.getSession();
    const token = s.session?.access_token;
    if (!token) return;

    await fetch(`${API_BASE_URL}/api/v1/reviews/${id}/sections/${sectionType}/generate`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    await loadData();
    setGenerating(null);
  }

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <SiteHeader />
      <main className="flex-1 max-w-5xl w-full mx-auto px-6 py-10">
        <Link href="/reviews" className="text-xs text-ash hover:text-stone transition-colors inline-block mb-6">
          ← Back to Projects
        </Link>

        {review && (
          <div className="border-b border-hairline pb-6 mb-8 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div>
              <p className="eyebrow text-ash mb-2">Literature Review</p>
              <h1
                className="text-3xl font-light text-ink"
                style={{ fontFamily: "var(--font-fraunces), Fraunces, Georgia, serif" }}
              >
                {review.title}
              </h1>
              {review.description && <p className="text-xs text-ash mt-2">{review.description}</p>}
            </div>
            <a
              href={`${API_BASE_URL}/api/v1/reviews/${id}/export`}
              download
              className="btn-outline text-xs px-4 py-2 self-start"
            >
              Export Markdown
            </a>
          </div>
        )}

        {/* Tabs */}
        <div className="flex border-b border-hairline gap-8 text-xs font-semibold mb-8">
          {(["sections", "papers"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-3 border-b-2 transition-colors capitalize ${
                activeTab === tab ? "border-primary text-primary" : "border-transparent text-ash hover:text-stone"
              }`}
            >
              {tab === "sections"
                ? `Synthesis Sections (${sections.length}/${SECTIONS.length})`
                : `Papers in Review (${papers.length})`}
            </button>
          ))}
        </div>

        {/* Sections Tab */}
        {activeTab === "sections" && (
          <div className="space-y-5">
            {SECTIONS.map((st) => {
              const sec = sections.find((s) => s.section_type === st);
              const isGen = generating === st;

              return (
                <div key={st} className="card shadow-card">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <p className="eyebrow text-stone">{st.replace("_", " ")}</p>
                      {sec?.is_abstract_only && (
                        <span className="text-[9px] eyebrow border border-gold/40 bg-canvas text-gold px-2 py-0.5 rounded-full">
                          Abstracts Only
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => handleGenerate(st)}
                      disabled={isGen || papers.length === 0}
                      className="btn-secondary text-xs px-4 py-1.5 disabled:opacity-40"
                    >
                      {isGen ? "Synthesizing..." : sec ? "Regenerate" : "Generate"}
                    </button>
                  </div>

                  {sec ? (
                    <div className="text-sm text-stone leading-relaxed whitespace-pre-line">
                      {sec.content}
                    </div>
                  ) : (
                    <p className="text-xs text-mute italic">Not generated yet.</p>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Papers Tab */}
        {activeTab === "papers" && (
          <div className="card divide-y divide-hairline">
            {papers.length > 0 ? (
              papers.map((p) => (
                <div key={p.id} className="py-4 flex items-center justify-between text-xs">
                  <div>
                    <h4 className="font-medium text-ink">{p.title}</h4>
                    <span className="text-ash">{p.year} · {p.venue}</span>
                  </div>
                  <Link href={`/papers/${p.id}`} className="text-primary font-medium hover:underline">
                    View →
                  </Link>
                </div>
              ))
            ) : (
              <p className="text-xs text-mute text-center py-10 italic">
                No papers added to this review yet. Search papers and click Add to Review.
              </p>
            )}
          </div>
        )}
      </main>
      <SiteFooter />
    </div>
  );
}
