"use client";

import { useEffect, useState } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";

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
      const res = await fetch("http://localhost:8000/api/v1/evaluation/experiments");
      const json = await res.json();
      setExperiments(json.data || []);
      if (json.data && json.data.length > 0) {
        setSelectedExp(json.data[0].id);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadExperiments();
  }, []);

  useEffect(() => {
    if (!selectedExp) return;
    fetch(`http://localhost:8000/api/v1/evaluation/experiments/${selectedExp}/results`)
      .then((res) => res.json())
      .then((json) => setResults(json.data || []));
  }, [selectedExp]);

  return (
    <div className="min-h-screen flex flex-col bg-stone-50">
      <SiteHeader />
      <main className="flex-1 max-w-5xl w-full mx-auto px-6 py-10">
        <div className="border-b border-stone-200 pb-5 mb-8">
          <h1 className="text-2xl font-bold text-stone-900 tracking-tight">Evaluation Lab</h1>
          <p className="text-sm text-stone-500 mt-1">
            Reproducible retrieval &amp; RAG quality metrics evaluated strictly against human judgments.
          </p>
        </div>

        {/* Benchmark notice */}
        <div className="bg-indigo-50/50 border border-indigo-100 p-4 rounded-xl text-xs text-indigo-900 mb-8">
          <span className="font-semibold">Benchmark Integrity:</span> All evaluation figures are computed by code from
          stored relevance judgments. No hardcoded scores or simulated perfection.
        </div>

        {loading ? (
          <div className="text-center py-20 text-xs text-stone-400">Loading evaluation experiments...</div>
        ) : experiments.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <h2 className="text-xs uppercase font-semibold text-stone-400 tracking-wider mb-2">Experiments</h2>
              {experiments.map((exp) => (
                <div
                  key={exp.id}
                  onClick={() => setSelectedExp(exp.id)}
                  className={`p-3 rounded-lg border text-xs cursor-pointer transition-all ${
                    selectedExp === exp.id
                      ? "border-indigo-600 bg-white shadow-xs font-semibold"
                      : "border-stone-200 hover:border-stone-300 bg-white"
                  }`}
                >
                  <div className="text-stone-900">{exp.name}</div>
                  <div className="text-[10px] text-stone-400 mt-1 flex items-center justify-between">
                    <span className="font-mono">{exp.strategy}</span>
                    <span className="uppercase">{exp.status}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="md:col-span-2 bg-white p-6 rounded-xl border border-stone-200">
              <h2 className="text-xs uppercase font-semibold text-stone-400 tracking-wider mb-4">Results</h2>
              {results.length > 0 ? (
                <div className="divide-y divide-stone-100">
                  {results.map((r, i) => (
                    <div key={i} className="py-2.5 flex items-center justify-between text-xs">
                      <span className="font-medium text-stone-700">{r.metric}</span>
                      <span className="font-mono font-semibold text-stone-900">{r.value}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-stone-400 italic">
                  Pending run. Execute benchmark to measure genuine retrieval quality.
                </p>
              )}
            </div>
          </div>
        ) : (
          <div className="bg-white p-12 text-center rounded-xl border border-stone-200">
            <h3 className="text-sm font-semibold text-stone-900">No evaluation runs recorded yet</h3>
            <p className="text-xs text-stone-500 mt-1">
              Configure human judgments in `evaluation_datasets` to trigger reproducible experiments.
            </p>
          </div>
        )}
      </main>
      <SiteFooter />
    </div>
  );
}
