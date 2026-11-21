import Link from "next/link";
import { createClient } from "@/lib/supabase/server";

export async function SiteHeader() {
  let user = null;
  try {
    const supabase = await createClient();
    const { data } = await supabase.auth.getUser();
    user = data.user;
  } catch {
    // Supabase unconfigured or offline in dev
  }

  return (
    <header className="sticky top-0 z-50 w-full bg-canvas/90 backdrop-blur border-b border-hairline">
      <div className="max-w-6xl mx-auto flex h-14 items-center justify-between px-6">
        {/* Wordmark + Nav */}
        <div className="flex items-center gap-8">
          <Link
            href="/"
            className="font-semibold text-base text-stone tracking-tight flex items-center gap-2"
            style={{ fontFamily: "var(--font-inter), Inter, system-ui, sans-serif" }}
          >
            {/* Small accent dot — stone colored */}
            <span className="w-2 h-2 rounded-full bg-primary inline-block" />
            PaperTrail
          </Link>

          <nav className="hidden md:flex items-center gap-6 text-sm text-stone">
            <Link href="/search" className="hover:text-ink transition-colors">
              Search
            </Link>
            <Link href="/graph" className="hover:text-ink transition-colors">
              Citation Graph
            </Link>
            <Link href="/recommendations" className="hover:text-ink transition-colors">
              Recommendations
            </Link>
            <Link href="/reviews" className="hover:text-ink transition-colors">
              Reviews
            </Link>
            <Link href="/evaluation" className="hover:text-ink transition-colors">
              Eval Lab
            </Link>
          </nav>
        </div>

        {/* Auth Controls */}
        <div className="flex items-center gap-3">
          {user ? (
            <Link
              href="/workspace"
              className="btn-secondary text-xs px-4 py-1.5"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
              Workspace
            </Link>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="text-xs font-medium text-stone hover:text-ink px-3 py-1.5 transition-colors"
              >
                Sign in
              </Link>
              <Link
                href="/register"
                className="btn-primary text-xs px-4 py-1.5"
              >
                Register
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
