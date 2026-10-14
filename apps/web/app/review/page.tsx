/* eslint-disable react-hooks/exhaustive-deps */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  getOpenReviews, getFact, getFactEvidence, resolveReview,
  type ReviewCaseResponse, type FactResponse, type EvidenceResponse
} from "@/lib/api";
import { 
  auth, getMasterUserData, logUserActivity 
} from "@/lib/firebase";
import { 
  AlertTriangle, CheckCircle2, XCircle, FileText, Loader2, 
  ShieldAlert, UserCheck, ChevronRight, Stethoscope, Clock, Check, RefreshCw,
  Pill, Calendar, Sparkles, Activity, ArrowLeft
} from "lucide-react";

/**
 * Human-readable presentation of extracted clinical facts instead of raw JSON dumps.
 */
function HumanReadableFactValue({ fact }: { fact: FactResponse }) {
  const v = (fact.value || {}) as Record<string, any>;
  
  switch (fact.fact_type) {
    case "medication": {
      const name = String(v.name || "Medication").trim();
      const strength = v.strength ? String(v.strength).trim() : null;
      const freq = v.frequency ? String(v.frequency).trim() : null;
      const timing = v.timing ? String(v.timing).trim() : null;
      const duration = v.duration ? String(v.duration).trim() : null;
      const quantity = v.quantity ? String(v.quantity).trim() : null;
      const simplified = v.simplified_meaning || v.meaning || v.explanation;
      
      return (
        <div className="flex flex-col gap-3 p-4 rounded-xl bg-slate-50 border border-slate-200 text-slate-800">
          <div className="flex items-center justify-between gap-2 flex-wrap border-b border-slate-200/60 pb-2">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                <Pill className="w-4 h-4" />
              </div>
              <span className="text-sm font-bold text-slate-900 tracking-tight">{name}</span>
            </div>
            {strength && (
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-mono text-xs font-bold shadow-2xs">
                {strength}
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            {freq && (
              <div className="flex items-start gap-1.5 bg-white p-2 rounded-lg border border-slate-200/80">
                <Clock className="w-3.5 h-3.5 text-emerald-600 mt-0.5 shrink-0" />
                <div>
                  <span className="text-slate-500 font-medium block text-[10px] uppercase">Directions / Frequency</span>
                  <span className="font-semibold text-slate-800">{freq}</span>
                </div>
              </div>
            )}
            {timing && (
              <div className="flex items-start gap-1.5 bg-white p-2 rounded-lg border border-slate-200/80">
                <Clock className="w-3.5 h-3.5 text-slate-400 mt-0.5 shrink-0" />
                <div>
                  <span className="text-slate-500 font-medium block text-[10px] uppercase">Timing</span>
                  <span className="font-semibold text-slate-800">{timing}</span>
                </div>
              </div>
            )}
            {duration && (
              <div className="flex items-start gap-1.5 bg-white p-2 rounded-lg border border-slate-200/80">
                <Calendar className="w-3.5 h-3.5 text-slate-400 mt-0.5 shrink-0" />
                <div>
                  <span className="text-slate-500 font-medium block text-[10px] uppercase">Course Duration</span>
                  <span className="font-semibold text-slate-800">{duration}</span>
                </div>
              </div>
            )}
            {quantity && (
              <div className="flex items-start gap-1.5 bg-white p-2 rounded-lg border border-slate-200/80">
                <FileText className="w-3.5 h-3.5 text-slate-400 mt-0.5 shrink-0" />
                <div>
                  <span className="text-slate-500 font-medium block text-[10px] uppercase">Dispensed Quantity</span>
                  <span className="font-semibold text-slate-800">{quantity}</span>
                </div>
              </div>
            )}
          </div>

          {simplified && (
            <div className="p-2.5 rounded-lg bg-emerald-50/90 border border-emerald-200 text-xs text-emerald-950 flex items-start gap-2 leading-relaxed">
              <Sparkles className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold block text-[10px] text-emerald-800 uppercase tracking-wide">Plain-Language Patient Guide</span>
                <span>{String(simplified)}</span>
              </div>
            </div>
          )}
        </div>
      );
    }
    case "follow_up": {
      const date = v.date ? String(v.date).trim() : null;
      const time = v.time ? String(v.time).trim() : null;
      const dept = v.department ? String(v.department).trim() : null;
      const provider = v.clinician || v.provider ? String(v.clinician || v.provider).trim() : null;
      const raw = v.raw_text ? String(v.raw_text).trim() : null;
      const simplified = v.simplified_meaning || v.meaning;

      return (
        <div className="flex flex-col gap-3 p-4 rounded-xl bg-slate-50 border border-slate-200 text-slate-800 text-xs">
          <div className="flex items-center gap-2 border-b border-slate-200/60 pb-2">
            <div className="w-7 h-7 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center shrink-0">
              <Calendar className="w-4 h-4" />
            </div>
            <div>
              <span className="text-sm font-bold text-slate-900 block">
                {dept ? `${dept} Follow-Up Appointment` : "Follow-Up Consultation"}
              </span>
              {provider && <span className="text-[11px] text-slate-500">With {provider}</span>}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {date && (
              <div className="bg-white p-2 rounded-lg border border-slate-200/80">
                <span className="text-slate-500 font-medium block text-[10px] uppercase">Scheduled Date</span>
                <span className="font-bold text-slate-900 text-xs">{date}</span>
              </div>
            )}
            {time && (
              <div className="bg-white p-2 rounded-lg border border-slate-200/80">
                <span className="text-slate-500 font-medium block text-[10px] uppercase">Scheduled Time</span>
                <span className="font-bold text-slate-900 text-xs">{time}</span>
              </div>
            )}
            {raw && raw !== date && (
              <div className="sm:col-span-2 bg-white p-2 rounded-lg border border-slate-200/80">
                <span className="text-slate-500 font-medium block text-[10px] uppercase">Stated Instructions</span>
                <span className="font-medium text-slate-800">{raw}</span>
              </div>
            )}
          </div>

          {simplified && (
            <div className="p-2.5 rounded-lg bg-purple-50/90 border border-purple-200 text-xs text-purple-950 flex items-start gap-2 leading-relaxed">
              <Sparkles className="w-3.5 h-3.5 text-purple-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold block text-[10px] text-purple-800 uppercase tracking-wide">Plain-Language Patient Guide</span>
                <span>{String(simplified)}</span>
              </div>
            </div>
          )}
        </div>
      );
    }
    case "warning_sign": {
      const text = v.text || "Warning symptom";
      const simplified = v.simplified_meaning || v.meaning;
      return (
        <div className="flex flex-col gap-2.5 p-4 rounded-xl bg-rose-50/70 border border-rose-200 text-slate-800 text-xs">
          <div className="flex items-center gap-2 text-rose-700 font-bold border-b border-rose-200/60 pb-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span className="text-xs uppercase tracking-wider">Emergency Red Flag Symptom</span>
          </div>
          <p className="text-sm font-semibold text-rose-950 leading-relaxed bg-white p-2.5 rounded-lg border border-rose-200">
            {text}
          </p>
          {simplified && (
            <div className="p-2 rounded-lg bg-white/90 border border-rose-200 text-xs text-rose-900 flex items-start gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-rose-600 shrink-0 mt-0.5" />
              <span>{String(simplified)}</span>
            </div>
          )}
        </div>
      );
    }
    case "instruction":
    case "documented_condition": {
      const text = v.text || v.raw_text || "Care Instruction";
      const simplified = v.simplified_meaning || v.meaning;
      return (
        <div className="flex flex-col gap-2.5 p-4 rounded-xl bg-teal-50/70 border border-teal-200 text-slate-800 text-xs">
          <div className="flex items-center gap-2 text-teal-800 font-bold border-b border-teal-200/60 pb-2">
            <Activity className="w-4 h-4 shrink-0" />
            <span className="text-xs uppercase tracking-wider">
              {fact.fact_type === "instruction" ? "Discharge Care Instruction" : "Clinical Documented Condition"}
            </span>
          </div>
          <p className="text-xs font-semibold text-slate-900 leading-relaxed bg-white p-2.5 rounded-lg border border-teal-200">
            {text}
          </p>
          {simplified && (
            <div className="p-2 rounded-lg bg-white/90 border border-teal-200 text-xs text-teal-900 flex items-start gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-teal-600 shrink-0 mt-0.5" />
              <span>{String(simplified)}</span>
            </div>
          )}
        </div>
      );
    }
    case "allergy": {
      const isNkda = v.no_known_allergies === true;
      return (
        <div className="flex flex-col gap-2 p-4 rounded-xl bg-amber-50/70 border border-amber-200 text-slate-800 text-xs">
          <div className="flex items-center gap-2 text-amber-800 font-bold border-b border-amber-200/60 pb-2">
            <ShieldAlert className="w-4 h-4 shrink-0" />
            <span className="text-xs uppercase tracking-wider">Documented Allergy Information</span>
          </div>
          <p className="text-sm font-bold text-slate-900 bg-white p-2.5 rounded-lg border border-amber-200">
            {isNkda ? "No Known Drug Allergies (NKDA)" : `Allergic to: ${v.substance || "Unspecified medication / substance"}`}
          </p>
        </div>
      );
    }
    case "encounter_date": {
      const kind = v.kind === "admission" ? "Hospital Admission" : v.kind === "discharge" ? "Hospital Discharge" : "Encounter";
      return (
        <div className="flex flex-col gap-2 p-4 rounded-xl bg-slate-50 border border-slate-200 text-slate-800 text-xs">
          <div className="flex items-center gap-2 font-bold text-slate-700 border-b border-slate-200/60 pb-2">
            <Clock className="w-4 h-4 text-slate-500 shrink-0" />
            <span className="text-xs uppercase tracking-wider">{kind} Date</span>
          </div>
          <p className="text-sm font-bold text-slate-900 bg-white p-2.5 rounded-lg border border-slate-200">
            {v.date || v.raw_text}
          </p>
        </div>
      );
    }
    default: {
      return (
        <div className="flex flex-col gap-2 p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-800">
          <span className="font-bold uppercase tracking-wider text-[10px] text-slate-500">{fact.fact_type}</span>
          <div className="space-y-1.5 bg-white p-2.5 rounded-lg border border-slate-200">
            {Object.entries(v)
              .filter(([_, val]) => val !== null && val !== undefined && val !== "")
              .map(([key, val]) => (
                <div key={key} className="flex gap-2">
                  <span className="font-semibold text-slate-500 capitalize shrink-0">{key.replace(/_/g, " ")}:</span>
                  <span className="font-medium text-slate-900">{typeof val === "object" ? JSON.stringify(val) : String(val)}</span>
                </div>
              ))}
          </div>
        </div>
      );
    }
  }
}

function ReviewDashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryReviewId = searchParams?.get("id") || searchParams?.get("review_id");
  const queryCaseId = searchParams?.get("case_id");

  const [reviews, setReviews] = useState<ReviewCaseResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeUserCaseId, setActiveUserCaseId] = useState<string | null>(null);
  
  const [selectedReview, setSelectedReview] = useState<ReviewCaseResponse | null>(null);
  const [facts, setFacts] = useState<FactResponse[]>([]);
  const [evidence, setEvidence] = useState<Record<string, EvidenceResponse[]>>({});
  
  const [resolving, setResolving] = useState(false);
  const [selectedWinningFact, setSelectedWinningFact] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<"ALL" | "HIGH" | "MEDIUM" | "LOW">("ALL");

  const selectReview = async (review: ReviewCaseResponse) => {
    setSelectedReview(review);
    setFacts([]);
    setEvidence({});
    setSelectedWinningFact(null);
    setNotes("");
    
    try {
      const factList = await Promise.all(
        review.fact_ids.map(id => getFact(id))
      );
      setFacts(factList);

      const evMap: Record<string, EvidenceResponse[]> = {};
      await Promise.all(
        review.fact_ids.map(async id => {
          evMap[id] = await getFactEvidence(id);
        })
      );
      setEvidence(evMap);
    } catch (err) {
      console.error("Failed to fetch review details", err);
    }
  };

  const fetchReviews = async () => {
    try {
      setLoading(true);
      setActionError(null);

      // Determine the user's active/recent uploaded case
      let targetCaseId: string | null = queryCaseId || null;
      const currentUser = auth.currentUser;
      const allowedCaseIds = new Set<string>();

      if (typeof window !== "undefined") {
        if (currentUser) {
          const userKey = `carelynx_recent_case_${currentUser.uid}`;
          targetCaseId = targetCaseId || localStorage.getItem(userKey);
          try {
            const master = await getMasterUserData(currentUser.uid);
            if (!targetCaseId) {
              targetCaseId = master.recent_case_id || master.cases?.[0]?.case_id || null;
            }
            master.cases?.forEach(c => allowedCaseIds.add(c.case_id));
          } catch {
            // fallback
          }
        }
        if (!targetCaseId) {
          targetCaseId = localStorage.getItem("carelynx_recent_case_id") || null;
        }
      }

      setActiveUserCaseId(targetCaseId);

      // CRITICAL FIX: If no file has been uploaded by this user, do NOT show foreign database alerts!
      if (!targetCaseId) {
        setReviews([]);
        setSelectedReview(null);
        setLoading(false);
        return;
      }

      allowedCaseIds.add(targetCaseId);

      // Fetch all open reviews from backend, and filter strictly to the recent uploaded file from this user
      const data = await getOpenReviews();
      const userFileReviews = data.filter(r => r.case_id === targetCaseId || (allowedCaseIds.size > 0 && allowedCaseIds.has(r.case_id) && r.case_id === targetCaseId));

      setReviews(userFileReviews);

      // Auto-select if redirected with specific review_id or if first item exists
      if (queryReviewId) {
        const target = userFileReviews.find(r => r.id === queryReviewId);
        if (target) selectReview(target);
      } else if (userFileReviews.length > 0) {
        selectReview(userFileReviews[0]);
      } else {
        setSelectedReview(null);
      }
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not load the review queue.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
    
    // Hide global footer while on review workspace
    const footer = document.querySelector("footer");
    if (footer) footer.style.display = "none";
    
    return () => {
      if (footer) footer.style.display = "";
    };
  }, [queryReviewId, queryCaseId]);

  const handleResolve = async (action: "approve" | "reject") => {
    if (!selectedReview) return;
    if (!notes.trim()) {
      setActionError("A clinical resolution note is mandatory before saving.");
      return;
    }

    setResolving(true);
    setActionError(null);
    const isConflict = Boolean(selectedReview.conflict_id);
    const decision = isConflict
      ? (action === "approve" ? "SELECT_SOURCE" : "REJECT")
      : (action === "approve" ? "APPROVE" : "REJECT");

    try {
      await resolveReview(selectedReview.id, {
        decision,
        resolution_notes: notes.trim(),
        reviewer_id: "clinician-reviewer-1",
        ...(isConflict && action === "approve" && selectedWinningFact ? { winning_fact_id: selectedWinningFact } : {})
      });

      if (auth.currentUser) {
        logUserActivity(
          auth.currentUser.uid, 
          "RESOLVED_REVIEW", 
          `Resolved clinical review alert: ${selectedReview.reason}`,
          { review_id: selectedReview.id, case_id: selectedReview.case_id, decision }
        );
      }

      setSelectedReview(null);
      await fetchReviews();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not resolve this review.");
    } finally {
      setResolving(false);
    }
  };

  const filteredReviews = reviews.filter(r => {
    if (filterSeverity === "ALL") return true;
    return r.severity === filterSeverity;
  });

  return (
    <div className="w-full h-[calc(100dvh-6.5rem)] flex flex-col md:flex-row overflow-hidden max-w-[1720px] mx-auto px-3 sm:px-6 lg:px-8 pb-4 pt-1 gap-4">
      {/* Left Sidebar: Queue of Open Reviews */}
      <aside className="w-full md:w-80 lg:w-96 border border-slate-200/80 rounded-2xl bg-white flex flex-col shrink-0 h-full overflow-hidden shadow-xs">
        {/* Workspace Brand / Header */}
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50 shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold text-xs">
              <Stethoscope className="w-4 h-4" />
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-bold text-slate-900 leading-none">Clinical Reviewer Workspace</span>
              <span className="text-[10px] text-slate-500 font-medium mt-0.5">
                {activeUserCaseId ? `Case #${activeUserCaseId.substring(0, 8)}` : "Recent Paperwork"}
              </span>
            </div>
          </div>
          <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 text-[10px] font-mono font-semibold border border-slate-200">
            {activeUserCaseId ? "FILTERED" : "EMPTY"}
          </span>
        </div>

        {/* Section Header */}
        <div className="p-4 border-b border-slate-100 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2 font-bold text-xs text-slate-800">
            <ShieldAlert className="w-4 h-4 text-emerald-700" />
            <span>Clinical Review Queue</span>
            <button 
              type="button"
              onClick={fetchReviews}
              className="p-1 hover:bg-slate-100 rounded-md text-slate-400 hover:text-slate-700 transition-colors cursor-pointer"
              title="Refresh Review Queue"
              aria-label="Refresh Review Queue"
            >
              <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin text-emerald-600' : ''}`} />
            </button>
          </div>
          <span className="text-xs bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded-full">
            {reviews.length} Open
          </span>
        </div>

        {/* Severity Filters */}
        <div className="flex gap-1.5 p-3 border-b border-slate-100 bg-slate-50/50 text-[11px] shrink-0">
          {(["ALL", "HIGH", "MEDIUM", "LOW"] as const).map(sev => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`px-2.5 py-1 rounded-md font-semibold transition-all cursor-pointer ${
                filterSeverity === sev 
                  ? "bg-white text-slate-900 shadow-2xs border border-slate-200" 
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/60"
              }`}
            >
              {sev}
            </button>
          ))}
        </div>

        {/* List of Cases */}
        <div 
          tabIndex={0}
          role="region"
          aria-label="Clinical Review Queue items"
          className="flex-1 min-h-0 overflow-y-auto divide-y divide-slate-100 review-queue-scroll custom-scrollbar overscroll-contain pb-16"
        >
          {loading ? (
            <div className="p-8 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin text-emerald-600" />
              <span>Loading review queue...</span>
            </div>
          ) : !activeUserCaseId ? (
            <div className="p-8 text-center text-xs text-slate-500">
              <FileText className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="font-semibold text-slate-700">No Document Uploaded</p>
              <p className="text-[11px] text-slate-400 mt-1">Upload discharge paperwork to see review alerts for your case.</p>
            </div>
          ) : filteredReviews.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">
              <Check className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
              <p className="font-semibold text-slate-700">All cases resolved</p>
              <p className="text-[11px] text-slate-400 mt-1">No open review alerts in your recent uploaded paperwork.</p>
            </div>
          ) : (
            filteredReviews.map(r => (
              <button
                key={r.id}
                onClick={() => selectReview(r)}
                className={`w-full text-left p-4 hover:bg-slate-50/80 transition-all flex flex-col gap-2 cursor-pointer ${selectedReview?.id === r.id ? 'bg-emerald-50/60 border-l-4 border-emerald-600 shadow-xs' : ''}`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                    r.severity === 'HIGH' ? 'bg-rose-100 text-rose-800' :
                    r.severity === 'MEDIUM' ? 'bg-amber-100 text-amber-800' :
                    'bg-slate-100 text-slate-700'
                  }`}>
                    {r.severity}
                  </span>
                  <span className="text-[11px] font-mono text-slate-400">
                    {r.created_at.split('T')[0]}
                  </span>
                </div>
                <div className="text-xs font-semibold text-slate-800 line-clamp-2">
                  {r.reason}
                </div>
                <div className="text-[11px] text-slate-500 flex items-center justify-between">
                  <span>{r.fact_ids.length} fact{r.fact_ids.length === 1 ? '' : 's'} flagged</span>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                </div>
              </button>
            ))
          )}
        </div>
      </aside>

      {/* Main Review Inspection Panel */}
      <main className="flex-1 flex flex-col h-full overflow-y-auto custom-scrollbar bg-slate-50/50 border border-slate-200/80 rounded-2xl shadow-xs">
        {selectedReview ? (
          <div className="p-6 max-w-5xl mx-auto w-full flex flex-col gap-6">
            {/* Header / Case Details */}
            <div className="card p-6 flex flex-col gap-3 shadow-xs bg-white">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  {selectedReview.reason_code} • Severity: {selectedReview.severity}
                </span>
                <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
                  {selectedReview.status}
                </span>
              </div>
              <h2 className="text-lg font-bold text-slate-900 leading-tight">
                {selectedReview.reason}
              </h2>
              {selectedReview.recommended_action && (
                <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-100 leading-relaxed">
                  <strong className="text-slate-800 font-semibold">Recommended Action:</strong> {selectedReview.recommended_action}
                </p>
              )}
              <div className="text-[11px] text-slate-500 flex items-center gap-4 pt-1 border-t border-slate-100">
                <span>Case UUID: <code className="font-mono text-slate-700">{selectedReview.case_id.substring(0, 8)}...</code></span>
                <span>Review ID: <code className="font-mono text-slate-700">{selectedReview.id.substring(0, 8)}...</code></span>
              </div>
            </div>

            {/* Statements & Sources Side-by-Side */}
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-emerald-600" />
                  <span>Statements & Document Excerpts Under Review</span>
                </h3>
                {selectedReview.reason_code === 'CONFLICT' && (
                  <span className="text-xs text-rose-600 font-semibold bg-rose-50 px-2 py-0.5 rounded-md border border-rose-100">
                    Select the winning statement to resolve conflict
                  </span>
                )}
              </div>

              <div className={selectedReview.reason_code === 'CONFLICT' ? "grid grid-cols-1 md:grid-cols-2 gap-4" : "flex flex-col gap-4"}>
                {facts.length === 0 ? (
                  <div className="card p-8 text-center text-xs text-slate-500 flex flex-col items-center gap-2 col-span-2">
                    <Loader2 className="w-5 h-5 animate-spin text-emerald-600" />
                    <span>Fetching fact entities and excerpts...</span>
                  </div>
                ) : (
                  facts.map((fact, idx) => {
                    const evList = evidence[fact.id] || [];
                    const isWinning = selectedWinningFact === fact.id;
                    return (
                      <div 
                        key={fact.id}
                        className={`card p-5 flex flex-col justify-between gap-4 transition-all relative bg-white ${isWinning ? 'ring-2 ring-emerald-500 border-emerald-500 bg-emerald-50/30 shadow-md' : 'border-line shadow-xs'}`}
                      >
                        <div>
                          <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-3">
                            <span className="text-xs font-bold text-emerald-700 uppercase">
                              Option {String.fromCharCode(65 + idx)}: {fact.fact_type}
                            </span>
                            
                            {selectedReview.reason_code === 'CONFLICT' && (
                              <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-800 cursor-pointer bg-slate-50 p-1 px-2.5 rounded-full border border-slate-200 hover:border-emerald-500 transition-colors">
                                <input 
                                  type="radio"
                                  name="winning_fact"
                                  checked={isWinning}
                                  onChange={() => setSelectedWinningFact(fact.id)}
                                  className="accent-emerald-600 w-3.5 h-3.5 cursor-pointer"
                                />
                                <span>Select as Correct</span>
                              </label>
                            )}
                          </div>

                          {/* Fact Content in Human Language */}
                          <HumanReadableFactValue fact={fact} />

                          {/* Source Snippet */}
                          <div className="mt-3 flex flex-col gap-1.5">
                            <span className="text-[11px] font-semibold text-slate-500 flex items-center gap-1">
                              <FileText className="w-3.5 h-3.5 text-slate-400" />
                              Verbatim Document Excerpt:
                            </span>
                            {evList.length > 0 && evList[0].snippet ? (
                              <div className="p-3 bg-emerald-50/60 border-l-3 border-emerald-500 rounded-r-lg text-xs italic text-slate-800 font-medium">
                                &quot;{evList[0].snippet}&quot;
                              </div>
                            ) : (
                              <span className="text-xs text-slate-400 italic">No snippet captured</span>
                            )}
                          </div>
                        </div>

                        <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-100 flex justify-between items-center">
                          <span>Fact ID: {fact.id.substring(0, 8)}...</span>
                          <span className="font-mono text-slate-700 font-semibold">Status: {fact.status}</span>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Reviewer Resolution Form */}
            <div className="card p-6 flex flex-col gap-4 shadow-sm bg-white border-line">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2 text-slate-900 font-bold text-sm">
                  <UserCheck className="w-4 h-4 text-emerald-600" />
                  <span>Clinical Adjudication Resolution</span>
                </div>
                <span className="text-xs text-slate-400 font-medium">
                  Reviewer ID: <strong className="text-slate-700">clinician-reviewer-1</strong>
                </span>
              </div>

              <label htmlFor="clinical-notes" className="text-xs font-semibold text-slate-700">
                Clinical Resolution Rationale <span className="text-rose-500">*</span>
              </label>
              <textarea
                id="clinical-notes"
                value={notes}
                onChange={e => setNotes(e.target.value)}
                placeholder="Explain the clinical basis for this determination (e.g., 'Confirmed with treating clinic that discharge summary 14 Oct follow-up supersedes draft note')..."
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 min-h-[90px] resize-y"
              />

              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => handleResolve("approve")}
                  disabled={resolving || (selectedReview.reason_code === 'CONFLICT' && !selectedWinningFact)}
                  className="flex-1 py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white text-xs sm:text-sm font-semibold flex items-center justify-center gap-2 transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-xs cursor-pointer"
                >
                  {resolving ? <Loader2 className="w-4 h-4 animate-spin"/> : <CheckCircle2 className="w-4 h-4"/>}
                  <span>Approve & Verify Statement{selectedReview.reason_code === 'CONFLICT' ? ' (Resolve Conflict)' : ''}</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleResolve("reject")}
                  disabled={resolving}
                  className="py-2.5 px-4 rounded-xl bg-rose-50 hover:bg-rose-100 active:bg-rose-200 text-rose-700 border border-rose-200 text-xs sm:text-sm font-semibold flex items-center justify-center gap-2 transition-colors disabled:opacity-40 cursor-pointer"
                >
                  {resolving ? <Loader2 className="w-4 h-4 animate-spin"/> : <XCircle className="w-4 h-4"/>}
                  <span>Reject Statement</span>
                </button>
              </div>
              {actionError && (
                <p role="alert" className="text-xs font-semibold text-rose-700">{actionError}</p>
              )}
            </div>
          </div>
        ) : !activeUserCaseId ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-500 gap-4 max-w-md mx-auto">
            <div className="w-16 h-16 rounded-2xl bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-100 shadow-sm">
              <FileText className="w-8 h-8" />
            </div>
            <div className="space-y-1.5">
              <h3 className="text-lg font-bold text-slate-900">No Medical Paperwork Uploaded</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Review alerts are strictly generated from your recent uploaded paperwork. You have not uploaded any discharge documents yet.
              </p>
            </div>
            <Link
              href="/?action=upload"
              className="px-5 py-2.5 rounded-full bg-brand hover:bg-brand-light text-white font-semibold text-xs flex items-center gap-2 shadow-sm transition-all cursor-pointer"
            >
              <Sparkles className="w-4 h-4" />
              <span>Upload Discharge Paperwork</span>
            </Link>
          </div>
        ) : reviews.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-500 gap-4 max-w-md mx-auto">
            <div className="w-16 h-16 rounded-2xl bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-100 shadow-sm">
              <CheckCircle2 className="w-8 h-8 text-emerald-600" />
            </div>
            <div className="space-y-1.5">
              <h3 className="text-lg font-bold text-slate-900">All Clear: No Review Alerts</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                No clinical dosage conflicts or safety ambiguities were flagged in your recent uploaded paperwork (Case #{activeUserCaseId.substring(0, 8)}).
              </p>
            </div>
            <Link
              href="/?action=care-plan"
              className="px-5 py-2.5 rounded-full bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs flex items-center gap-2 shadow-sm transition-all cursor-pointer"
            >
              <span>View Patient Care Plan →</span>
            </Link>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-400 gap-3">
            <ShieldAlert className="w-12 h-12 text-slate-300 opacity-80" />
            <h3 className="text-base font-semibold text-slate-800">Select a review case</h3>
            <p className="text-xs max-w-sm text-slate-500">
              Choose an alert from the queue on the left to inspect side-by-side evidence excerpts and submit your clinical resolution.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

export default function ReviewDashboard() {
  return (
    <Suspense fallback={
      <div className="w-full h-[calc(100dvh-4.5rem)] flex items-center justify-center bg-slate-50">
        <Loader2 className="w-6 h-6 animate-spin text-emerald-600" />
      </div>
    }>
      <ReviewDashboardContent />
    </Suspense>
  );
}
