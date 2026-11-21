"use client";

import { useEffect, useState } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { API_BASE_URL } from "@/lib/api/client";

interface Experiment {
  id: string;
  name: string;
  strategy: string;
  status: string;
  created_at: string;
}

export default function EvaluationPage() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [selectedExp, setSelectedExp] = useState<string | null>(null);
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  async function loadExperiments() {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/evaluation/experiments`);
      const json = await res.json();
      setExperiments(json.data || []);
      if (json.data && json.data.length > 0) {
        setSelectedExp(json.data[0].id);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadExperiments(); }, []);

  useEffect(() => {
    if (!selectedExp) return;
    fetch(`${API_BASE_URL}/api/v1/evaluation/experiments/${selectedExp}/results`)
      .then((res) => res.json())
      .then((json) => setResults(json.data || []));
  }, [selectedExp]);

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <SiteHeader />
      <main className="flex-1 max-w-5xl w-full mx-auto px-6 py-12">
        {/* Header */}
        <div className="border-b border-hairline pb-6 mb-10">
          <p className="eyebrow text-ash mb-2">Measurement</p>
          <h1
            className="text-4xl font-light text-ink"
            style={{ fontFamily: "var(--font-fraunces), Fraunces, Georgia, serif" }}
          >
            Evaluation Lab
          </h1>
          <p className="text-sm text-ash mt-2">
            Reproducible retrieval &amp; RAG quality metrics evaluated strictly against human judgments.
          </p>
        </div>

        {/* Benchmark Integrity Notice */}
        <div className="card border-l-2 border-primary mb-10 bg-surface">
          <p className="text-xs text-stone leading-relaxed">
            <span className="font-semibold text-ink">Benchmark Integrity:</span> All evaluation figures are computed by
            code from stored relevance judgments. No hardcoded scores or simulated perfection.
          </p>
        </div>

        {loading ? (
          <div className="text-center py-24 text-xs text-ash">Loading evaluation experiments...</div>
        ) : experiments.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Experiment List */}
            <div className="space-y-2">
              <p className="eyebrow text-ash mb-3">Experiments</p>
              {experiments.map((exp) => (
                <div
                  key={exp.id}
                  onClick={() => setSelectedExp(exp.id)}
                  className={`card text-xs cursor-pointer transition-all ${
                    selectedExp === exp.id
                      ? "border-primary shadow-card"
                      : "hover:border-[#c4bdb2]"
                  }`}
                >
                  <div className="font-medium text-ink">{exp.name}</div>
                  <div className="text-[10px] text-ash mt-1 flex items-center justify-between">
                    <span className="font-mono">{exp.strategy}</span>
                    <span className="uppercase tracking-wide">{exp.status}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Results Panel */}
            <div className="md:col-span-2 card">
              <p className="eyebrow text-ash mb-5">Results</p>
              {results.length > 0 ? (
                <div className="divide-y divide-hairline">
                  {results.map((r, i) => (
                    <div key={i} className="py-3 flex items-center justify-between text-xs">
                      <span className="font-medium text-stone">{r.metric}</span>
                      <span className="font-mono font-semibold text-ink">{r.value}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-mute italic">
                  Pending run. Execute benchmark to measure genuine retrieval quality.
                </p>
              )}
            </div>
          </div>
        ) : (
          <div className="card shadow-elevated text-center py-16">
            <h3 className="text-sm font-medium text-ink mb-1">No evaluation runs recorded yet</h3>
            <p className="text-xs text-ash mt-1">
              Configure human judgments in <code className="font-mono text-stone">evaluation_datasets</code> to trigger reproducible experiments.
            </p>
          </div>
        )}
      </main>
      <SiteFooter />
    </div>
  );
}
