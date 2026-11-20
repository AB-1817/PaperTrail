"use client";

import { useEffect, useState } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { PaperCard } from "@/components/papers/PaperCard";
import { createClient } from "@/lib/supabase/client";
import { Paper } from "@/lib/api/client";

export default function RecommendationsPage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadRecs() {
      try {
        const supabase = createClient();
        const { data: sessionData } = await supabase.auth.getSession();
        const token = sessionData.session?.access_token;

        const res = await fetch("http://localhost:8000/api/v1/recommendations/personalized", {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        const json = await res.json();
        setPapers(json.data || []);
      } catch (err) {
        console.error("Failed to load recommendations", err);
      } finally {
        setLoading(false);
      }
    }
    loadRecs();
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-stone-50">
      <SiteHeader />
      <main className="flex-1 max-w-5xl w-full mx-auto px-6 py-10">
        <div className="border-b border-stone-200 pb-5 mb-8">
          <h1 className="text-2xl font-bold text-stone-900 tracking-tight">Personalized Recommendations</h1>
          <p className="text-sm text-stone-500 mt-1">
            Grounded suggestions based on your saved papers, reading interests, and citation structures.
          </p>
        </div>

        {loading ? (
          <div className="text-center py-20 text-xs text-stone-400">Loading recommendations...</div>
        ) : papers.length > 0 ? (
          <div className="space-y-4">
            {papers.map((p) => (
              <PaperCard key={p.id} paper={p} />
            ))}
          </div>
        ) : (
          <div className="bg-white p-12 text-center rounded-xl border border-stone-200">
            <h3 className="text-sm font-semibold text-stone-900">No recommendations available yet</h3>
            <p className="text-xs text-stone-500 mt-1">
              Save papers to your workspace to activate personalized recommendations.
            </p>
          </div>
        )}
      </main>
      <SiteFooter />
    </div>
  );
}
