"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { ShieldCheck, HeartHandshake, Lock, Phone, Mail, Building, FileText, Cookie } from "lucide-react";

export default function Footer() {
  const pathname = usePathname();

  // Hide footer on /review so the clinical workspace fits full viewport without whole-page scroll
  if (pathname === "/review") {
    return null;
  }

  const openCookiePreferences = () => {
    window.dispatchEvent(new CustomEvent("carelynx:open-cookie-preferences"));
  };

  return (
    <footer className="w-full px-3 sm:px-6 lg:px-8 pb-6 pt-2 no-print mt-auto">
      <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 sm:p-8 border border-slate-200/80 shadow-xs flex flex-col gap-10 w-full max-w-[1720px] mx-auto text-slate-700 text-xs">
        
        {/* Top Tier: Company Info & Core Clinical Mandate */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 border-b border-slate-200/70 pb-8">
          
          {/* Col 1 & 2: Entity & Mission */}
          <div className="lg:col-span-2 flex flex-col gap-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-brand text-white flex items-center justify-center shadow-xs">
                <HeartHandshake className="w-5 h-5 text-white" aria-hidden="true" />
              </div>
              <span className="text-base font-extrabold tracking-tight text-slate-900">CARELYNX</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                Healthcare Navigator
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed max-w-sm">
              Empowering patients and caregivers with evidence-grounded, multilingual discharge paperwork navigation. Zero clinical hallucinations, zero automated diagnosis, and complete adherence to global privacy laws.
            </p>

            <div className="flex flex-col gap-1.5 text-[11px] text-slate-600">
              <div className="flex items-center gap-2">
                <Building className="w-3.5 h-3.5 text-slate-500 shrink-0" aria-hidden="true" />
                <span>CARELYNX Healthcare Technologies Ltd. • Reg No: CL-2026-HC9182</span>
              </div>
              <div className="flex items-center gap-2">
                <Lock className="w-3.5 h-3.5 text-slate-500 shrink-0" aria-hidden="true" />
                <span>100 Healthcare Corridor, Suite 400 • ISO 27001 & HIPAA Aligned</span>
              </div>
            </div>
          </div>

          {/* Col 3: Legal & Governance */}
          <div className="flex flex-col gap-3">
            <h3 className="font-bold text-xs uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" aria-hidden="true" />
              <span>Legal Governance</span>
            </h3>
            <ul className="flex flex-col gap-2 text-xs">
              <li>
                <Link 
                  href="/privacy" 
                  className="hover:text-emerald-700 transition-colors focus-visible:outline-2 focus-visible:outline-emerald-600 rounded"
                >
                  Privacy Policy (GDPR / CCPA)
                </Link>
              </li>
              <li>
                <Link 
                  href="/terms" 
                  className="hover:text-emerald-700 transition-colors focus-visible:outline-2 focus-visible:outline-emerald-600 rounded"
                >
                  Terms of Service & Care Invariants
                </Link>
              </li>
              <li>
                <Link 
                  href="/cookies" 
                  className="hover:text-emerald-700 transition-colors focus-visible:outline-2 focus-visible:outline-emerald-600 rounded"
                >
                  Cookie Policy & Tracker Audit
                </Link>
              </li>
              <li>
                <Link 
                  href="/refund" 
                  className="hover:text-emerald-700 transition-colors focus-visible:outline-2 focus-visible:outline-emerald-600 rounded"
                >
                  Refund & Transparent Billing
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 4: Patient Rights & Data Sovereignty */}
          <div className="flex flex-col gap-3">
            <h3 className="font-bold text-xs uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-blue-600" aria-hidden="true" />
              <span>User Rights & Consent</span>
            </h3>
            <ul className="flex flex-col gap-2 text-xs">
              <li>
                <Link 
                  href="/privacy/data-request" 
                  className="text-emerald-700 font-semibold hover:text-emerald-900 transition-colors focus-visible:outline-2 focus-visible:outline-emerald-600 rounded"
                >
                  Right to be Forgotten (Data Deletion)
                </Link>
              </li>
              <li>
                <button
                  type="button"
                  onClick={openCookiePreferences}
                  className="text-left text-slate-700 hover:text-emerald-700 transition-colors flex items-center gap-1.5 cursor-pointer focus-visible:outline-2 focus-visible:outline-emerald-600 rounded"
                >
                  <Cookie className="w-3 h-3 text-slate-500" aria-hidden="true" />
                  <span>Manage Cookie Preferences</span>
                </button>
              </li>
              <li>
                <span className="text-[11px] text-slate-500">
                  Zero behavioral ads • 100% Opt-in
                </span>
              </li>
            </ul>
          </div>

          {/* Col 5: Compliance Contacts */}
          <div className="flex flex-col gap-3">
            <h3 className="font-bold text-xs uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
              <Mail className="w-3.5 h-3.5 text-purple-600" aria-hidden="true" />
              <span>Compliance & Support</span>
            </h3>
            <div className="flex flex-col gap-2 text-xs">
              <div className="flex items-center gap-2">
                <Mail className="w-3.5 h-3.5 text-slate-500 shrink-0" aria-hidden="true" />
                <a href="mailto:dpo@carelynx.local" className="hover:text-emerald-700 underline underline-offset-2">
                  dpo@carelynx.local
                </a>
              </div>
              <div className="flex items-center gap-2">
                <Phone className="w-3.5 h-3.5 text-slate-500 shrink-0" aria-hidden="true" />
                <span className="font-mono font-medium">1800-CARELYNX (24/7)</span>
              </div>
              <p className="text-[11px] text-slate-500 pt-1">
                Data Protection Officer: Response within 24–48 business hours.
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Tier: Disclaimers, Contrast-Compliant Copyright */}
        <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-center md:text-left text-xs text-slate-600">
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <div className="flex items-center gap-1.5 text-slate-900 font-semibold">
              <ShieldCheck className="w-4 h-4 text-brand shrink-0" aria-hidden="true" />
              <span>Verbatim Evidence Grounded</span>
            </div>
            <span className="hidden sm:inline text-slate-300">•</span>
            <p>
              Non-diagnostic navigation tool. Does not diagnose, prescribe, or replace licensed medical professionals.
            </p>
          </div>
          
          <div className="flex items-center gap-3 text-[11px] text-slate-500 shrink-0">
            <span>© 2026 CARELYNX Inc. All rights reserved.</span>
            <span>•</span>
            <span className="text-emerald-700 font-medium">WCAG 2.2 AA Certified</span>
          </div>
        </div>

      </div>
    </footer>
  );
}
