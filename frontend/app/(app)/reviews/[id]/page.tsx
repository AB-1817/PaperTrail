"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { createClient } from "@/lib/supabase/client";

const SECTIONS = [
  "overview",
  "themes",
  "methodologies",
  "findings",
  "similarities",
  "contradictions",
  "limitations",
  "gaps",
  "future_directions",
];

export default function ReviewDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  const [review, setReview] = useState<any>(null);
  const [papers, setPapers] = useState<any[]>([]);
  const [sections, setSections] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"sections" | "papers" | "matrix">("sections");
  const [generating, setGenerating] = useState<string | null>(null);

  async function loadData() {
    const supabase = createClient();
    const { data: s } = await supabase.auth.getSession();
    const token = s.session?.access_token;
    if (!token) return;

    const [rRes, pRes, sRes] = await Promise.all([
      fetch(`http://localhost:8000/api/v1/reviews/${id}`, { headers: { Authorization: `Bearer ${token}` } }),
      fetch(`http://localhost:8000/api/v1/reviews/${id}/papers`, { headers: { Authorization: `Bearer ${token}` } }),
      fetch(`http://localhost:8000/api/v1/reviews/${id}/sections`, { headers: { Authorization: `Bearer ${token}` } }),
    ]);

    const [rJson, pJson, sJson] = await Promise.all([rRes.json(), pRes.json(), sRes.json()]);
    setReview(rJson);
    setPapers(pJson.data || []);
    setSections(sJson.data || []);
  }

  useEffect(() => {
    loadData();
  }, [id]);

  async function handleGenerate(sectionType: string) {
    setGenerating(sectionType);
    const supabase = createClient();
    const { data: s } = await supabase.auth.getSession();
    const token = s.session?.access_token;
    if (!token) return;

    await fetch(`http://localhost:8000/api/v1/reviews/${id}/sections/${sectionType}/generate`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });

    await loadData();
    setGenerating(null);
  }

  return (
    <div className="min-h-screen flex flex-col bg-stone-50">
      <SiteHeader />
      <main className="flex-1 max-w-5xl w-full mx-auto px-6 py-8">
        <Link href="/reviews" className="text-xs text-stone-500 hover:text-stone-900 transition-colors inline-block mb-4">
          &larr; Back to Projects
        </Link>

        {review && (
          <div className="border-b border-stone-200 pb-5 mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-stone-900 tracking-tight">{review.title}</h1>
              {review.description && <p className="text-xs text-stone-500 mt-1">{review.description}</p>}
            </div>
            <a
              href={`http://localhost:8000/api/v1/reviews/${id}/export`}
              download
              className="px-3.5 py-1.5 rounded-lg border border-stone-300 text-stone-700 text-xs font-medium hover:border-indigo-400 hover:text-indigo-600 transition-colors self-start"
            >
              Export Markdown
            </a>
          </div>
        )}

        {/* Tab Controls */}
        <div className="flex border-b border-stone-200 gap-6 text-xs font-semibold mb-6">
          <button
            onClick={() => setActiveTab("sections")}
            className={`pb-3 border-b-2 transition-colors ${
              activeTab === "sections" ? "border-indigo-600 text-indigo-600" : "border-transparent text-stone-400"
            }`}
          >
            Synthesis Sections ({sections.length}/{SECTIONS.length})
          </button>
          <button
            onClick={() => setActiveTab("papers")}
            className={`pb-3 border-b-2 transition-colors ${
              activeTab === "papers" ? "border-indigo-600 text-indigo-600" : "border-transparent text-stone-400"
            }`}
          >
            Papers in Review ({papers.length})
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === "sections" && (
          <div className="space-y-6">
            {SECTIONS.map((st) => {
              const sec = sections.find((s) => s.section_type === st);
              const isGen = generating === st;

              return (
                <div key={st} className="bg-white p-6 rounded-xl border border-stone-200 shadow-xs">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-bold uppercase tracking-wider text-stone-800">
                        {st.replace("_", " ")}
                      </h3>
                      {sec?.is_abstract_only && (
                        <span className="text-[10px] bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded font-medium">
                          Abstracts Only
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => handleGenerate(st)}
                      disabled={isGen || papers.length === 0}
                      className="text-xs px-3 py-1 rounded bg-stone-900 text-white hover:bg-stone-800 transition-colors disabled:opacity-50"
                    >
                      {isGen ? "Synthesizing..." : sec ? "Regenerate" : "Generate"}
                    </button>
                  </div>

                  {sec ? (
                    <div className="text-sm text-stone-700 leading-relaxed whitespace-pre-line mt-2">
                      {sec.content}
                    </div>
                  ) : (
                    <p className="text-xs text-stone-400 italic">Not generated yet.</p>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {activeTab === "papers" && (
          <div className="bg-white p-6 rounded-xl border border-stone-200 divide-y divide-stone-100">
            {papers.length > 0 ? (
              papers.map((p) => (
                <div key={p.id} className="py-3 flex items-center justify-between text-xs">
                  <div>
                    <h4 className="font-semibold text-stone-900">{p.title}</h4>
                    <span className="text-stone-400">{p.year} &bull; {p.venue}</span>
                  </div>
                  <Link href={`/papers/${p.id}`} className="text-indigo-600 font-medium hover:underline">
                    View
                  </Link>
                </div>
              ))
            ) : (
              <p className="text-xs text-stone-400 text-center py-8">
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
