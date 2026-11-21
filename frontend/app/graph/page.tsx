"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { API_BASE_URL } from "@/lib/api/client";

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
    fetch(`${API_BASE_URL}/api/v1/graph/seed/${encodeURIComponent(seed)}`)
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
    <div className="min-h-screen flex flex-col bg-canvas">
      <SiteHeader />
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-12 flex flex-col">
        {/* Header */}
        <div className="border-b border-hairline pb-6 mb-8">
          <p className="eyebrow text-ash mb-2">Network Explorer</p>
          <h1
            className="text-4xl font-light text-ink"
            style={{ fontFamily: "var(--font-fraunces), Fraunces, Georgia, serif" }}
          >
            Citation &amp; Relationship Graph
          </h1>
          <p className="text-xs text-ash mt-2">
            Explore authentic citation networks and thematic connections between indexed papers.
          </p>
        </div>

        {/* Graph Canvas */}
        <div className="flex-1 card shadow-elevated min-h-[520px] flex flex-col overflow-hidden">
          {loading ? (
            <div className="flex-1 flex items-center justify-center text-xs text-ash">
              Loading citation graph...
            </div>
          ) : nodes.length > 0 ? (
            <div className="flex flex-col h-full">
              <div className="text-xs text-ash mb-5">
                Showing <span className="font-semibold text-ink">{nodes.length}</span> connected papers
                and <span className="font-semibold text-ink">{edges.length}</span> verified citation edges.
              </div>

              {/* Node Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 flex-1">
                {nodes.map((node) => (
                  <div
                    key={node.id}
                    onClick={() => setSelectedNode(node)}
                    className={`card text-xs cursor-pointer transition-all ${
                      selectedNode?.id === node.id
                        ? "border-primary shadow-card"
                        : "hover:border-[#c4bdb2]"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1.5">
                      <span
                        className={`w-2 h-2 rounded-full flex-shrink-0 ${
                          node.is_seed ? "bg-primary" : node.open_access ? "bg-olive" : "bg-ash"
                        }`}
                      />
                      <span className="font-medium text-ink line-clamp-1">{node.title}</span>
                    </div>
                    <span className="text-[11px] text-ash">{node.year || "Unknown Year"}</span>
                  </div>
                ))}
              </div>

              {/* Selected Node Detail */}
              {selectedNode && (
                <div className="mt-6 pt-5 border-t border-hairline flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-ink">{selectedNode.title}</h3>
                    <p className="text-xs text-ash mt-0.5">ID: {selectedNode.id}</p>
                  </div>
                  <a
                    href={`/papers/${selectedNode.id}`}
                    className="btn-secondary text-xs px-4 py-2"
                  >
                    Open Paper →
                  </a>
                </div>
              )}
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center py-16">
              <p className="text-sm text-stone">No active paper seed selected for graph exploration.</p>
              <p className="text-xs text-ash mt-2 max-w-xs leading-relaxed">
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
