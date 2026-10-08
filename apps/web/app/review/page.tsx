"use client";

import { useEffect, useState } from "react";
import { 
  getOpenReviews, getFact, getFactEvidence, resolveReview,
  type ReviewCaseResponse, type FactResponse, type EvidenceResponse
} from "@/lib/api";
import { 
  AlertTriangle, CheckCircle2, XCircle, FileText, Loader2, 
  ShieldAlert, UserCheck, ChevronRight, Stethoscope, Clock, Check
} from "lucide-react";

export default function ReviewDashboard() {
  const [reviews, setReviews] = useState<ReviewCaseResponse[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [selectedReview, setSelectedReview] = useState<ReviewCaseResponse | null>(null);
  const [facts, setFacts] = useState<FactResponse[]>([]);
  const [evidence, setEvidence] = useState<Record<string, EvidenceResponse[]>>({});
  
  const [resolving, setResolving] = useState(false);
  const [selectedWinningFact, setSelectedWinningFact] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [filterSeverity, setFilterSeverity] = useState<"ALL" | "HIGH" | "MEDIUM" | "LOW">("ALL");

  const fetchReviews = async () => {
    try {
      setLoading(true);
      const data = await getOpenReviews();
      setReviews(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, []);

  const selectReview = async (review: ReviewCaseResponse) => {
    setSelectedReview(review);
    setFacts([]);
    setEvidence({});
    setSelectedWinningFact(null);
    setNotes("");
    
    try {
      const fetchedFacts = await Promise.all(
        review.fact_ids.map(id => getFact(id))
      );
      setFacts(fetchedFacts);
      
      const evMap: Record<string, EvidenceResponse[]> = {};
      for (const fact of fetchedFacts) {
        evMap[fact.id] = await getFactEvidence(fact.id);
      }
      setEvidence(evMap);
    } catch (err) {
      console.error("Failed to fetch review details", err);
    }
  };

  const handleResolve = async (decision: "approve" | "reject") => {
    if (!selectedReview) return;
    setResolving(true);
    try {
      await resolveReview(selectedReview.id, {
        decision,
        resolution_notes: notes || (decision === "approve" ? "Verified and approved by clinician" : "Rejected due to clinical inconsistency"),
        reviewer_id: "clinician-reviewer-1",
        winning_fact_id: selectedWinningFact || undefined
      });
      setSelectedReview(null);
      await fetchReviews();
    } catch (err) {
      console.error("Failed to resolve", err);
    } finally {
      setResolving(false);
    }
  };

  const filteredReviews = reviews.filter(r => {
    if (filterSeverity === "ALL") return true;
    return r.severity === filterSeverity;
  });

  return (
    <div className="flex-1 flex h-[calc(100vh-4rem)] overflow-hidden bg-bg">
      {/* Sidebar: Case Queue */}
      <aside className="w-80 sm:w-96 border-r border-line bg-surface/80 backdrop-blur flex flex-col h-full z-10 shrink-0">
        <div className="p-4 sm:p-5 border-b border-line flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h1 className="font-bold text-base text-slate-800 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-500" />
              <span>Clinical Review Queue</span>
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 border border-amber-200 text-amber-700 font-mono">
              {reviews.length} Open
            </span>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed">
            Safety flags requiring human verification: document conflicts, OCR quality, or unverified claims.
          </p>

          {/* Severity Filters */}
          <div className="flex items-center gap-1.5 pt-1">
            {(["ALL", "HIGH", "MEDIUM", "LOW"] as const).map(sev => (
              <button
                key={sev}
                onClick={() => setFilterSeverity(sev)}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition-all ${filterSeverity === sev ? 'bg-slate-900 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>
        
        {/* Queue Items List */}
        <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
          {loading ? (
            <div className="p-8 flex flex-col items-center justify-center gap-2 text-slate-400 text-xs">
              <Loader2 className="w-5 h-5 animate-spin text-emerald-600" />
              <span>Loading review queue...</span>
            </div>
          ) : filteredReviews.length === 0 ? (
            <div className="p-8 text-center flex flex-col items-center justify-center gap-2 text-slate-400 text-xs">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 opacity-60" />
              <p className="font-semibold text-slate-800">All cases verified</p>
              <p>No open review cases matching this filter.</p>
            </div>
          ) : (
            filteredReviews.map(r => (
              <button
                key={r.id}
                onClick={() => selectReview(r)}
                className={`w-full text-left p-4 hover:bg-slate-50/80 transition-all flex flex-col gap-2 ${selectedReview?.id === r.id ? 'bg-emerald-50/60 border-l-4 border-emerald-600 shadow-sm' : ''}`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full uppercase ${r.severity === 'HIGH' ? 'bg-rose-100 text-rose-700 border border-rose-200' : 'bg-amber-100 text-amber-700 border border-amber-200'}`}>
                    {r.reason_code}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {new Date(r.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <p className="text-xs font-semibold text-slate-800 line-clamp-2 leading-snug">
                  {r.reason}
                </p>
                <span className="text-[11px] text-slate-500 flex items-center gap-1">
                  Case ID: {r.case_id.substring(0, 8)}... <ChevronRight className="w-3 h-3 ml-auto text-slate-400" />
                </span>
              </button>
            ))
          )}
        </div>
      </aside>

      {/* Main: Clinical Comparator Workspace */}
      <main className="flex-1 h-full overflow-y-auto bg-slate-50/40 p-6 sm:p-8">
        {selectedReview ? (
          <div className="max-w-4xl mx-auto flex flex-col gap-6 fade-in">
            {/* Header Callout */}
            <div className="card p-6 bg-white border-line shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <span className="text-xs font-mono font-bold text-amber-700 bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200 uppercase">
                    {selectedReview.reason_code} • Severity: {selectedReview.severity}
                  </span>
                  <h2 className="text-xl font-bold text-slate-900 mt-2">
                    {selectedReview.reason}
                  </h2>
                  {selectedReview.recommended_action && (
                    <p className="text-xs text-emerald-700 font-mono mt-1 font-semibold">
                      Recommended Action: {selectedReview.recommended_action}
                    </p>
                  )}
                </div>
                <div className="px-3 py-1 rounded-full bg-slate-100 border border-slate-200 text-xs font-mono text-slate-600 shrink-0">
                  Review Case #{selectedReview.id.substring(0, 8)}
                </div>
              </div>
            </div>

            {/* Side-by-Side Fact & Evidence Comparison */}
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                  <Stethoscope className="w-4 h-4 text-emerald-600" />
                  <span>Statements & Document Excerpts Under Review</span>
                </h3>
                {selectedReview.reason_code === 'CONFLICT' && (
                  <span className="text-xs text-amber-800 font-medium bg-amber-50 px-2.5 py-1 rounded-full border border-amber-200">
                    Select the winning statement below to approve
                  </span>
                )}
              </div>

              <div className={selectedReview.reason_code === 'CONFLICT' ? "grid grid-cols-1 md:grid-cols-2 gap-4" : "flex flex-col gap-4"}>
                {facts.length === 0 ? (
                  <div className="card p-8 flex items-center justify-center gap-2 text-slate-400 text-xs bg-white">
                    <Loader2 className="w-4 h-4 animate-spin text-emerald-600" />
                    <span>Fetching fact entities and excerpts...</span>
                  </div>
                ) : (
                  facts.map((fact, idx) => {
                    const evList = evidence[fact.id] || [];
                    const isWinning = selectedWinningFact === fact.id;
                    return (
                      <div 
                        key={fact.id}
                        className={`card p-5 flex flex-col justify-between gap-4 transition-all relative bg-white ${isWinning ? 'ring-2 ring-emerald-500 border-emerald-500 bg-emerald-50/30 shadow-md' : 'border-line shadow-sm'}`}
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
                                  className="accent-emerald-600 w-3.5 h-3.5"
                                />
                                <span>Select as Correct</span>
                              </label>
                            )}
                          </div>

                          {/* Fact Content */}
                          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs font-mono text-slate-800 leading-relaxed">
                            {JSON.stringify(fact.value, null, 2)}
                          </div>

                          {/* Source Snippet */}
                          <div className="mt-3 flex flex-col gap-1.5">
                            <span className="text-[11px] font-semibold text-slate-500 flex items-center gap-1">
                              <FileText className="w-3.5 h-3.5 text-slate-400" />
                              Verbatim Document Excerpt:
                            </span>
                            {evList.length > 0 && evList[0].snippet ? (
                              <div className="p-3 bg-emerald-50/60 border-l-2 border-emerald-500 rounded-r-lg text-xs italic text-slate-700">
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

            {/* Resolution Form */}
            <div className="card p-6 bg-white border-line shadow-sm flex flex-col gap-4">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-emerald-600" />
                <span>Clinician Resolution & Notes</span>
              </h3>

              <textarea 
                value={notes}
                onChange={e => setNotes(e.target.value)}
                placeholder="Enter clinical rationale or notes regarding this resolution..."
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 min-h-[90px] resize-y"
              />

              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <button
                  onClick={() => handleResolve("approve")}
                  disabled={resolving || (selectedReview.reason_code === 'CONFLICT' && !selectedWinningFact)}
                  className="flex-1 py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs sm:text-sm font-semibold flex items-center justify-center gap-2 transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
                >
                  {resolving ? <Loader2 className="w-4 h-4 animate-spin"/> : <CheckCircle2 className="w-4 h-4"/>}
                  <span>Approve & Verify Statement{selectedReview.reason_code === 'CONFLICT' ? ' (Resolve Conflict)' : ''}</span>
                </button>

                <button
                  onClick={() => handleResolve("reject")}
                  disabled={resolving}
                  className="py-2.5 px-4 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs sm:text-sm font-semibold flex items-center justify-center gap-2 transition-colors disabled:opacity-40"
                >
                  {resolving ? <Loader2 className="w-4 h-4 animate-spin"/> : <XCircle className="w-4 h-4"/>}
                  <span>Reject Statement</span>
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-400 gap-3">
            <ShieldAlert className="w-12 h-12 text-slate-300 opacity-80" />
            <h3 className="text-base font-semibold text-slate-800">Select a review case</h3>
            <p className="text-xs max-w-sm text-slate-500">
              Choose a case from the queue on the left to inspect side-by-side evidence excerpts and submit your clinical resolution.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

