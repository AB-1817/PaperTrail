import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import Link from "next/link";

export default function WorkspacePage() {
  return (
    <div className="min-h-screen flex flex-col bg-stone-50">
      <SiteHeader />
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-10">
        <div className="border-b border-stone-200 pb-5 mb-8">
          <h1 className="text-2xl font-bold text-stone-900 tracking-tight">Research Workspace</h1>
          <p className="text-sm text-stone-500 mt-1">
            Organize your papers, curate collections, record synthesis notes, and track your reading queue.
          </p>
        </div>

        {/* Workspace Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-5 rounded-lg border border-stone-200">
            <span className="text-xs uppercase font-medium text-stone-400">Saved Papers</span>
            <p className="text-2xl font-bold text-stone-900 mt-2">0</p>
          </div>
          <div className="bg-white p-5 rounded-lg border border-stone-200">
            <span className="text-xs uppercase font-medium text-stone-400">Collections</span>
            <p className="text-2xl font-bold text-stone-900 mt-2">0</p>
          </div>
          <div className="bg-white p-5 rounded-lg border border-stone-200">
            <span className="text-xs uppercase font-medium text-stone-400">Notes</span>
            <p className="text-2xl font-bold text-stone-900 mt-2">0</p>
          </div>
          <div className="bg-white p-5 rounded-lg border border-stone-200">
            <span className="text-xs uppercase font-medium text-stone-400">Reading Queue</span>
            <p className="text-2xl font-bold text-stone-900 mt-2">0</p>
          </div>
        </div>

        {/* Section Tabs & Content */}
        <div className="bg-white rounded-xl border border-stone-200 p-8 text-center min-h-[300px] flex flex-col items-center justify-center">
          <div className="w-12 h-12 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center font-semibold mb-3">
            📚
          </div>
          <h3 className="text-base font-semibold text-stone-900">Your workspace is ready</h3>
          <p className="text-xs text-stone-500 max-w-md mt-1 mb-6">
            Search genuine academic papers and click &ldquo;Save to Workspace&rdquo; or start by discovering new research.
          </p>
          <Link
            href="/search"
            className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700 transition-colors"
          >
            Explore Literature
          </Link>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
