"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { Cookie, ShieldCheck, X, Check, SlidersHorizontal, AlertCircle } from "lucide-react";

export interface CookiePreferences {
  necessary: boolean;
  functional: boolean;
  analytics: boolean;
  timestamp: string;
}

const STORAGE_KEY = "carelynx_cookie_consent_v1";

export default function CookieConsent() {
  const [hasDecided, setHasDecided] = useState<boolean | null>(null);
  const [showPreferences, setShowPreferences] = useState(false);
  const [preferences, setPreferences] = useState<CookiePreferences>({
    necessary: true,
    functional: false,
    analytics: false,
    timestamp: "",
  });

  const modalRef = useRef<HTMLDivElement>(null);

  // Load existing preferences on mount
  useEffect(() => {
    setTimeout(() => {
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          const parsed = JSON.parse(stored);
          setPreferences(parsed);
          setHasDecided(true);
        } else {
          setHasDecided(false);
        }
      } catch {
        setHasDecided(false);
      }
    }, 0);
  }, []);

  // Listen for open preferences event from Footer or Cookie Policy page
  useEffect(() => {
    const handleOpen = () => setShowPreferences(true);
    window.addEventListener("carelynx:open-cookie-preferences", handleOpen);
    return () => window.removeEventListener("carelynx:open-cookie-preferences", handleOpen);
  }, []);

  // Handle escape key to close preferences modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && showPreferences) {
        setShowPreferences(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [showPreferences]);

  const saveConsent = useCallback((prefs: CookiePreferences) => {
    const payload: CookiePreferences = {
      ...prefs,
      necessary: true,
      timestamp: new Date().toISOString(),
    };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch (err) {
      console.error("Unable to save cookie consent", err);
    }
    setPreferences(payload);
    setHasDecided(true);
    setShowPreferences(false);

    // Dispatch global event for any dependent tracking scripts
    window.dispatchEvent(
      new CustomEvent("carelynx:consent-updated", { detail: payload })
    );
  }, []);

  const handleAcceptAll = () => {
    saveConsent({
      necessary: true,
      functional: true,
      analytics: true,
      timestamp: "",
    });
  };

  const handleRejectAll = () => {
    saveConsent({
      necessary: true,
      functional: false,
      analytics: false,
      timestamp: "",
    });
  };

  const handleSaveCustom = () => {
    saveConsent(preferences);
  };

  // If loading or already decided and modal is closed, don't render banner
  if (hasDecided === null) return null;

  return (
    <>
      {/* 1. Global Cookie Consent Floating Banner (Visible until decided) */}
      {!hasDecided && (
        <aside
          role="region"
          aria-label="Cookie and Privacy Consent"
          className="fixed bottom-0 inset-x-0 z-50 p-4 sm:p-6 no-print pointer-events-none"
        >
          <div className="mx-auto max-w-5xl bg-white/95 backdrop-blur-md border border-slate-300 shadow-2xl rounded-2xl p-5 sm:p-6 text-slate-900 pointer-events-auto transition-all animate-fadeIn">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center shrink-0 mt-0.5">
                  <Cookie className="w-5 h-5 text-emerald-700" aria-hidden="true" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <h2 className="text-sm sm:text-base font-bold text-slate-900 flex items-center gap-2">
                    <span>Privacy & Cookie Governance</span>
                    <span className="text-[11px] font-semibold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full border border-emerald-200">
                      GDPR & CCPA Compliant
                    </span>
                  </h2>
                  <p className="text-xs sm:text-sm text-slate-600 leading-relaxed max-w-3xl">
                    CARELYNX strictly enforces a <strong>privacy-first, zero-tracking by default</strong> policy. We only store essential technical session data required to process and navigate your discharge documents. Non-essential cookies or analytics are blocked until you grant explicit permission. Review our{" "}
                    <Link
                      href="/cookies"
                      className="text-emerald-700 font-semibold underline underline-offset-2 hover:text-emerald-900 focus-visible:outline-2 focus-visible:outline-emerald-600"
                    >
                      Cookie Policy
                    </Link>{" "}
                    and{" "}
                    <Link
                      href="/privacy"
                      className="text-emerald-700 font-semibold underline underline-offset-2 hover:text-emerald-900 focus-visible:outline-2 focus-visible:outline-emerald-600"
                    >
                      Privacy Policy
                    </Link>.
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap sm:flex-nowrap items-center gap-2.5 w-full md:w-auto shrink-0">
                <button
                  type="button"
                  onClick={handleRejectAll}
                  className="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-100 text-slate-800 font-semibold text-xs sm:text-sm shadow-xs transition-colors cursor-pointer focus-visible:outline-2 focus-visible:outline-emerald-600"
                  id="cookie-btn-reject"
                >
                  Reject All Non-Essential
                </button>
                <button
                  type="button"
                  onClick={() => setShowPreferences(true)}
                  className="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-slate-300 bg-slate-50 hover:bg-slate-100 text-slate-800 font-semibold text-xs sm:text-sm shadow-xs transition-colors flex items-center justify-center gap-1.5 cursor-pointer focus-visible:outline-2 focus-visible:outline-emerald-600"
                  id="cookie-btn-manage"
                >
                  <SlidersHorizontal className="w-3.5 h-3.5" aria-hidden="true" />
                  <span>Preferences</span>
                </button>
                <button
                  type="button"
                  onClick={handleAcceptAll}
                  className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs sm:text-sm shadow-md shadow-emerald-600/20 transition-all cursor-pointer focus-visible:outline-2 focus-visible:outline-emerald-600"
                  id="cookie-btn-accept"
                >
                  Accept All
                </button>
              </div>
            </div>
          </div>
        </aside>
      )}

      {/* 2. Granular Cookie Preferences Modal */}
      {showPreferences && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="cookie-modal-title"
          aria-describedby="cookie-modal-desc"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn"
          onClick={() => setShowPreferences(false)}
        >
          <div
            ref={modalRef}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-2xl bg-white border border-slate-200 rounded-3xl shadow-2xl p-6 sm:p-8 flex flex-col gap-6 text-slate-900 max-h-[92dvh] overflow-y-auto custom-scrollbar"
          >
            {/* Modal Header */}
            <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center shrink-0">
                  <ShieldCheck className="w-5 h-5" aria-hidden="true" />
                </div>
                <div>
                  <h2 id="cookie-modal-title" className="text-lg font-bold text-slate-900">
                    Cookie & Storage Preferences
                  </h2>
                  <p id="cookie-modal-desc" className="text-xs text-slate-500">
                    Control how CARELYNX handles cookies and local browser storage.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowPreferences(false)}
                className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer focus-visible:outline-2 focus-visible:outline-emerald-600"
                aria-label="Close cookie preferences dialog"
              >
                <X className="w-5 h-5" aria-hidden="true" />
              </button>
            </div>

            {/* Cookie Categories */}
            <div className="flex flex-col gap-4">
              {/* Category 1: Strictly Necessary */}
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex flex-col gap-1 pr-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-slate-900">Strictly Necessary Cookies</span>
                    <span className="text-[10px] font-bold uppercase tracking-wider bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full">
                      Always Active
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Essential for secure session handling, CSRF defense, and persisting your language preferences. These cannot be disabled.
                  </p>
                </div>
                <div className="flex items-center shrink-0">
                  <span className="text-xs font-semibold text-emerald-700 flex items-center gap-1">
                    <Check className="w-4 h-4" aria-hidden="true" /> Required
                  </span>
                </div>
              </div>

              {/* Category 2: Functional Cookies */}
              <div className="p-4 rounded-2xl bg-white border border-slate-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex flex-col gap-1 pr-2">
                  <span className="font-bold text-sm text-slate-900">Functional & Document Cache</span>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Permits local caching of encrypted discharge summaries so you do not have to re-upload files during the same active recovery session.
                  </p>
                </div>
                <div className="flex items-center shrink-0">
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={preferences.functional}
                      onChange={(e) =>
                        setPreferences((prev) => ({ ...prev, functional: e.target.checked }))
                      }
                      className="sr-only peer"
                      aria-label="Enable functional and document caching"
                    />
                    <div className="w-11 h-6 bg-slate-200 peer-focus:outline-2 peer-focus:outline-emerald-600 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
                  </label>
                </div>
              </div>

              {/* Category 3: Privacy-Preserving Analytics */}
              <div className="p-4 rounded-2xl bg-white border border-slate-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex flex-col gap-1 pr-2">
                  <span className="font-bold text-sm text-slate-900">Anonymized Technical Diagnostics</span>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Aggregated error logging and UI responsiveness benchmarks without recording any medical, personal, or identifying patient values.
                  </p>
                </div>
                <div className="flex items-center shrink-0">
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={preferences.analytics}
                      onChange={(e) =>
                        setPreferences((prev) => ({ ...prev, analytics: e.target.checked }))
                      }
                      className="sr-only peer"
                      aria-label="Enable anonymized technical diagnostics"
                    />
                    <div className="w-11 h-6 bg-slate-200 peer-focus:outline-2 peer-focus:outline-emerald-600 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
                  </label>
                </div>
              </div>
            </div>

            {/* Notice */}
            <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs">
              <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" aria-hidden="true" />
              <p>
                Under GDPR and HIPAA technical safeguard rules, CARELYNX never sells patient data or utilizes behavioral ad pixels. You may change or revoke these settings at any time from the website footer.
              </p>
            </div>

            {/* Modal Actions */}
            <div className="flex flex-col sm:flex-row items-center justify-end gap-3 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={handleRejectAll}
                className="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs sm:text-sm transition-colors cursor-pointer focus-visible:outline-2 focus-visible:outline-emerald-600"
              >
                Reject All Non-Essential
              </button>
              <button
                type="button"
                onClick={handleSaveCustom}
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs sm:text-sm shadow-md shadow-emerald-600/20 transition-all cursor-pointer focus-visible:outline-2 focus-visible:outline-emerald-600"
              >
                Save My Preferences
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
