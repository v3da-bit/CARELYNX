import Link from "next/link";
import { ShieldCheck, FileText, AlertTriangle, ArrowLeft, Scale, CheckCircle } from "lucide-react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service & Medical Disclaimer — CARELYNX",
  description: "Terms governing use of CARELYNX discharge paperwork navigation, verbatim evidence policies, and clinical disclaimers.",
};

export default function TermsPage() {
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
          Last Updated: October 12, 2026 • Version 2.1
        </span>
      </div>

      {/* Header Banner */}
      <header className="bg-white/90 backdrop-blur-md border border-slate-200 rounded-3xl p-8 shadow-xs flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-blue-100 text-blue-800 flex items-center justify-center shrink-0">
            <Scale className="w-6 h-6" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Terms of Service & Clinical Boundary Invariants
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 mt-1">
              Legal agreements, non-diagnostic boundaries, and honest consumer protection covenants
            </p>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-amber-50/80 border border-amber-200 text-amber-950 text-xs sm:text-sm leading-relaxed flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <strong className="font-bold">CRITICAL MEDICAL DISCLAIMER:</strong> CARELYNX is an assistive information organization tool designed to make hospital discharge papers easier to read and navigate. CARELYNX does <strong>NOT</strong> provide medical diagnosis, initiate therapy, or modify medication doses. Always follow the direct verbal and written instructions of your treating physician. If you experience an emergency, call emergency services immediately (911 / 112 / 108).
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="bg-white/90 backdrop-blur-md border border-slate-200 rounded-3xl p-8 sm:p-10 shadow-xs flex flex-col gap-10 leading-relaxed text-sm text-slate-700">
        
        {/* Section 1: Acceptance & Eligibility */}
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-700" aria-hidden="true" />
            <span>1. Acceptance of Terms & User Eligibility</span>
          </h2>
          <p>
            By accessing or uploading documents to CARELYNX (&quot;Platform&quot;), you acknowledge that you have read, understood, and agree to be bound by these Terms of Service. You affirm that you are at least 18 years of age, or possess legal guardian authority to manage paperwork on behalf of an eligible dependent.
          </p>
        </section>

        {/* Section 2: Non-Diagnostic Mandate */}
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-700" aria-hidden="true" />
            <span>2. Strict Safety Boundaries & Non-Goals</span>
          </h2>
          <p>
            CARELYNX operates under immutable clinical safety invariants defined in our system governance:
          </p>
          <ul className="list-disc pl-5 space-y-2">
            <li>
              <strong>No Autonomous Medical Decisions:</strong> The Platform never interprets laboratory test anomalies or clinical findings as disease diagnoses.
            </li>
            <li>
              <strong>Zero Dose Modification:</strong> Medication names, dosages, intake schedules, and frequencies are extracted verbatim as documented. The system never adjusts or suggests alternative regimens.
            </li>
            <li>
              <strong>Conflict Escalation:</strong> When discrepancies occur across separate discharge papers (e.g., differing follow-up dates), CARELYNX never arbitrarily picks a winner. Discrepancies are flagged as <code>CONFLICT_DETECTED</code> and held for human clinical review.
            </li>
          </ul>
        </section>

        {/* Section 3: Anti-Dark Patterns & Consumer Protection */}
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Scale className="w-4 h-4 text-emerald-700" aria-hidden="true" />
            <span>3. Honest UI Covenants (Anti-Dark Patterns)</span>
          </h2>
          <p>
            We adhere strictly to ethical design standards and consumer protection regulations:
          </p>
          <ul className="list-disc pl-5 space-y-2">
            <li>
              <strong>No Sneak-In Items or Hidden Fees:</strong> Patient care plan navigation is provided transparently with zero concealed recurring subscription traps.
            </li>
            <li>
              <strong>No Pre-Selected Marketing Consents:</strong> All data consent checkboxes are un-checked by default. You retain full autonomy over your choices.
            </li>
            <li>
              <strong>Easy Opt-Out & Deletion:</strong> You can purge your encounters and browser storage in a single click via our{" "}
              <Link href="/privacy/data-request" className="text-emerald-700 underline font-semibold">
                Data Deletion Portal
              </Link>.
            </li>
          </ul>
        </section>

        {/* Section 4: Acceptable Use */}
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <FileText className="w-4 h-4 text-emerald-700" aria-hidden="true" />
            <span>4. Acceptable Use & Document Ownership</span>
          </h2>
          <p>
            You agree only to submit documents for which you have lawful ownership or explicit consent (such as being the named patient, parent, or designated healthcare proxy). You agree not to upload malicious payloads, executable files, or counterfeit medical credentials.
          </p>
        </section>

        {/* Section 5: Intellectual Property */}
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-700" aria-hidden="true" />
            <span>5. Intellectual Property & Verbatim Citations</span>
          </h2>
          <p>
            The software, user interface design, styling, and deterministic safety algorithms of CARELYNX are the property of CARELYNX Healthcare Technologies Ltd. All clinical discharge excerpts cited in the Verbatim Evidence Drawer remain the underlying property of the issuing medical facility and the patient.
          </p>
        </section>

        {/* Section 6: Limitation of Liability */}
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-700" aria-hidden="true" />
            <span>6. Limitation of Liability</span>
          </h2>
          <p>
            To the maximum extent permitted by applicable law, CARELYNX and its developers shall not be liable for any direct, indirect, incidental, or consequential damages resulting from delays, misinterpretations, or errors in source paperwork provided by third-party hospital systems. Always cross-examine printed physical discharge sheets before taking any clinical action.
          </p>
        </section>

        {/* Section 7: Governing Law */}
        <section className="flex flex-col gap-3 border-t border-slate-100 pt-6">
          <h2 className="text-lg font-bold text-slate-900">7. Governing Law & Dispute Resolution</h2>
          <p>
            These Terms are governed by and construed in accordance with applicable consumer protection and healthcare privacy statutes. Any controversies shall be subject to amicable conciliation or binding arbitration.
          </p>
          <p className="text-xs text-slate-500 pt-2">
            For legal inquiries: <a href="mailto:compliance@carelynx.local" className="text-emerald-700 underline font-semibold">compliance@carelynx.local</a>
          </p>
        </section>

      </main>
    </div>
  );
}
