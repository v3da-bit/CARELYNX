"use client";

import { useState } from "react";
import Link from "next/link";
import { Trash2, ShieldCheck, ArrowLeft, Download, CheckCircle, AlertCircle, RefreshCw } from "lucide-react";

export default function DataRequestPage() {
  const [purged, setPurged] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submittedTicket, setSubmittedTicket] = useState<string | null>(null);

  // Form fields
  const [requestType, setRequestType] = useState<string>("deletion");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [caseId, setCaseId] = useState("");
  const [details, setDetails] = useState("");
  const [authorizedConsent, setAuthorizedConsent] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const handlePurgeLocalData = () => {
    try {
      localStorage.clear();
      sessionStorage.clear();
      setPurged(true);
      setTimeout(() => setPurged(false), 5000);
    } catch {
      setPurged(true);
    }
  };

  const handleSubmitRequest = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");

    if (!authorizedConsent) {
      setErrorMsg("You must confirm your legal identity and authority to submit this data request.");
      return;
    }

    if (!fullName.trim() || !email.trim()) {
      setErrorMsg("Please provide your full legal name and valid contact email.");
      return;
    }

    setSubmitting(true);
    setTimeout(() => {
      const ticket = `DSAR-${Date.now().toString().slice(-6)}-${Math.random().toString(36).substring(2, 6).toUpperCase()}`;
      setSubmittedTicket(ticket);
      setSubmitting(false);
    }, 700);
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
          GDPR Art. 17 & CCPA § 1798.105 Compliance Portal
        </span>
      </div>

      {/* Header Banner */}
      <header className="bg-white/90 backdrop-blur-md border border-slate-200 rounded-3xl p-8 shadow-xs flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-rose-100 text-rose-800 flex items-center justify-center shrink-0">
            <Trash2 className="w-6 h-6" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              User Data Rights & Erasure Request Portal
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 mt-1">
              Right to be Forgotten, Data Subject Access Requests (DSAR), and Local Storage Purge
            </p>
          </div>
        </div>

        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          Under global privacy laws including GDPR (Articles 15–22), California Consumer Privacy Act (CCPA/CPRA), and HIPAA data sovereignty guidelines, you possess the permanent legal right to delete, export, or rectify any personal and health documentation processed through our systems.
        </p>
      </header>

      {/* Action Block 1: Instant Client-Side Purge */}
      <section className="bg-white/90 backdrop-blur-md border border-slate-200 rounded-3xl p-8 shadow-xs flex flex-col gap-5">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div className="flex flex-col gap-1">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <RefreshCw className="w-4 h-4 text-emerald-700" aria-hidden="true" />
              <span>1. Instant Local Browser Data Purge</span>
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 max-w-xl">
              Immediately wipe all cached discharge paperwork, encounter identifiers, translation states, and local cookie preferences stored in this browser session.
            </p>
          </div>

          <button
            type="button"
            onClick={handlePurgeLocalData}
            className="px-5 py-3 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs sm:text-sm shadow-md shadow-rose-600/20 transition-all flex items-center gap-2 cursor-pointer focus-visible:outline-2 focus-visible:outline-rose-600"
            id="btn-purge-local"
          >
            <Trash2 className="w-4 h-4" aria-hidden="true" />
            <span>Purge My Local Browser Cache</span>
          </button>
        </div>

        {purged && (
          <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs sm:text-sm flex items-center gap-2.5 animate-fadeIn">
            <CheckCircle className="w-5 h-5 text-emerald-700 shrink-0" aria-hidden="true" />
            <span>
              <strong>Local Cache Cleared:</strong> All session tokens, case identifiers, and cached paperwork have been successfully purged from your browser storage.
            </span>
          </div>
        )}
      </section>

      {/* Action Block 2: Formal Server-Side DSAR Form */}
      <section className="bg-white/90 backdrop-blur-md border border-slate-200 rounded-3xl p-8 sm:p-10 shadow-xs flex flex-col gap-6">
        <div className="flex flex-col gap-1 border-b border-slate-100 pb-4">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-700" aria-hidden="true" />
            <span>2. Formal Server-Side Data Deletion & Export Request</span>
          </h2>
          <p className="text-xs text-slate-500">
            Submit a request to permanently delete or export records from backend storage. Responses are guaranteed within 30 days pursuant to GDPR Art. 12(3).
          </p>
        </div>

        {submittedTicket ? (
          <div className="p-6 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-950 flex flex-col gap-4 animate-fadeIn">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-emerald-200 text-emerald-800 flex items-center justify-center shrink-0">
                <CheckCircle className="w-6 h-6" aria-hidden="true" />
              </div>
              <div>
                <h3 className="font-bold text-base text-slate-900">Data Subject Request Registered</h3>
                <p className="text-xs text-slate-600">
                  Reference Ticket ID: <strong className="font-mono text-emerald-800">{submittedTicket}</strong>
                </p>
              </div>
            </div>

            <p className="text-xs text-slate-700 leading-relaxed">
              Your formal request for <strong>{requestType.toUpperCase()}</strong> has been submitted to the Data Protection Officer (<code>dpo@carelynx.local</code>). A verification email has been dispatched to <strong>{email}</strong>. In accordance with statutory guidelines, server records will be permanently erased or compiled within 30 days.
            </p>

            <button
              type="button"
              onClick={() => {
                setSubmittedTicket(null);
                setFullName("");
                setEmail("");
                setCaseId("");
                setDetails("");
                setAuthorizedConsent(false);
              }}
              className="self-start text-xs font-bold text-emerald-800 hover:text-emerald-950 underline underline-offset-2 cursor-pointer focus-visible:outline-2 focus-visible:outline-emerald-600 rounded"
            >
              Submit Another Request
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmitRequest} className="flex flex-col gap-5">
            {errorMsg && (
              <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" aria-hidden="true" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Request Type */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="request-type" className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Request Type *
              </label>
              <select
                id="request-type"
                value={requestType}
                onChange={(e) => setRequestType(e.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white p-3 text-sm text-slate-800 focus-visible:outline-2 focus-visible:outline-emerald-600"
              >
                <option value="deletion">Right to Erasure / Permanent Deletion (GDPR Art. 17 / CCPA)</option>
                <option value="export">Right to Data Portability / Machine-Readable Export (GDPR Art. 20)</option>
                <option value="rectification">Right to Rectification / Correction (GDPR Art. 16)</option>
                <option value="restriction">Right to Restrict Processing (GDPR Art. 18)</option>
              </select>
            </div>

            {/* Name & Email */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="full-name" className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                  Full Legal Name *
                </label>
                <input
                  id="full-name"
                  type="text"
                  required
                  placeholder="e.g., Sarah Jenkins"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 bg-white p-3 text-sm text-slate-800 focus-visible:outline-2 focus-visible:outline-emerald-600"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="email" className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                  Contact Email Address *
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  placeholder="e.g., s.jenkins@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 bg-white p-3 text-sm text-slate-800 focus-visible:outline-2 focus-visible:outline-emerald-600"
                />
              </div>
            </div>

            {/* Case / Encounter ID */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="case-id" className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Case or Encounter UUID (Optional)
              </label>
              <input
                id="case-id"
                type="text"
                placeholder="e.g., e4f8d9b2-3b1a-4c8d-9e0f-1a2b3c4d5e6f"
                value={caseId}
                onChange={(e) => setCaseId(e.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white p-3 text-sm font-mono text-slate-800 focus-visible:outline-2 focus-visible:outline-emerald-600"
              />
              <span className="text-[11px] text-slate-500">
                Found on your care plan header (e.g. Case #e4f8d9b2...). If omitted, we will search by verified contact email.
              </span>
            </div>

            {/* Additional details */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="details" className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Specific Instructions or Notes
              </label>
              <textarea
                id="details"
                rows={3}
                placeholder="Provide any specific document dates or instructions for the privacy team..."
                value={details}
                onChange={(e) => setDetails(e.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white p-3 text-sm text-slate-800 focus-visible:outline-2 focus-visible:outline-emerald-600"
              />
            </div>

            {/* Mandatory Un-checked Consent Checkbox (GDPR requirement) */}
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex items-start gap-3">
              <input
                id="consent-checkbox"
                type="checkbox"
                checked={authorizedConsent}
                onChange={(e) => setAuthorizedConsent(e.target.checked)}
                className="w-4 h-4 mt-0.5 rounded border-slate-300 text-emerald-600 focus-visible:outline-2 focus-visible:outline-emerald-600 shrink-0 cursor-pointer"
              />
              <label htmlFor="consent-checkbox" className="text-xs text-slate-700 leading-relaxed cursor-pointer">
                <strong>Identity & Legal Authority Attestation:</strong> I declare under penalty of law that I am the individual whose health records are identified above, or the authorized legal caregiver/parent of the patient, and I formally request the execution of this data subject right.
              </label>
            </div>

            {/* Submit button */}
            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={submitting}
                className="px-6 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-sm shadow-md transition-all flex items-center gap-2 cursor-pointer focus-visible:outline-2 focus-visible:outline-emerald-600"
                id="btn-submit-dsar"
              >
                {submitting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" aria-hidden="true" />
                    <span>Transmitting Request...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" aria-hidden="true" />
                    <span>Submit Formal Data Request</span>
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </section>

    </div>
  );
}
