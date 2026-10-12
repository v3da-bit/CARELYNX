import Link from "next/link";
import { ShieldCheck, Lock, FileText, UserCheck, AlertCircle, ArrowLeft, Building, Mail } from "lucide-react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy & Data Governance — CARELYNX",
  description: "Comprehensive GDPR, CCPA/CPRA, and healthcare privacy notice governing discharge paperwork navigation on CARELYNX.",
};

export default function PrivacyPage() {
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
          Last Updated: October 12, 2026 • Version 2.2
        </span>
      </div>

      {/* Header Banner */}
      <header className="bg-white/90 backdrop-blur-md border border-slate-200 rounded-3xl p-8 shadow-xs flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-800 flex items-center justify-center shrink-0">
            <Lock className="w-6 h-6" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Privacy Policy & Health Data Governance
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 mt-1">
              GDPR (EU/UK), CCPA/CPRA (California), and HIPAA Security Invariant Disclosures
            </p>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-emerald-50/70 border border-emerald-200/80 text-emerald-900 text-xs sm:text-sm leading-relaxed flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-emerald-700 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <strong className="font-bold">Core Privacy Principle:</strong> CARELYNX processes medical discharge paperwork exclusively to empower patients and caregivers. We enforce strict data minimization, store documents in private isolated storage, never sell personal information, and never use patient clinical documents to train public commercial AI models.
          </div>
        </div>
      </header>

      {/* Main Legal Content */}
      <main className="bg-white/90 backdrop-blur-md border border-slate-200 rounded-3xl p-8 sm:p-10 shadow-xs flex flex-col gap-10 leading-relaxed text-sm text-slate-700">
        
        {/* Section 1: Data Controller & Contact */}
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Building className="w-4 h-4 text-emerald-700" aria-hidden="true" />
            <span>1. Identity of Data Controller & DPO</span>
          </h2>
          <p>
            The Data Controller responsible for your personal information under the General Data Protection Regulation (GDPR) and California Consumer Privacy Act (CCPA) is:
          </p>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-800 space-y-1">
            <p className="font-bold">CARELYNX Healthcare Technologies Ltd.</p>
            <p>Registration Number: CL-2026-HC9182</p>
            <p>Corporate Office: 100 Healthcare Corridor, Suite 400, Tech City</p>
            <p>
              Data Protection Officer (DPO):{" "}
              <a href="mailto:dpo@carelynx.local" className="text-emerald-700 underline font-semibold">
                dpo@carelynx.local
              </a>
            </p>
          </div>
        </section>

        {/* Section 2: Data Minimization */}
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <UserCheck className="w-4 h-4 text-emerald-700" aria-hidden="true" />
            <span>2. Strict Data Minimization & Categories Collected</span>
          </h2>
          <p>
            In accordance with GDPR Article 5(1)(c) (&quot;data minimization&quot;), CARELYNX collects and processes only the information strictly necessary to provide discharge instructions:
          </p>
          <ul className="list-disc pl-5 space-y-2">
            <li>
              <strong>Uploaded Clinical Documents:</strong> Discharge summaries, handwritten or digital prescriptions, and post-operative instruction sheets submitted directly by the patient or authorized caregiver.
            </li>
            <li>
              <strong>Derived Medical Facts:</strong> Extracted appointment dates, medication names, dosages, wound care instructions, and emergency warning symptoms.
            </li>
            <li>
              <strong>Technical Telemetry:</strong> Anonymized server logs (IP address hashed with SHA-256, HTTP status codes, browser client user-agent) retained solely for security defense and rate-limiting.
            </li>
          </ul>
          <div className="p-3.5 rounded-xl bg-slate-100/70 border border-slate-200 text-xs text-slate-700">
            <strong>What We Never Collect:</strong> We never collect social security numbers, credit card details, advertising tracking cookies, or biometric identifiers.
          </div>
        </section>

        {/* Section 3: Legal Basis for Processing */}
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <FileText className="w-4 h-4 text-emerald-700" aria-hidden="true" />
            <span>3. Lawful Basis for Processing (GDPR Articles 6 & 9)</span>
          </h2>
          <p>
            Because healthcare paperwork contains special category health data, we process your information under:
          </p>
          <ul className="list-disc pl-5 space-y-2">
            <li>
              <strong>Explicit Consent (GDPR Art. 6(1)(a) & Art. 9(2)(a)):</strong> You provide voluntary, informed consent prior to document upload.
            </li>
            <li>
              <strong>Provision of Health Care Services (GDPR Art. 9(2)(h)):</strong> Assisting the navigation and comprehension of legitimate hospital discharge directions.
            </li>
          </ul>
        </section>

        {/* Section 4: Storage, Encryption & Security */}
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Lock className="w-4 h-4 text-emerald-700" aria-hidden="true" />
            <span>4. Security Safeguards & Zero-Leakage Architecture</span>
          </h2>
          <p>
            CARELYNX implements defense-in-depth technical and organizational measures aligned with HIPAA Security Rule (45 CFR § 164.312) and ISO/IEC 27001:
          </p>
          <ul className="list-disc pl-5 space-y-2">
            <li>
              <strong>Encryption in Transit & At Rest:</strong> All communications enforce TLS 1.3 encryption. Uploaded documents are assigned randomized UUIDv4 storage keys outside public web roots.
            </li>
            <li>
              <strong>Zero Commercial AI Training:</strong> Your clinical paperwork is never stored, scraped, or ingested to train public machine-learning models.
            </li>
            <li>
              <strong>Audit Logging:</strong> All document accesses and clinical review adjudications create tamper-evident audit logs.
            </li>
          </ul>
        </section>

        {/* Section 5: User Rights under GDPR & CCPA/CPRA */}
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-700" aria-hidden="true" />
            <span>5. Your Legal Rights (Access, Deletion, Portability)</span>
          </h2>
          <p>
            Depending on your jurisdiction, you possess the following enforceable data subject rights:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
            <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50">
              <strong className="block font-bold text-slate-900 mb-1">Right to Erasure (To be Forgotten)</strong>
              Request the immediate deletion of all uploaded documents and extracted medical records.
            </div>
            <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50">
              <strong className="block font-bold text-slate-900 mb-1">Right of Access & Portability</strong>
              Export a machine-readable JSON or print-ready record of all extracted clinical facts.
            </div>
            <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50">
              <strong className="block font-bold text-slate-900 mb-1">Right to Rectification</strong>
              Flag ambiguous or erroneous extractions for clinical review correction.
            </div>
            <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50">
              <strong className="block font-bold text-slate-900 mb-1">Right to Withdraw Consent</strong>
              Revoke processing permissions at any time without punitive consequences.
            </div>
          </div>
          <p className="pt-2">
            You can exercise your deletion or export rights instantly through our dedicated{" "}
            <Link
              href="/privacy/data-request"
              className="text-emerald-700 font-bold underline underline-offset-2 hover:text-emerald-900 focus-visible:outline-2 focus-visible:outline-emerald-600 rounded"
            >
              Data Deletion & Rights Portal
            </Link>.
          </p>
        </section>

        {/* Section 6: Children's Health Data & Parental Consent */}
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-emerald-700" aria-hidden="true" />
            <span>6. Protection of Minors (COPPA & GDPR Article 8)</span>
          </h2>
          <p>
            CARELYNX does not knowingly allow unsupervised access by children under 18 years of age. If a child&apos;s pediatric discharge paperwork is processed, it must be submitted exclusively by a parent or legally recognized guardian. We provide immediate deletion mechanisms upon verification of unauthorized submission.
          </p>
        </section>

        {/* Section 7: Inquiries & Supervisory Authorities */}
        <section className="flex flex-col gap-3 border-t border-slate-100 pt-6">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Mail className="w-4 h-4 text-emerald-700" aria-hidden="true" />
            <span>7. Contacting the DPO or Lodging a Complaint</span>
          </h2>
          <p>
            If you have inquiries regarding this privacy framework or believe your rights have not been respected, contact our Data Protection Officer at:
          </p>
          <p className="font-mono text-xs bg-slate-100 p-3 rounded-xl border border-slate-200">
            Email: dpo@carelynx.local • Subject: Data Privacy Inquiry
          </p>
          <p className="text-xs text-slate-500">
            EU residents have the right to lodge a formal complaint with their respective national Data Protection Authority (DPA).
          </p>
        </section>

      </main>
    </div>
  );
}
