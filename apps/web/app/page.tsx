"use client";

import { useEffect, useState, useRef } from "react";
import { 
  getHealth, createCase, uploadDocument, processDocument, getCase, getCaseFacts, getFactEvidence, translateCase,
  type Health, type CaseOut, type FactResponse, type EvidenceResponse
} from "@/lib/api";
import { FileUp, Loader2, Calendar, Pill, AlertTriangle, FileText, CheckCircle2, X } from "lucide-react";

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeCase, setActiveCase] = useState<CaseOut | null>(null);
  const [facts, setFacts] = useState<FactResponse[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Translation state
  const [language, setLanguage] = useState<"en" | "hi" | "gu">("en");
  const [isTranslating, setIsTranslating] = useState(false);
  const [translations, setTranslations] = useState<Record<string, Record<string, unknown>>>({});
  
  // Evidence panel state
  const [selectedFact, setSelectedFact] = useState<FactResponse | null>(null);
  const [evidence, setEvidence] = useState<EvidenceResponse[]>([]);
  const [isFetchingEvidence, setIsFetchingEvidence] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((e: Error) => setError(e.message));
  }, []);

  // Poll for case status
  useEffect(() => {
    if (!activeCase || !isProcessing) return;
    
    const interval = setInterval(async () => {
      try {
        const c = await getCase(activeCase.id);
        setActiveCase(c);
        
        const isStillProcessing = c.documents.some(d => d.processing_status === "PROCESSING" || d.processing_status === "UPLOADED");
        
        if (!isStillProcessing) {
          setIsProcessing(false);
          const f = await getCaseFacts(c.id);
          setFacts(f);
        }
      } catch (err) {
        console.error(err);
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, [activeCase, isProcessing]);

  const handleLanguageChange = async (targetLang: "en" | "hi" | "gu") => {
    if (targetLang === "en") {
      setLanguage("en");
      return;
    }
    if (!activeCase) return;
    
    setIsTranslating(true);
    try {
      const res = await translateCase(activeCase.id, targetLang);
      const newMap: Record<string, Record<string, unknown>> = {};
      res.translated_facts.forEach(t => {
        newMap[t.id] = t.translated_value;
      });
      setTranslations(newMap);
      setLanguage(targetLang);
    } catch (err) {
      console.error(err);
    } finally {
      setIsTranslating(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    try {
      setIsUploading(true);
      setError(null);
      
      let caseId = activeCase?.id;
      if (!caseId) {
        const newCase = await createCase();
        caseId = newCase.id;
      }
      
      const doc = await uploadDocument(caseId, file);
      await processDocument(doc.id);
      
      const c = await getCase(caseId);
      setActiveCase(c);
      setIsProcessing(true);
      
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };
  
  const viewEvidence = async (fact: FactResponse) => {
    setSelectedFact(fact);
    setIsFetchingEvidence(true);
    setEvidence([]);
    try {
      const ev = await getFactEvidence(fact.id);
      setEvidence(ev);
    } catch (err) {
      console.error(err);
    } finally {
      setIsFetchingEvidence(false);
    }
  };

  const getFactIcon = (type: string) => {
    switch (type) {
      case "encounter_date":
      case "follow_up": return <Calendar className="w-5 h-5 text-blue-400" />;
      case "medication": return <Pill className="w-5 h-5 text-purple-400" />;
      case "warning_sign": return <AlertTriangle className="w-5 h-5 text-orange-400" />;
      default: return <FileText className="w-5 h-5 text-gray-400" />;
    }
  };
  
  const getFactTitle = (fact: FactResponse) => {
    const val = language === "en" || !translations[fact.id] ? fact.value : translations[fact.id];
    switch (fact.fact_type) {
      case "encounter_date": return `Encounter: ${val.date || val.raw_text} (${val.kind})`;
      case "follow_up": return `Follow-up: ${val.date || val.raw_text || "Unknown date"}`;
      case "medication": {
        const details = [val.strength, val.frequency, val.timing].filter(Boolean).join(" ");
        return `${val.name} ${details ? "— " + details : ""}`;
      }
      case "warning_sign": return `Warning sign: ${val.text}`;
      case "documented_condition": return `Condition: ${val.text}`;
      case "allergy": return `Allergy: ${val.substance}`;
      case "instruction": return `Instruction: ${val.text}`;
      default: return fact.fact_type;
    }
  };

  const renderStatus = (fact: FactResponse) => {
    if (fact.status === "VERIFIED") return <span className="text-verified flex items-center gap-1 text-xs"><CheckCircle2 className="w-3 h-3" /> Verified</span>;
    if (fact.status === "NEEDS_REVIEW" || fact.status === "HUMAN_REQUIRED") return <span className="text-review flex items-center gap-1 text-xs"><AlertTriangle className="w-3 h-3" /> Needs review</span>;
    if (fact.status === "CONFLICT_DETECTED") return <span className="text-red-400 flex items-center gap-1 text-xs"><AlertTriangle className="w-3 h-3" /> Conflict detected</span>;
    return null;
  };

  return (
    <div className="flex h-full w-full relative">
      <section className={`mx-auto max-w-4xl w-full px-5 py-12 transition-all duration-300 ${selectedFact ? 'pr-80' : ''}`}>
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl md:text-4xl font-semibold tracking-tight">Clearer discharge instructions</h1>
            <p className="mt-3 max-w-2xl text-muted">
              Upload discharge documents. CARELYNX shows what they say, where each statement came from, and what needs a
              human to check.
            </p>
          </div>
          {activeCase && (
            <div className="flex bg-line/20 rounded-lg p-1 text-sm border border-line">
              <button onClick={() => handleLanguageChange("en")} className={`px-3 py-1.5 rounded-md flex items-center gap-2 transition-colors ${language === 'en' ? 'bg-bg text-fg shadow-sm' : 'text-muted hover:text-fg'}`}>English</button>
              <button onClick={() => handleLanguageChange("hi")} disabled={isTranslating} className={`px-3 py-1.5 rounded-md flex items-center gap-2 transition-colors ${language === 'hi' ? 'bg-bg text-fg shadow-sm' : 'text-muted hover:text-fg'} disabled:opacity-50`}>
                {isTranslating && language !== 'hi' ? <Loader2 className="w-3 h-3 animate-spin"/> : null} Hindi
              </button>
              <button onClick={() => handleLanguageChange("gu")} disabled={isTranslating} className={`px-3 py-1.5 rounded-md flex items-center gap-2 transition-colors ${language === 'gu' ? 'bg-bg text-fg shadow-sm' : 'text-muted hover:text-fg'} disabled:opacity-50`}>
                {isTranslating && language !== 'gu' ? <Loader2 className="w-3 h-3 animate-spin"/> : null} Gujarati
              </button>
            </div>
          )}
        </div>

        {/* Uploader */}
        <div className="mt-8 border border-dashed border-line/70 rounded-xl p-10 flex flex-col items-center justify-center bg-bg/30 relative hover:border-line transition-colors">
          <input 
            type="file" 
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed" 
            onChange={handleFileUpload}
            disabled={isUploading || isProcessing}
            ref={fileInputRef}
            accept="application/pdf,image/jpeg,image/png"
          />
          <div className="flex flex-col items-center gap-3 text-center pointer-events-none">
            {isUploading ? (
              <Loader2 className="w-10 h-10 text-muted animate-spin" />
            ) : (
              <FileUp className="w-10 h-10 text-muted" />
            )}
            <div>
              <p className="font-medium">
                {isUploading ? "Uploading document..." : "Click or drag to upload"}
              </p>
              <p className="text-sm text-muted mt-1">PDF, JPG, or PNG</p>
            </div>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-4 border border-red-900/50 bg-red-900/10 text-red-400 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Processing Status */}
        {activeCase && (
          <div className="mt-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-medium">Your Care Plan</h2>
              {isProcessing && (
                <span className="flex items-center gap-2 text-sm text-muted pulse-dot">
                  <Loader2 className="w-4 h-4 animate-spin" /> Processing AI extraction
                </span>
              )}
            </div>
            
            {/* Documents uploaded */}
            <div className="flex gap-2 flex-wrap mb-8">
              {activeCase.documents.map(d => (
                <div key={d.id} className="text-xs px-3 py-1.5 rounded-full border border-line/70 bg-bg flex items-center gap-2">
                  <span className="truncate max-w-[150px]" title={d.filename}>{d.filename}</span>
                  <span className={`w-2 h-2 rounded-full ${d.processing_status === 'COMPLETED' ? 'bg-verified' : d.processing_status === 'FAILED' ? 'bg-red-500' : 'bg-review animate-pulse'}`}></span>
                </div>
              ))}
            </div>

            {/* Timeline / Facts */}
            {!isProcessing && facts.length > 0 && (
              <div className="space-y-4 relative before:absolute before:inset-0 before:ml-7 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-line before:to-transparent">
                {facts.filter(f => f.status !== "REJECTED").map(fact => (
                  <div key={fact.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    <div className="flex items-center justify-center w-14 h-14 rounded-full border-4 border-bg bg-bg shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-[0_0_0_1px_rgba(255,255,255,0.1)] z-10">
                      {getFactIcon(fact.fact_type)}
                    </div>
                    <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] card p-5 flex flex-col gap-2 hover:border-accent/50 transition-colors cursor-pointer" onClick={() => viewEvidence(fact)}>
                      <div className="flex items-start justify-between">
                        <h3 className="font-medium leading-tight">{getFactTitle(fact)}</h3>
                      </div>
                      {renderStatus(fact)}
                      <div className="mt-2 pt-3 border-t border-line/30 flex justify-between items-center">
                        <span className="text-xs text-muted font-mono bg-bg/50 px-2 py-1 rounded">
                          Confidence: {fact.confidence !== null ? Math.round(fact.confidence * 100) + '%' : 'N/A'}
                        </span>
                        <button className="text-xs text-accent hover:text-accent-2 transition-colors">
                          View Evidence
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {!isProcessing && facts.length === 0 && activeCase.documents.some(d => d.processing_status === 'COMPLETED') && (
              <div className="p-8 text-center text-muted border border-line/50 rounded-xl">
                No structured facts could be reliably extracted from these documents.
              </div>
            )}
          </div>
        )}

        {/* Footer Status */}
        <div className="mt-16 pt-8 border-t border-line/70 text-xs text-muted flex justify-between">
          <span>CARELYNX Patient View</span>
          <div id="api-status">
            {!error && !health && <span className="pulse-dot">Checking API…</span>}
            {health && (
              <span>
                API <b className={health.status === "ok" ? "text-verified" : "text-review"}>{health.status}</b>
              </span>
            )}
          </div>
        </div>
      </section>

      {/* Evidence Sidebar */}
      {selectedFact && (
        <aside className="fixed right-0 top-0 h-full w-[400px] border-l border-line bg-bg/95 backdrop-blur shadow-2xl p-6 overflow-y-auto animate-in slide-in-from-right z-30">
          <div className="flex justify-between items-start mb-6">
            <h2 className="text-lg font-semibold">Evidence Viewer</h2>
            <button onClick={() => setSelectedFact(null)} className="p-1 hover:bg-line rounded-full transition-colors">
              <X className="w-5 h-5 text-muted" />
            </button>
          </div>
          
          <div className="mb-8">
            <div className="text-sm text-muted mb-1">Fact extracted</div>
            <div className="font-medium p-3 bg-line/20 rounded-lg border border-line/50">
              {getFactTitle(selectedFact)}
            </div>
            {selectedFact.status_reasons && selectedFact.status_reasons.length > 0 && (
              <div className="mt-3 p-3 bg-red-900/10 border border-red-900/50 rounded-lg">
                <div className="text-xs text-red-400 font-semibold mb-1">Status Reasons</div>
                <ul className="text-xs text-red-300 list-disc list-inside">
                  {selectedFact.status_reasons.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            )}
          </div>

          <div className="space-y-4">
            <h3 className="text-sm text-muted font-medium border-b border-line pb-2">Source Documents</h3>
            {isFetchingEvidence ? (
              <div className="flex justify-center p-8"><Loader2 className="w-6 h-6 animate-spin text-muted" /></div>
            ) : evidence.length > 0 ? (
              evidence.map(ev => {
                const doc = activeCase?.documents.find(d => d.id === ev.document_id);
                return (
                  <div key={ev.id} className="card p-4 text-sm">
                    <div className="flex items-center gap-2 mb-3 text-xs text-muted">
                      <FileText className="w-4 h-4" />
                      <span className="truncate">{doc?.filename || "Unknown document"}</span>
                      <span>• Page {ev.page_number}</span>
                    </div>
                    {ev.snippet ? (
                      <div className="relative">
                        <div className="absolute left-0 top-0 bottom-0 w-1 bg-accent/50 rounded-l"></div>
                        <p className="pl-4 text-fg/90 italic bg-line/10 p-2 rounded rounded-l-none text-xs leading-relaxed">
                          &quot;{ev.snippet}&quot;
                        </p>
                      </div>
                    ) : (
                      <p className="text-xs text-review italic">No direct snippet extracted.</p>
                    )}
                  </div>
                );
              })
            ) : (
              <p className="text-sm text-muted text-center p-4">No evidence found.</p>
            )}
          </div>
        </aside>
      )}
    </div>
  );
}
