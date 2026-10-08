import type { Metadata } from "next";
import Link from "next/link";
import { ShieldCheck, HeartHandshake, AlertTriangle, Sparkles } from "lucide-react";
import "./globals.css";

export const metadata: Metadata = {
  title: "CARELYNX — Clear, Evidence-Linked Discharge Instructions",
  description:
    "Helping patients and caregivers navigate hospital discharge paperwork safely with line-by-line evidence, verified medications, and human review.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-bg text-fg selection:bg-brand-muted selection:text-brand">
        {/* Navigation Bar matching MindWell reference */}
        <header className="border-b border-line/60 bg-white/70 backdrop-blur-md sticky top-0 z-30 shadow-xs">
          <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between" aria-label="Main Navigation">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2.5 font-bold tracking-tight text-slate-900 group" id="nav-home">
              <div className="w-8 h-8 rounded-xl bg-brand text-white flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
                <HeartHandshake className="w-5 h-5 text-white" />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold tracking-tight text-slate-900">CARELYNX</span>
                <span className="hidden sm:inline px-2 py-0.5 rounded-full text-[11px] font-semibold bg-brand-muted text-brand">
                  Discharge Navigator
                </span>
              </div>
            </Link>
            
            {/* Center Navigation Links */}
            <div className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
              <Link href="/" className="hover:text-brand transition-colors">
                AI Fact Extraction
              </Link>
              <Link href="/" className="hover:text-brand transition-colors">
                Care Plan
              </Link>
              <Link href="/" className="hover:text-brand transition-colors">
                Prescriptions
              </Link>
              <Link href="/review" className="hover:text-brand transition-colors">
                Clinical Audit
              </Link>
            </div>

            {/* Right Action Pills */}
            <div className="flex items-center gap-2 sm:gap-3 text-sm">
              <Link 
                href="/review" 
                className="px-3.5 sm:px-4 py-2 rounded-full bg-rose-500 hover:bg-rose-600 active:bg-rose-700 text-white font-semibold text-xs sm:text-sm flex items-center gap-1.5 shadow-sm shadow-rose-500/20 transition-all"
                id="nav-emergency"
              >
                <AlertTriangle className="w-4 h-4" />
                <span>Review Alert</span>
              </Link>
              <Link 
                href="/" 
                className="px-4 sm:px-5 py-2 rounded-full bg-brand hover:bg-brand-light text-white font-semibold text-xs sm:text-sm flex items-center gap-1.5 shadow-sm shadow-emerald-500/20 transition-all"
                id="nav-get-started"
              >
                <Sparkles className="w-4 h-4" />
                <span>Upload Paperwork</span>
              </Link>
            </div>
          </nav>
        </header>

        <main className="flex-1 flex flex-col">{children}</main>

        <footer className="border-t border-slate-200/80 bg-white/60 text-xs text-slate-600 py-6 no-print">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row justify-between items-center gap-4 text-center sm:text-left">
            <div className="flex items-center gap-2 text-slate-700">
              <ShieldCheck className="w-4 h-4 text-brand shrink-0" />
              <p>
                <strong className="text-slate-900">CARELYNX Verbatim Evidence Policy:</strong> All facts are anchored directly to original paperwork sentences.
              </p>
            </div>
            <p className="text-slate-600 font-medium text-[11px] shrink-0">
              Non-diagnostic navigation tool • Always verify with your clinical team
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}

