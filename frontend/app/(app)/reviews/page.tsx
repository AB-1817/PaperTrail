"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { createClient } from "@/lib/supabase/client";

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

      const res = await fetch("http://localhost:8000/api/v1/reviews", {
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

  useEffect(() => {
    loadReviews();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    const supabase = createClient();
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    if (!token) return;

    await fetch("http://localhost:8000/api/v1/reviews", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ title, description }),
    });

    setShowModal(false);
    setTitle("");
    setDescription("");
    loadReviews();
  }

  return (
    <div className="min-h-screen flex flex-col bg-stone-50">
      <SiteHeader />
      <main className="flex-1 max-w-5xl w-full mx-auto px-6 py-10">
        <div className="flex items-center justify-between border-b border-stone-200 pb-5 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-stone-900 tracking-tight">Literature Review Studio</h1>
            <p className="text-sm text-stone-500 mt-1">
              Synthesize cross-paper findings, methodologies, and comparisons with claim-level evidence citations.
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700 transition-colors shadow-sm"
          >
            + New Project
          </button>
        </div>

        {loading ? (
          <div className="text-center py-20 text-xs text-stone-400">Loading reviews...</div>
        ) : reviews.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {reviews.map((rev) => (
              <Link
                key={rev.id}
                href={`/reviews/${rev.id}`}
                className="bg-white p-6 rounded-xl border border-stone-200 hover:border-indigo-200 hover:shadow-sm transition-all flex flex-col justify-between"
              >
                <div>
                  <h3 className="text-base font-semibold text-stone-900">{rev.title}</h3>
                  {rev.description && (
                    <p className="text-xs text-stone-500 mt-1 line-clamp-2">{rev.description}</p>
                  )}
                </div>
                <div className="mt-4 pt-3 border-t border-stone-100 flex items-center justify-between text-xs text-stone-400">
                  <span>{rev.paper_count} papers</span>
                  <span className="uppercase text-[10px] tracking-wide font-semibold text-stone-600 bg-stone-100 px-2 py-0.5 rounded">
                    {rev.status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="bg-white p-12 text-center rounded-xl border border-stone-200">
            <h3 className="text-sm font-semibold text-stone-900">No review projects yet</h3>
            <p className="text-xs text-stone-500 mt-1 mb-4">
              Create a project to synthesize research across multiple papers.
            </p>
            <button
              onClick={() => setShowModal(true)}
              className="px-4 py-2 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Create Your First Review
            </button>
          </div>
        )}

        {showModal && (
          <div className="fixed inset-0 bg-stone-900/30 backdrop-blur-xs flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-stone-200">
              <h2 className="text-lg font-bold text-stone-900 mb-4">New Literature Review</h2>
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-stone-700 mb-1">Project Title</label>
                  <input
                    type="text"
                    required
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Hallucination Mitigation in RAG"
                    className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-100 focus:border-indigo-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-stone-700 mb-1">Description</label>
                  <textarea
                    rows={3}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Brief description of the research scope"
                    className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-100 focus:border-indigo-600"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-3 py-2 text-xs font-medium text-stone-600 hover:text-stone-900"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-700"
                  >
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
