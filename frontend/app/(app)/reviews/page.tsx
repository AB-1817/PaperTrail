"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { createClient } from "@/lib/supabase/client";
import { API_BASE_URL } from "@/lib/api/client";

interface Review {
  id: string;
  title: string;
  description?: string;
  status: string;
  paper_count: number;
  created_at: string;
}

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  async function loadReviews() {
    try {
      const supabase = createClient();
      const { data } = await supabase.auth.getSession();
      const token = data.session?.access_token;
      if (!token) return;

      const res = await fetch(`${API_BASE_URL}/api/v1/reviews`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      setReviews(json.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadReviews(); }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    const supabase = createClient();
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    if (!token) return;

    await fetch(`${API_BASE_URL}/api/v1/reviews`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ title, description }),
    });

    setShowModal(false);
    setTitle("");
    setDescription("");
    loadReviews();
  }

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <SiteHeader />
      <main className="flex-1 max-w-5xl w-full mx-auto px-6 py-12">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-hairline pb-6 mb-10">
          <div>
            <p className="eyebrow text-ash mb-2">Synthesis</p>
            <h1
              className="text-4xl font-light text-ink"
              style={{ fontFamily: "var(--font-fraunces), Fraunces, Georgia, serif" }}
            >
              Literature Review Studio
            </h1>
            <p className="text-sm text-ash mt-2">
              Synthesize cross-paper findings, methodologies, and comparisons with claim-level evidence citations.
            </p>
          </div>
          <button onClick={() => setShowModal(true)} className="btn-primary text-xs mt-1">
            + New Project
          </button>
        </div>

        {loading ? (
          <div className="text-center py-24 text-xs text-ash">Loading reviews...</div>
        ) : reviews.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {reviews.map((rev) => (
              <Link
                key={rev.id}
                href={`/reviews/${rev.id}`}
                className="card-hover flex flex-col justify-between"
              >
                <div>
                  <h3 className="text-base font-medium text-ink">{rev.title}</h3>
                  {rev.description && (
                    <p className="text-xs text-ash mt-1 line-clamp-2">{rev.description}</p>
                  )}
                </div>
                <div className="mt-5 pt-4 border-t border-hairline flex items-center justify-between text-xs text-ash">
                  <span>{rev.paper_count} papers</span>
                  <span className="eyebrow text-[9px] px-2.5 py-1 rounded-full border border-hairline bg-canvas text-stone">
                    {rev.status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="card shadow-elevated text-center py-16">
            <h3 className="text-sm font-medium text-ink mb-1">No review projects yet</h3>
            <p className="text-xs text-ash mt-1 mb-6">
              Create a project to synthesize research across multiple papers.
            </p>
            <button onClick={() => setShowModal(true)} className="btn-primary">
              Create Your First Review
            </button>
          </div>
        )}

        {/* Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-ink-band/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <div className="card shadow-elevated max-w-md w-full">
              <h2
                className="text-2xl font-light text-ink mb-6"
                style={{ fontFamily: "var(--font-fraunces), Fraunces, Georgia, serif" }}
              >
                New Literature Review
              </h2>
              <form onSubmit={handleCreate} className="space-y-5">
                <div>
                  <label className="block text-xs font-medium text-stone mb-1.5">Project Title</label>
                  <input
                    type="text"
                    required
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Hallucination Mitigation in RAG"
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-stone mb-1.5">Description</label>
                  <textarea
                    rows={3}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Brief description of the research scope"
                    className="input-field resize-none"
                  />
                </div>
                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="btn-outline text-xs px-4 py-2"
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn-primary text-xs px-5 py-2">
                    Create Project
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
      <SiteFooter />
    </div>
  );
}
