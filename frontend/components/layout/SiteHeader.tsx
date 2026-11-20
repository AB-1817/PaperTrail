import Link from "next/link";
import { createClient } from "@/lib/supabase/server";

export async function SiteHeader() {
  let user = null;
  try {
    const supabase = await createClient();
    const { data } = await supabase.auth.getUser();
    user = data.user;
  } catch {
    // If Supabase is unconfigured or offline in dev
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b border-stone-200 bg-stone-50/90 backdrop-blur">
      <div className="max-w-6xl mx-auto flex h-14 items-center justify-between px-6">
        <div className="flex items-center gap-8">
          <Link href="/" className="font-semibold text-lg text-stone-900 tracking-tight flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-600 inline-block" />
            PaperTrail
          </Link>
          <nav className="hidden md:flex items-center gap-6 text-sm text-stone-600">
            <Link href="/search" className="hover:text-stone-900 transition-colors">
              Search
            </Link>
            <Link href="/graph" className="hover:text-stone-900 transition-colors">
              Citation Graph
            </Link>
            <Link href="/recommendations" className="hover:text-stone-900 transition-colors">
              Recommendations
            </Link>
            <Link href="/reviews" className="hover:text-stone-900 transition-colors">
              Reviews
            </Link>
            <Link href="/evaluation" className="hover:text-stone-900 transition-colors">
              Eval Lab
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {user ? (
            <Link
              href="/workspace"
              className="text-xs font-medium px-3 py-1.5 rounded-md bg-stone-900 text-white hover:bg-stone-800 transition-colors flex items-center gap-2"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              Workspace
            </Link>
          ) : (
            <div className="flex items-center gap-2 text-xs font-medium">
              <Link
                href="/auth/login"
                className="px-3 py-1.5 rounded-md text-stone-600 hover:text-stone-900 transition-colors"
              >
                Sign in
              </Link>
              <Link
                href="/auth/register"
                className="px-3 py-1.5 rounded-md bg-indigo-600 text-white hover:bg-indigo-700 transition-colors"
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
