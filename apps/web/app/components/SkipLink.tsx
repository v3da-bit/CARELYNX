"use client";

export default function SkipLink() {
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2.5 focus:bg-slate-900 focus:text-white focus:font-semibold focus:rounded-lg focus:shadow-lg focus:outline-2 focus:outline-emerald-500 focus:outline-offset-2"
    >
      Skip to main content
    </a>
  );
}
