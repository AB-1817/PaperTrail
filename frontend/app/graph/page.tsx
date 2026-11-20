"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";

interface GraphNode {
  id: string;
  title: string;
  year?: number;
  open_access: boolean;
  is_seed: boolean;
}

interface GraphEdge {
  source: string;
  target: string;
  type: string;
}

export default function GraphPage() {
  const searchParams = useSearchParams();
  const seed = searchParams.get("seed") || "";

  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!seed) return;
    setLoading(true);

    fetch(`http://localhost:8000/api/v1/graph/seed/${seed}`)
      .then((res) => res.json())
      .then((json) => {
        if (json.data) {
          setNodes(json.data.nodes || []);
          setEdges(json.data.edges || []);
          const sNode = json.data.nodes?.find((n: GraphNode) => n.is_seed);
          if (sNode) setSelectedNode(sNode);
        }
      })
      .finally(() => setLoading(false));
  }, [seed]);

  return (
    <div className="min-h-screen flex flex-col bg-stone-50">
      <SiteHeader />
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8 flex flex-col">
        <div className="border-b border-stone-200 pb-4 mb-6">
          <h1 className="text-2xl font-bold text-stone-900 tracking-tight">Citation &amp; Relationship Graph</h1>
          <p className="text-xs text-stone-500 mt-1">
            Explore authentic citation networks and thematic connections between indexed papers.
          </p>
        </div>

        {/* Graph Display Area */}
        <div className="flex-1 bg-white border border-stone-200 rounded-xl p-6 min-h-[500px] flex flex-col items-center justify-center relative overflow-hidden">
          {loading ? (
            <div className="text-xs text-stone-400">Loading citation graph...</div>
          ) : nodes.length > 0 ? (
            <div className="w-full h-full flex flex-col justify-between">
              <div className="text-xs text-stone-400 mb-4">
                Showing <span className="font-semibold text-stone-700">{nodes.length}</span> connected papers and{" "}
                <span className="font-semibold text-stone-700">{edges.length}</span> verified citation edges.
              </div>

              {/* Node List View / Visual Representation */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {nodes.map((node) => (
                  <div
                    key={node.id}
                    onClick={() => setSelectedNode(node)}
                    className={`p-4 rounded-lg border text-xs cursor-pointer transition-all ${
                      selectedNode?.id === node.id
                        ? "border-indigo-600 bg-indigo-50/50 shadow-sm"
                        : "border-stone-200 hover:border-stone-300"
                    }`}
                  >
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          node.is_seed ? "bg-indigo-600" : node.open_access ? "bg-emerald-500" : "bg-stone-400"
                        }`}
                      />
                      <span className="font-semibold text-stone-800 line-clamp-1">{node.title}</span>
                    </div>
                    <span className="text-[11px] text-stone-400">{node.year || "Unknown Year"}</span>
                  </div>
                ))}
              </div>

              {/* Selected Node Drawer */}
              {selectedNode && (
                <div className="mt-6 pt-4 border-t border-stone-100 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-stone-900">{selectedNode.title}</h3>
                    <p className="text-xs text-stone-400">ID: {selectedNode.id}</p>
                  </div>
                  <a
                    href={`/papers/${selectedNode.id}`}
                    className="px-3 py-1.5 rounded-lg bg-stone-900 text-white text-xs font-medium hover:bg-stone-800 transition-colors"
                  >
                    Open Paper Detail &rarr;
                  </a>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-sm text-stone-500">No active paper seed selected for graph exploration.</p>
              <p className="text-xs text-stone-400 mt-1">
                Search for any paper and click &ldquo;Explore Citation Graph&rdquo; to visualize its citation neighborhood.
              </p>
            </div>
          )}
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
