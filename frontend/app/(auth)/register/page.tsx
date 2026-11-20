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
    const { error: authError } = await supabase.auth.signUp({
      email,
      password,
    });

    if (authError) {
      setError(authError.message);
      setLoading(false);
    } else {
      setSuccess(true);
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-stone-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <Link href="/" className="inline-flex items-center gap-2 text-xl font-semibold text-stone-900 mb-2">
          <span className="w-2.5 h-2.5 rounded-full bg-indigo-600 inline-block" />
          PaperTrail
        </Link>
        <h2 className="text-2xl font-bold tracking-tight text-stone-900">Create an account</h2>
        <p className="mt-2 text-xs text-stone-500">
          Already have an account?{" "}
          <Link href="/auth/login" className="font-medium text-indigo-600 hover:text-indigo-500">
            Sign in
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm border border-stone-200 rounded-xl sm:px-10">
          {success ? (
            <div className="p-4 text-center bg-emerald-50 border border-emerald-200 rounded-lg">
              <h3 className="text-sm font-semibold text-emerald-800">Account created</h3>
              <p className="mt-1 text-xs text-emerald-600">
                Check your inbox to verify your email, or{" "}
                <Link href="/auth/login" className="font-medium underline">
                  sign in right now
                </Link>
                .
              </p>
            </div>
          ) : (
            <form className="space-y-4" onSubmit={handleRegister}>
              {error && (
                <div className="p-3 text-xs bg-red-50 border border-red-200 text-red-700 rounded-md">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-stone-700 mb-1">Email address</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-100 focus:border-indigo-600"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-stone-700 mb-1">Password</label>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-100 focus:border-indigo-600"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 px-4 text-xs font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 focus:outline-none transition-colors disabled:opacity-50"
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
