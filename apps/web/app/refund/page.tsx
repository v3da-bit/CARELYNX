import Link from "next/link";
import Image from "next/image";
import { ShieldCheck, ArrowLeft, HeartHandshake, CheckCircle2, FileText, Mail, Phone } from "lucide-react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Refund Policy & Honest Pricing Standards — CARELYNX",
  description: "Transparent pricing covenants, cancellation rights, and consumer protection guarantees on CARELYNX.",
};

export default function RefundPolicyPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-12 flex flex-col gap-8 text-slate-800">
      {/* Top Breadcrumb / Back Link */}
      <div className="flex items-center justify-between">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700 hover:text-emerald-900 transition-colors focus-visible:outline-2 focus-visible:outline-emerald-600 rounded"
        >
          <ArrowLeft className="w-4 h-4" aria-hidden="true" />
          <span>Back to Care Navigator</span>
        </Link>
        <span className="text-xs font-mono text-slate-500">
          Last Updated: October 12, 2026 • Version 1.2
        </span>
      </div>

      {/* Header Banner */}
      <header className="bg-white/90 backdrop-blur-md border border-slate-200 rounded-3xl p-8 shadow-xs flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-white border border-slate-200/80 p-1.5 flex items-center justify-center shrink-0 shadow-xs overflow-hidden">
            <Image
              src="/carelynx-icon.png"
              alt="CARELYNX Logo"
              width={38}
              height={38}
              className="w-full h-full object-contain"
            />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Refund Policy & Transparent Billing Covenant
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 mt-1">
              Ethical consumer protection, anti-dark patterns, and fair cancellation guarantees
            </p>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-emerald-50/70 border border-emerald-200 text-emerald-950 text-xs sm:text-sm leading-relaxed flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-emerald-700 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <strong>Anti-Dark Pattern Promise:</strong> CARELYNX believes healthcare software should be honest and transparent. We never use pre-checked checkboxes, countdown traps, deceptive renewal loops, or hidden handling fees. What you see is what you get.
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="bg-white/90 backdrop-blur-md border border-slate-200 rounded-3xl p-8 sm:p-10 shadow-xs flex flex-col gap-10 leading-relaxed text-sm text-slate-700">
        
        {/* Section 1: Patient Tier */}
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-700" aria-hidden="true" />
            <span>1. Free Patient & Caregiver Access Tier</span>
          </h2>
          <p>
            CARELYNX provides core discharge paperwork navigation, medication timeline extraction, verbatim evidence inspection, and multilingual translations (English, Hindi, Gujarati) free of predatory paywalls for individual patients and their primary family caregivers.
          </p>
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700">
            Patients are never subjected to surprise fees, required credit card entry, or hidden recurring memberships for processing their standard discharge documents.
          </div>
        </section>

        {/* Section 2: Hospital & Enterprise Reviewer Licenses */}
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <FileText className="w-4 h-4 text-emerald-700" aria-hidden="true" />
            <span>2. Hospital Enterprise & Reviewer Subscriptions</span>
          </h2>
          <p>
            Institutional clinical reviewer seats (used by hospital discharge coordinators and hospital audit teams accessing <code>/review</code>) are billed on a fixed, transparent enterprise agreement.
          </p>
          <ul className="list-disc pl-5 space-y-1 text-xs">
            <li><strong>Upfront Fee Quotations:</strong> All enterprise rates, server compute provisioning fees, and local AMD ROCm deployment costs are quoted upfront in formal written statements of work.</li>
            <li><strong>No Automatic Conversion Traps:</strong> Free clinical evaluation pilots never roll over into paid contracts without explicit, counter-signed administrative approval.</li>
          </ul>
        </section>

        {/* Section 3: 14-Day Statutory Refund Right */}
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-700" aria-hidden="true" />
            <span>3. 14-Day Statutory Cancellation & Refund Guarantee</span>
          </h2>
          <p>
            In compliance with the EU Consumer Rights Directive (2011/83/EU) and statutory fair trade protections:
          </p>
          <ul className="list-disc pl-5 space-y-2 text-xs">
            <li>
              Any institutional or premium reviewer subscription may be canceled within <strong>14 calendar days</strong> of purchase for a <strong>100% full refund</strong>, no justification required.
            </li>
            <li>
              Refunds are processed back to the original method of payment within 5 to 7 business days of written cancellation notice.
            </li>
            <li>
              No hidden cancellation penalties, retention fees, or complex phone-call cancellation obstacle courses.
            </li>
          </ul>
        </section>

        {/* Section 4: Dispute Resolution & Direct Contact */}
        <section className="flex flex-col gap-3 border-t border-slate-100 pt-6">
          <h2 className="text-lg font-bold text-slate-900">4. Dispute Resolution & Customer Support</h2>
          <p>
            If you encounter any billing discrepancy, unauthorized charge, or service dissatisfaction, our billing team is available for immediate resolution:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-2">
            <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 flex items-center gap-2.5">
              <Mail className="w-4 h-4 text-emerald-700 shrink-0" aria-hidden="true" />
              <div>
                <span className="block font-bold text-slate-900">Email Inquiries:</span>
                <a href="mailto:billing@carelynx.local" className="text-emerald-700 underline font-medium">
                  billing@carelynx.local
                </a>
              </div>
            </div>
            <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 flex items-center gap-2.5">
              <Phone className="w-4 h-4 text-emerald-700 shrink-0" aria-hidden="true" />
              <div>
                <span className="block font-bold text-slate-900">24/7 Patient Helpline:</span>
                <span className="font-mono text-slate-800 font-semibold">1800-CARELYNX</span>
              </div>
            </div>
          </div>
        </section>

      </main>
    </div>
  );
}
