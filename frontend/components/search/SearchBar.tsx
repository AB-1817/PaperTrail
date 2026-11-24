"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export function SearchBar({
  initialQuery = "",
  placeholder = "Search papers by keyword, concept, title, or DOI...",
}: {
  initialQuery?: string;
  placeholder?: string;
}) {
  const [query, setQuery] = useState(initialQuery);
  const router = useRouter();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = query.trim();
    if (trimmed.length > 0) {
      router.push(`/search?q=${encodeURIComponent(trimmed)}`);
    } else {
      router.push("/search");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <div
        className="relative flex items-center rounded-md overflow-hidden border border-hairline bg-surface shadow-card focus-within:ring-2 transition-all"
        style={{ outlineColor: "var(--color-primary)" }}
      >
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className="w-full py-3.5 pl-4 pr-28 text-sm text-ink bg-transparent placeholder-ash focus:outline-none"
        />
        <button
          type="submit"
          className="absolute right-2 btn-primary text-xs px-5 py-2"
        >
          Search
        </button>
      </div>
    </form>
  );
}
