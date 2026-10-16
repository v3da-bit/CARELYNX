"use client";

import Link from "next/link";
import { Cookie, ShieldCheck, ArrowLeft, SlidersHorizontal, CheckCircle2, Lock } from "lucide-react";

export default function CookiePolicyPage() {
  const openPreferences = () => {
    window.dispatchEvent(new CustomEvent("carelynx:open-cookie-preferences"));
  };

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-12 flex flex-col gap-8 text-slate-800">
      {/* Top Breadcrumb / Back Link */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700 hover:text-emerald-900 transition-colors focus-visible:outline-2 focus-visible:outline-emerald-600 rounded"
        >
          <ArrowLeft className="w-4 h-4" aria-hidden="true" />
          <span>Back to Care Navigator</span>
        </Link>
        <span className="text-xs font-mono text-slate-500">
          Last Updated: October 12, 2026 • Version 2.0
        </span>
      </div>

      {/* Header Banner */}
      <header className="bg-white/90 backdrop-blur-md border border-slate-200 rounded-3xl p-8 shadow-xs flex flex-col gap-5">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-amber-100 text-amber-800 flex items-center justify-center shrink-0">
              <Cookie className="w-6 h-6" aria-hidden="true" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                Cookie Policy & Tracking Technologies Audit
              </h1>
              <p className="text-xs sm:text-sm text-slate-600 mt-1">
                Transparent disclosure under EU ePrivacy Directive, GDPR, and California CPRA
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={openPreferences}
            className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs sm:text-sm shadow-md shadow-emerald-600/20 transition-all flex items-center gap-2 cursor-pointer focus-visible:outline-2 focus-visible:outline-emerald-600"
          >
            <SlidersHorizontal className="w-4 h-4" aria-hidden="true" />
            <span>Customize Cookie Preferences</span>
          </button>
        </div>

        <div className="p-4 rounded-2xl bg-emerald-50/70 border border-emerald-200 text-emerald-950 text-xs sm:text-sm leading-relaxed flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-emerald-700 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <strong>100% Privacy by Default:</strong> CARELYNX blocks all non-essential cookies and tracking scripts prior to obtaining your informed, active opt-in. We do not use third-party advertising cookies, cross-site trackers, or behavioral profiling pixels.
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="bg-white/90 backdrop-blur-md border border-slate-200 rounded-3xl p-8 sm:p-10 shadow-xs flex flex-col gap-10 leading-relaxed text-sm text-slate-700">
        
        {/* Section 1: Overview */}
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-slate-900">1. What Are Cookies & Local Storage?</h2>
          <p>
            Cookies and browser local storage are small data files saved directly within your browser cache. They allow web platforms to remember your session states, prevent repetitive logins, and preserve active preferences such as your language choice.
          </p>
        </section>

        {/* Section 2: Complete Cookie Inventory */}
        <section className="flex flex-col gap-4">
          <h2 className="text-lg font-bold text-slate-900">2. Complete Cookie & Local Storage Inventory</h2>
          <p>
            Below is the exhaustive, transparent list of every storage token utilized by the CARELYNX platform:
          </p>

          <div className="overflow-x-auto border border-slate-200 rounded-2xl">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-100 text-slate-900 border-b border-slate-200 uppercase font-mono tracking-wider">
                <tr>
                  <th className="p-3 font-bold">Storage Key / Cookie</th>
                  <th className="p-3 font-bold">Category</th>
                  <th className="p-3 font-bold">Purpose</th>
                  <th className="p-3 font-bold">Lifespan</th>
                  <th className="p-3 font-bold">Party</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                <tr>
                  <td className="p-3 font-mono font-semibold text-slate-900">carelynx_cookie_consent_v1</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-800 border border-slate-200">
                      Strictly Necessary
                    </span>
                  </td>
                  <td className="p-3 text-slate-600">
                    Stores your active cookie choices so the consent banner is not shown repeatedly.
                  </td>
                  <td className="p-3 font-mono text-slate-600">12 Months</td>
                  <td className="p-3 font-semibold text-emerald-700">1st Party</td>
                </tr>

                <tr>
                  <td className="p-3 font-mono font-semibold text-slate-900">carelynx_lang</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
                      Functional
                    </span>
                  </td>
                  <td className="p-3 text-slate-600">
                    Remembers your preferred language selection (English, Hindi, or Gujarati).
                  </td>
                  <td className="p-3 font-mono text-slate-600">Persistent</td>
                  <td className="p-3 font-semibold text-emerald-700">1st Party</td>
                </tr>

                <tr>
                  <td className="p-3 font-mono font-semibold text-slate-900">carelynx_active_case</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-800 border border-slate-200">
                      Strictly Necessary
                    </span>
                  </td>
                  <td className="p-3 text-slate-600">
                    Maintains your active encounter UUID during processing so a page reload does not discard your care plan.
                  </td>
                  <td className="p-3 font-mono text-slate-600">Session (Cleared on tab close)</td>
                  <td className="p-3 font-semibold text-emerald-700">1st Party</td>
                </tr>

                <tr>
                  <td className="p-3 font-mono font-semibold text-slate-900">carelynx_diag_telemetry</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-800 border border-purple-200">
                      Analytics (Opt-in)
                    </span>
                  </td>
                  <td className="p-3 text-slate-600">
                    Anonymized UI latency measurements (strictly disabled unless explicitly activated in preferences).
                  </td>
                  <td className="p-3 font-mono text-slate-600">30 Days</td>
                  <td className="p-3 font-semibold text-emerald-700">1st Party</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Section 3: Third Party Tracker Audit */}
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Lock className="w-4 h-4 text-emerald-700" aria-hidden="true" />
            <span>3. Third-Party Tracker & Pixel Audit</span>
          </h2>
          <p>
            CARELYNX underwent a strict architectural privacy audit:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
            <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/50 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" aria-hidden="true" />
              <div>
                <strong className="block text-slate-900">Zero Meta (Facebook) Pixels</strong>
                No social tracking beacons or conversion trackers installed.
              </div>
            </div>
            <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/50 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" aria-hidden="true" />
              <div>
                <strong className="block text-slate-900">Zero Google Analytics Beacons</strong>
                No advertising identifiers or third-party demographic profiling.
              </div>
            </div>
            <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/50 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" aria-hidden="true" />
              <div>
                <strong className="block text-slate-900">Local Zero-Network Typography</strong>
                Zero external font CDNs; all glyphs render from local system font stacks.
              </div>
            </div>
            <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/50 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" aria-hidden="true" />
              <div>
                <strong className="block text-slate-900">Zero Ad Exchange Retargeting</strong>
                No cookies are exchanged with data brokers or marketing networks.
              </div>
            </div>
          </div>
        </section>

        {/* Section 4: Browser Management */}
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-slate-900">4. How to Clear or Disable Cookies in Your Browser</h2>
          <p>
            You can configure your browser to reject all cookies or clear existing records at any time:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-xs">
            <li><strong>Google Chrome:</strong> Settings → Privacy and Security → Third-party cookies → Clear browsing data.</li>
            <li><strong>Mozilla Firefox:</strong> Settings → Privacy & Security → Cookies and Site Data → Clear Data.</li>
            <li><strong>Apple Safari:</strong> Settings → Safari → Advanced → Block All Cookies & Website Data.</li>
            <li><strong>Microsoft Edge:</strong> Settings → Cookies and site permissions → Manage and delete cookies and site data.</li>
          </ul>
        </section>

        {/* Section 5: Rights Link */}
        <section className="flex flex-col gap-3 border-t border-slate-100 pt-6">
          <p className="text-xs text-slate-600">
            For instructions on purging all uploaded encounter documentation, visit the{" "}
            <Link href="/privacy/data-request" className="text-emerald-700 underline font-semibold">
              Right to be Forgotten & Data Deletion Portal
            </Link>.
          </p>
        </section>

      </main>
    </div>
  );
}
