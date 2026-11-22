"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") || "/workspace";

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const supabase = createClient();
    const { error: authError } = await supabase.auth.signInWithPassword({ email, password });

    if (authError) {
      setError(authError.message);
      setLoading(false);
    } else {
      router.push(next as any);
      router.refresh();
    }
  }

  return (
    <div className="card shadow-elevated px-8 py-8">
      <form className="space-y-5" onSubmit={handleLogin}>
        {error && (
          <div className="p-3 text-xs bg-surface border border-error/30 text-error rounded-md">
            {error}
          </div>
        )}

        <div>
          <label className="block text-xs font-medium text-stone mb-1.5">Email address</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input-field"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-stone mb-1.5">Password</label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input-field"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="btn-primary w-full"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-canvas flex flex-col justify-center py-16 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-8">
        <Link href="/" className="inline-flex items-center gap-2 text-base font-semibold text-stone mb-4">
          <span className="w-2 h-2 rounded-full bg-primary inline-block" />
          PaperTrail
        </Link>
        <h2
          className="text-3xl font-light text-ink"
          style={{ fontFamily: "var(--font-fraunces), Fraunces, Georgia, serif" }}
        >
          Sign in to your account
        </h2>
        <p className="mt-2 text-xs text-ash">
          Or{" "}
          <Link href="/register" className="font-medium text-primary hover:opacity-80">
            create a new account
          </Link>
        </p>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Suspense fallback={<div className="card text-center py-10 text-xs text-ash">Loading login form...</div>}>
          <LoginForm />
        </Suspense>
      </div>
    </div>
  );
}
