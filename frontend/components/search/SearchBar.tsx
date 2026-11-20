"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export function SearchBar({ initialQuery = "", placeholder = "Search papers by keyword, concept, title, or DOI..." }: { initialQuery?: string; placeholder?: string }) {
  const [query, setQuery] = useState(initialQuery);
  const router = useRouter();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = query.trim();
    if (trimmed.length >= 2) {
      router.push(`/search?q=${encodeURIComponent(trimmed)}`);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <div className="relative flex items-center shadow-sm rounded-lg overflow-hidden border border-stone-300 focus-within:border-indigo-600 focus-within:ring-2 focus-within:ring-indigo-100 transition-all bg-white">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className="w-full py-3.5 pl-4 pr-24 text-sm text-stone-900 bg-transparent placeholder-stone-400 focus:outline-none"
        />
        <button
          type="submit"
          className="absolute right-2 px-4 py-2 text-xs font-medium rounded-md bg-indigo-600 text-white hover:bg-indigo-700 transition-colors shadow-sm"
        >
          Search
        </button>
      </div>
    </form>
  );
}
