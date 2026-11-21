"use client";

import { useEffect, useState } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { PaperCard } from "@/components/papers/PaperCard";
import { createClient } from "@/lib/supabase/client";
import { Paper, API_BASE_URL } from "@/lib/api/client";

export default function RecommendationsPage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadRecs() {
      try {
        const supabase = createClient();
        const { data: sessionData } = await supabase.auth.getSession();
        const token = sessionData.session?.access_token;

        const res = await fetch(`${API_BASE_URL}/api/v1/recommendations/personalized`, {
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
    <div className="min-h-screen flex flex-col bg-canvas">
      <SiteHeader />
      <main className="flex-1 max-w-5xl w-full mx-auto px-6 py-12">
        <div className="border-b border-hairline pb-6 mb-10">
          <p className="eyebrow text-ash mb-2">Discovery</p>
          <h1
            className="text-4xl font-light text-ink"
            style={{ fontFamily: "var(--font-fraunces), Fraunces, Georgia, serif" }}
          >
            Personalized Recommendations
          </h1>
          <p className="text-sm text-ash mt-2">
            Grounded suggestions based on your saved papers, reading interests, and citation structures.
          </p>
        </div>

        {loading ? (
          <div className="text-center py-24 text-xs text-ash">Loading recommendations...</div>
        ) : papers.length > 0 ? (
          <div className="space-y-3">
            {papers.map((p) => (
              <PaperCard key={p.id} paper={p} />
            ))}
          </div>
        ) : (
          <div className="card shadow-elevated text-center py-16">
            <h3 className="text-sm font-medium text-ink mb-1">No recommendations available yet</h3>
            <p className="text-xs text-ash mt-1">
              Save papers to your workspace to activate personalized recommendations.
            </p>
          </div>
        )}
      </main>
      <SiteFooter />
    </div>
  );
}
