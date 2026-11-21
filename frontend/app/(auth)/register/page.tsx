"use client";

import { useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const supabase = createClient();
    const { error: authError } = await supabase.auth.signUp({ email, password });

    if (authError) {
      setError(authError.message);
      setLoading(false);
    } else {
      setSuccess(true);
      setLoading(false);
    }
  }

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
          Create an account
        </h2>
        <p className="mt-2 text-xs text-ash">
          Already have one?{" "}
          <Link href="/login" className="font-medium text-primary hover:opacity-80">
            Sign in
          </Link>
        </p>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="card shadow-elevated px-8 py-8">
          {success ? (
            <div className="p-5 text-center bg-canvas border border-sage-pale rounded-lg">
              <h3 className="text-sm font-semibold text-olive mb-1">Account created</h3>
              <p className="text-xs text-ash">
                Check your inbox to verify your email, or{" "}
                <Link href="/login" className="font-medium text-primary underline">
                  sign in right now
                </Link>
                .
              </p>
            </div>
          ) : (
            <form className="space-y-5" onSubmit={handleRegister}>
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
                  minLength={8}
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
                {loading ? "Creating account..." : "Register"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
