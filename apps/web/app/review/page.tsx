"use client";

import { useEffect, useState } from "react";
import { 
  getOpenReviews, getFact, getFactEvidence, resolveReview,
  type ReviewCaseResponse, type FactResponse, type EvidenceResponse
} from "@/lib/api";
import { AlertTriangle, CheckCircle2, XCircle, FileText, Loader2, ArrowRight } from "lucide-react";

export default function ReviewDashboard() {
  const [reviews, setReviews] = useState<ReviewCaseResponse[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [selectedReview, setSelectedReview] = useState<ReviewCaseResponse | null>(null);
  const [facts, setFacts] = useState<FactResponse[]>([]);
  const [evidence, setEvidence] = useState<Record<string, EvidenceResponse[]>>({});
  
  const [resolving, setResolving] = useState(false);
  const [selectedWinningFact, setSelectedWinningFact] = useState<string | null>(null);
  const [notes, setNotes] = useState("");

  const fetchReviews = async () => {
    try {
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
        resolution_notes: notes,
        reviewer_id: "human-reviewer-1",
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

  const renderFactContent = (fact: FactResponse) => {
    return (
      <div className="text-sm">
        <div className="font-medium text-fg/90 mb-2 border-b border-line pb-2">{fact.fact_type}</div>
        <pre className="bg-bg/50 p-2 rounded text-xs overflow-auto font-mono text-muted">
          {JSON.stringify(fact.value, null, 2)}
        </pre>
        {evidence[fact.id]?.length > 0 && (
          <div className="mt-3 text-xs">
            <div className="text-muted mb-1 flex items-center gap-1"><FileText className="w-3 h-3"/> Evidence Snippet:</div>
            <div className="pl-3 border-l-2 border-accent/40 italic bg-accent/5 p-2 rounded rouded-l-none text-fg/80">
              "{evidence[fact.id][0].snippet}"
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex h-screen overflow-hidden bg-bg/20">
      {/* Sidebar: Queue */}
      <aside className="w-80 border-r border-line bg-bg flex flex-col h-full z-10">
        <div className="p-4 border-b border-line">
          <h1 className="font-semibold text-lg flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-400" />
            Review Queue
          </h1>
          <p className="text-xs text-muted mt-1">{reviews.length} cases need human attention</p>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="p-8 flex justify-center"><Loader2 className="w-5 h-5 animate-spin text-muted" /></div>
          ) : reviews.length === 0 ? (
            <div className="p-8 text-center text-muted text-sm">All caught up!</div>
          ) : (
            <div className="divide-y divide-line">
              {reviews.map(r => (
                <button
                  key={r.id}
                  onClick={() => selectReview(r)}
                  className={`w-full text-left p-4 hover:bg-line/20 transition-colors ${selectedReview?.id === r.id ? 'bg-line/30' : ''}`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-orange-500/20 text-orange-400">
                      {r.reason_code}
                    </span>
                    <span className="text-[10px] text-muted">{new Date(r.created_at).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-sm font-medium line-clamp-2 mt-2">{r.reason}</p>
                </button>
              ))}
            </div>
          )}
        </div>
      </aside>

      {/* Main: Review Workspace */}
      <main className="flex-1 h-full overflow-y-auto relative">
        {selectedReview ? (
          <div className="max-w-4xl mx-auto p-8 fade-in">
            <div className="mb-8">
              <h2 className="text-2xl font-semibold mb-2">Case Resolution</h2>
              <div className="p-4 rounded-xl border border-orange-500/30 bg-orange-500/5 text-orange-200">
                <div className="font-medium text-orange-400 mb-1 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4"/> Issue: {selectedReview.reason_code}
                </div>
                <p className="text-sm">{selectedReview.reason}</p>
                {selectedReview.recommended_action && (
                  <div className="mt-2 text-xs bg-black/20 p-2 rounded inline-block font-mono">
                    Action needed: {selectedReview.recommended_action}
                  </div>
                )}
              </div>
            </div>

            <div className="mb-8">
              <h3 className="text-lg font-medium mb-4 border-b border-line pb-2">Facts Under Review</h3>
              
              <div className={selectedReview.reason_code === 'CONFLICT' ? "grid grid-cols-2 gap-4" : "space-y-4"}>
                {facts.length === 0 ? (
                  <div className="flex items-center gap-2 text-muted text-sm"><Loader2 className="w-4 h-4 animate-spin"/> Loading facts...</div>
                ) : (
                  facts.map(fact => (
                    <div 
                      key={fact.id} 
                      className={`card p-5 relative transition-all ${selectedWinningFact === fact.id ? 'ring-2 ring-accent border-accent' : ''}`}
                    >
                      {selectedReview.reason_code === 'CONFLICT' && (
                        <div className="absolute top-4 right-4">
                          <label className="flex items-center gap-2 text-sm cursor-pointer">
                            <input 
                              type="radio" 
                              name="winning_fact" 
                              checked={selectedWinningFact === fact.id}
                              onChange={() => setSelectedWinningFact(fact.id)}
                              className="accent-accent w-4 h-4"
                            />
                            Select as correct
                          </label>
                        </div>
                      )}
                      
                      {renderFactContent(fact)}
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="card p-6 bg-bg/50 border-line/70">
              <h3 className="text-sm font-medium mb-3">Resolution Decision</h3>
              <textarea 
                value={notes}
                onChange={e => setNotes(e.target.value)}
                placeholder="Optional notes about this resolution..."
                className="w-full bg-bg border border-line rounded-lg p-3 text-sm min-h-[80px] focus:outline-none focus:border-accent resize-y mb-4"
              />
              
              <div className="flex gap-3">
                <button 
                  onClick={() => handleResolve("approve")}
                  disabled={resolving || (selectedReview.reason_code === 'CONFLICT' && !selectedWinningFact)}
                  className="flex-1 bg-verified/20 hover:bg-verified/30 text-verified border border-verified/50 py-2.5 rounded-lg font-medium flex items-center justify-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {resolving ? <Loader2 className="w-4 h-4 animate-spin"/> : <CheckCircle2 className="w-4 h-4"/>}
                  Approve Fact{selectedReview.reason_code === 'CONFLICT' ? ' (Resolve Conflict)' : ''}
                </button>
                <button 
                  onClick={() => handleResolve("reject")}
                  disabled={resolving}
                  className="flex-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 py-2.5 rounded-lg font-medium flex items-center justify-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {resolving ? <Loader2 className="w-4 h-4 animate-spin"/> : <XCircle className="w-4 h-4"/>}
                  Reject Fact{facts.length > 1 ? 's' : ''}
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-muted">
            <AlertTriangle className="w-12 h-12 mb-4 opacity-20" />
            <p>Select a case from the queue to review.</p>
          </div>
        )}
      </main>
    </div>
  );
}
