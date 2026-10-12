"use client";

import { useEffect, useState, useRef, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { 
  getHealth, createCase, uploadDocument, processDocument, getCase, getCaseFacts, getFactEvidence, translateCase, API_BASE,
  type Health, type CaseOut, type FactResponse, type EvidenceResponse, type TranslatedText
} from "@/lib/api";
import { 
  FileUp, Loader2, Calendar, Pill, AlertTriangle, FileText, 
  X, Printer, Globe, ShieldAlert, Sparkles, Clock, Stethoscope, HeartHandshake,
  ChevronRight, Activity, AlertCircle, ShieldCheck, PhoneCall, Check, ExternalLink, Download, Lock
} from "lucide-react";

function HomeContent() {
  const searchParams = useSearchParams();
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeCase, setActiveCase] = useState<CaseOut | null>(null);
  const [facts, setFacts] = useState<FactResponse[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Translation state
  const [language, setLanguage] = useState<"en" | "hi" | "gu" | "mr" | "ta" | "te">("en");
  const [isTranslating, setIsTranslating] = useState(false);
  const [translations, setTranslations] = useState<Record<string, TranslatedText>>({});
  
  // Evidence popup state
  const [selectedFact, setSelectedFact] = useState<FactResponse | null>(null);
  const [evidence, setEvidence] = useState<EvidenceResponse[]>([]);
  const [isFetchingEvidence, setIsFetchingEvidence] = useState(false);

  // Helpline copy feedback state
  const [helplineCopied, setHelplineCopied] = useState(false);
  
  // Pre-upload consent gateway state
  const [showUploadConsentModal, setShowUploadConsentModal] = useState(false);
  const [consentAge, setConsentAge] = useState(false);
  const [consentPrivacy, setConsentPrivacy] = useState(false);
  const [hasSessionUploadConsent, setHasSessionUploadConsent] = useState(false);
  const [pendingFile, setPendingFile] = useState<File | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((e: Error) => setError(e.message));
  }, []);

  const handledActionRef = useRef<string | null>(null);

  // Common upload pipeline
  const uploadAndProcessFile = useCallback(async (file: File) => {
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
    }
  }, [activeCase]);

  // 1-Click Sample Hospital PDF loader
  const handleLoadSample = useCallback(async (
    samplePath: string = "/sample_medical_record.pdf", 
    filename: string = "sample_discharge_summary.pdf",
    targetSection?: string
  ) => {
    try {
      setIsUploading(true);
      setError(null);
      const res = await fetch(samplePath);
      const blob = await res.blob();
      const file = new File([blob], filename, { type: "application/pdf" });
      await uploadAndProcessFile(file);
      
      if (targetSection) {
        setTimeout(() => {
          const el = document.getElementById(targetSection);
          if (el) el.scrollIntoView({ behavior: "smooth" });
        }, 800);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load sample document");
      setIsUploading(false);
    }
  }, [uploadAndProcessFile]);

  // Handle custom events and URL parameters from Navbar / external links
  useEffect(() => {
    const handleUploadEvent = () => {
      if (hasSessionUploadConsent) {
        fileInputRef.current?.click();
      } else {
        setShowUploadConsentModal(true);
      }
    };

    const handleCarePlanEvent = () => {
      if (activeCase) {
        const el = document.getElementById("care-plan");
        if (el) el.scrollIntoView({ behavior: "smooth" });
      } else {
        handleLoadSample("/sample_medical_record.pdf", "sample_discharge_summary.pdf", "care-plan");
      }
    };

    const handlePrescriptionsEvent = () => {
      if (activeCase) {
        const el = document.getElementById("prescriptions");
        if (el) el.scrollIntoView({ behavior: "smooth" });
      } else {
        handleLoadSample("/sample_medical_record.pdf", "sample_discharge_summary.pdf", "prescriptions");
      }
    };

    window.addEventListener("carelynx:upload", handleUploadEvent);
    window.addEventListener("carelynx:careplan", handleCarePlanEvent);
    window.addEventListener("carelynx:prescriptions", handlePrescriptionsEvent);

    // Check URL params — once per action: this effect re-runs on every case update, and re-running
    // "demo" would upload the sample again in a loop.
    const action = searchParams.get("action");
    const isNewAction = action !== handledActionRef.current;
    handledActionRef.current = action;
    if (!isNewAction) {
      // already handled
    } else if (action === "upload") {
      if (hasSessionUploadConsent) {
        setTimeout(() => fileInputRef.current?.click(), 200);
      } else {
        setShowUploadConsentModal(true);
      }
    } else if (action === "demo") {
      handleLoadSample("/sample_medical_record.pdf", "sample_discharge_summary.pdf", "care-plan");
    } else if (action === "prescriptions") {
      handlePrescriptionsEvent();
    } else if (action === "care-plan") {
      handleCarePlanEvent();
    }

    return () => {
      window.removeEventListener("carelynx:upload", handleUploadEvent);
      window.removeEventListener("carelynx:careplan", handleCarePlanEvent);
      window.removeEventListener("carelynx:prescriptions", handlePrescriptionsEvent);
    };
  }, [activeCase, handleLoadSample, hasSessionUploadConsent, searchParams]);

  // Close popup modal on ESC key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (showUploadConsentModal) setShowUploadConsentModal(false);
        if (selectedFact) setSelectedFact(null);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedFact, showUploadConsentModal]);

  // Poll for case status during background processing
  useEffect(() => {
    if (!activeCase || !isProcessing) return;
    
    const interval = setInterval(async () => {
      try {
        const c = await getCase(activeCase.id);
        setActiveCase(c);
        
        const isStillProcessing = c.documents.some(
          d => d.processing_status === "PROCESSING" || d.processing_status === "UPLOADED"
        );
        
        if (!isStillProcessing) {
          setIsProcessing(false);
          const f = await getCaseFacts(c.id);
          setFacts(f);

          // Auto-translate summary upon completion if a non-English language is active
          if (language !== "en") {
            setIsTranslating(true);
            try {
              setTranslations(await translateCase(c.id, language));
            } catch (err) {
              console.error("Auto-translation on summary creation failed:", err);
            } finally {
              setIsTranslating(false);
            }
          }
        }
      } catch (err) {
        console.error(err);
      }
    }, 1200);
    
    return () => clearInterval(interval);
  }, [activeCase, isProcessing, language]);

  // Handle multilingual translation
  const handleLanguageChange = async (targetLang: "en" | "hi" | "gu" | "mr" | "ta" | "te") => {
    if (targetLang === "en") {
      setLanguage("en");
      return;
    }
    if (!activeCase) {
      await handleLoadSample("/sample_medical_record.pdf", "sample_discharge_summary.pdf");
      setLanguage(targetLang);
      return;
    }
    
    setIsTranslating(true);
    try {
      setTranslations(await translateCase(activeCase.id, targetLang));
      setLanguage(targetLang);
    } catch (err) {
      console.error(err);
    } finally {
      setIsTranslating(false);
    }
  };

  // Upload custom file with consent gateway check
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!hasSessionUploadConsent) {
      setPendingFile(file);
      setShowUploadConsentModal(true);
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }
    await uploadAndProcessFile(file);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const initiateUploadClick = () => {
    if (hasSessionUploadConsent) {
      fileInputRef.current?.click();
    } else {
      setShowUploadConsentModal(true);
    }
  };

  const handleConfirmUploadConsent = async () => {
    if (!consentAge || !consentPrivacy) return;
    setHasSessionUploadConsent(true);
    setShowUploadConsentModal(false);
    if (pendingFile) {
      const f = pendingFile;
      setPendingFile(null);
      await uploadAndProcessFile(f);
    } else {
      fileInputRef.current?.click();
    }
  };

  const copyHelplineNumber = () => {
    navigator.clipboard.writeText("1800-CARELYNX");
    setHelplineCopied(true);
    setTimeout(() => setHelplineCopied(false), 2500);
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

  const getFactTitle = (fact: FactResponse): string => {
    const tr = language !== "en" ? translations[fact.id] : undefined;
    if (tr) return [tr.title, tr.subtitle, tr.date].filter(Boolean).join(" — ");
    const val = fact.value || {};
    const sanitize = (s: string) => s.replace(/^["'“”„\s:.-]+|["'“”„\s:.-]+$/g, "").trim();

    switch (fact.fact_type) {
      case "encounter_date": {
        const kind = String(val.kind || "");
        const kindLabel = kind === "admission" ? "Hospital Admission" : kind === "discharge" ? "Hospital Discharge" : "Encounter";
        const dateStr = String(val.date || val.raw_text || "");
        return `${kindLabel}: ${dateStr}`;
      }
      case "follow_up": {
        const raw = sanitize(String(val.raw_text || ""));
        const date = String(val.date || "");
        const provider = sanitize(String(val.provider || ""));
        const dept = sanitize(String(val.department || ""));
        if (dept && provider) return `${dept} Follow-up with ${provider}`;
        if (provider) return `Follow-up with ${provider}`;
        if (dept) return `${dept} Follow-up`;
        if (date) return `Follow-up Visit (${date})`;
        return raw || "Scheduled Follow-up Appointment";
      }
      case "medication": {
        const name = sanitize(String(val.name || "Medication"));
        const strength = val.strength ? sanitize(String(val.strength)) : "";
        const freq = val.frequency ? sanitize(String(val.frequency)) : "";
        const details = [strength, freq].filter(Boolean).join(" • ");
        return `${name} ${details ? "— " + details : ""}`;
      }
      case "warning_sign": return sanitize(String(val.text || "Warning sign"));
      case "documented_condition": return sanitize(String(val.text || "Condition"));
      case "allergy": return `Allergy: ${sanitize(String(val.substance || "Substance"))}`;
      case "instruction": return sanitize(String(val.text || "Care Instruction"));
      default: return sanitize(String(fact.fact_type));
    }
  };

  // Categorize facts
  const warnings = facts.filter(f => f.fact_type === "warning_sign" && f.status !== "REJECTED");
  const medications = facts.filter(f => f.fact_type === "medication" && f.status !== "REJECTED");
  const appointments = facts.filter(f => f.fact_type === "follow_up" && f.status !== "REJECTED");
  const instructions = facts.filter(f => (f.fact_type === "instruction" || f.fact_type === "documented_condition" || f.fact_type === "encounter_date") && f.status !== "REJECTED");

  return (
    <div className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-12">
      {/* Global Error Banner */}
      {error && (
        <div className="p-4 border border-rose-200 bg-rose-50 text-rose-800 rounded-2xl text-sm flex items-start gap-3 shadow-xs no-print fade-in">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold text-rose-900">Processing Notification</p>
            <p className="text-xs text-rose-700 mt-0.5">{error}</p>
          </div>
          <button onClick={() => setError(null)} className="text-rose-500 hover:text-rose-700 p-1 cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main View: Landing Hero OR Active Case Care Plan */}
      {!activeCase ? (
        <div className="flex flex-col gap-16" id="hero">
          {/* Hero Section */}
          <section className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center pt-4 sm:pt-8 pb-4">
            {/* Left Hero Content */}
            <div className="lg:col-span-7 flex flex-col gap-6">
              <div>
                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-slate-900 leading-[1.15]">
                  A clear, evidence-linked <br className="hidden sm:inline" />
                  <span className="text-brand font-extrabold">discharge companion</span> <br className="hidden sm:inline" />
                  for every patient
                </h1>
                <p className="mt-5 text-slate-600 text-base sm:text-lg leading-relaxed max-w-xl">
                  Supporting your post-hospital recovery with AI-guided fact extraction, verified medication schedules, clinical warnings, and safe multilingual translation. 100% grounded in source paperwork.
                </p>
              </div>

              {/* Action Buttons Group */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <input 
                  type="file" 
                  className="hidden" 
                  onChange={handleFileUpload}
                  disabled={isUploading || isProcessing}
                  ref={fileInputRef}
                  accept="application/pdf,image/jpeg,image/png"
                />
                
                {/* 1. Royal Blue Button */}
                <button
                  onClick={initiateUploadClick}
                  disabled={isUploading || isProcessing}
                  className="px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-bold text-sm shadow-md shadow-blue-500/20 transition-all flex items-center gap-2 cursor-pointer focus-visible:outline-2 focus-visible:outline-blue-600 focus-visible:outline-offset-2"
                  id="hero-btn-upload"
                  aria-label="Upload patient paperwork"
                >
                  {isUploading ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <FileUp className="w-4 h-4" aria-hidden="true" />}
                  <span>Upload Paperwork</span>
                </button>

                {/* 2. Vibrant Mint Green Button */}
                <button
                  onClick={() => handleLoadSample("/sample_medical_record.pdf", "sample_discharge_summary.pdf", "care-plan")}
                  disabled={isUploading || isProcessing}
                  className="px-6 py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white font-bold text-sm shadow-md shadow-emerald-500/20 transition-all flex items-center gap-2 cursor-pointer"
                  id="hero-btn-demo"
                >
                  {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                  <span>Demo Hospital Report</span>
                </button>

                {/* 3. Soft Sky Button with Deep Navy Contrast */}
                <button
                  onClick={() => handleLoadSample("/sample_conflicting_prescription.pdf", "sample_conflicting_prescription.pdf")}
                  disabled={isUploading || isProcessing}
                  className="px-5 py-3.5 rounded-xl bg-sky-100 hover:bg-sky-200 text-sky-950 font-bold text-sm border border-sky-300 transition-all flex items-center gap-2 shadow-xs cursor-pointer"
                  id="hero-btn-conflict"
                >
                  <AlertTriangle className="w-4 h-4 text-sky-800" />
                  <span>Test Conflict</span>
                </button>

                {/* 4. Emergency Crimson Button */}
                <a
                  href="/review"
                  className="px-5 py-3.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-sm shadow-md shadow-rose-500/20 transition-all flex items-center gap-2 cursor-pointer"
                  id="hero-btn-emergency"
                >
                  <ShieldAlert className="w-4 h-4" />
                  <span>Clinical Queue</span>
                </a>
              </div>

              {/* Interactive 24/7 Helpline Pill */}
              <div className="pt-2 flex items-center gap-3">
                <a
                  href="tel:1800227359"
                  onClick={(e) => {
                    if (!("ontouchstart" in window)) {
                      e.preventDefault();
                      copyHelplineNumber();
                    }
                  }}
                  className="inline-flex items-center gap-2.5 px-4 py-2.5 rounded-full bg-white/95 border border-slate-300 text-xs text-slate-800 shadow-xs hover:border-emerald-500 transition-colors backdrop-blur-md group cursor-pointer"
                  title="Click to call or copy helpline number"
                >
                  <span className="w-2 h-2 rounded-full bg-rose-600 animate-pulse shrink-0" />
                  <span className="font-bold text-slate-900 flex items-center gap-1.5">
                    <PhoneCall className="w-3.5 h-3.5 text-rose-600" />
                    Carelynx Patient Helpline:
                  </span>
                  <span className="font-mono text-slate-700 font-semibold">1800-CARELYNX</span>
                  <span className="text-[11px] text-brand font-semibold hidden sm:inline">
                    {helplineCopied ? "✓ Copied!" : "(24/7 Support)"}
                  </span>
                </a>
              </div>
            </div>

            {/* Right Hero Feature Showcase Card */}
            <div className="lg:col-span-5 flex justify-center">
              <div className="w-full max-w-md bg-gradient-to-br from-emerald-100/60 via-teal-50/70 to-sky-100/50 rounded-3xl p-8 border border-emerald-200/60 shadow-xl shadow-emerald-500/5 flex flex-col items-center justify-center text-center relative overflow-hidden">
                <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-md px-3 py-1 rounded-full text-[11px] font-semibold text-emerald-800 border border-emerald-100 shadow-xs flex items-center gap-1">
                  <HeartHandshake className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Safe Space</span>
                </div>
                
                <div className="w-24 h-24 rounded-full bg-white/90 shadow-md border border-emerald-100 flex items-center justify-center text-brand mb-6">
                  <ShieldCheck className="w-12 h-12 text-brand" />
                </div>

                <h3 className="text-xl font-bold text-slate-900 mb-1">
                  100% Verifiable Evidence
                </h3>
                <p className="text-xs text-slate-600 max-w-xs mb-6 leading-relaxed">
                  Every dosage, recovery step, and warning is grounded in verbatim source quotes from your paperwork.
                </p>

                <div className="flex flex-wrap justify-center gap-2">
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-white/80 text-slate-700 border border-slate-200/60 shadow-xs">
                    Confidential
                  </span>
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-white/80 text-slate-700 border border-slate-200/60 shadow-xs">
                    Accessible
                  </span>
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-white/80 text-slate-700 border border-slate-200/60 shadow-xs">
                    Supportive
                  </span>
                </div>
              </div>
            </div>
          </section>

          {/* Complete Feature Suite Grid */}
          <section className="flex flex-col gap-10" id="features">
            <div className="text-center max-w-2xl mx-auto">
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
                Complete Discharge Care Navigation
              </h2>
              <p className="text-sm sm:text-base text-slate-600 mt-2">
                Integrated features designed to provide comprehensive, accessible, and error-free post-discharge support for patients and caregivers.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Feature 1: AI Fact Extraction */}
              <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 border border-slate-200/70 shadow-xs hover:shadow-md hover:border-emerald-200 transition-all flex flex-col justify-between gap-6 group">
                <div className="flex flex-col gap-4">
                  <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                    <Sparkles className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-slate-900 mb-1.5">
                      AI-Guided Fact Extraction
                    </h3>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      Converts unstructured hospital records into clean, categorized patient action items without hallucinating clinical facts.
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => handleLoadSample("/sample_medical_record.pdf", "sample_discharge_summary.pdf", "care-plan")}
                  className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 flex items-center gap-1 self-start cursor-pointer"
                >
                  <span>Try Demo Report</span>
                  <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </button>
              </div>

              {/* Feature 2: Medication Schedules */}
              <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 border border-slate-200/70 shadow-xs hover:shadow-md hover:border-sky-200 transition-all flex flex-col justify-between gap-6 group">
                <div className="flex flex-col gap-4">
                  <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center">
                    <Pill className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-slate-900 mb-1.5">
                      Prescription Schedule Tracker
                    </h3>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      Structured medication schedules with exact dosages, intake timings, and food restrictions preserved word-for-word.
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => handleLoadSample("/sample_medical_record.pdf", "sample_discharge_summary.pdf", "prescriptions")}
                  className="text-xs font-semibold text-sky-700 hover:text-sky-800 flex items-center gap-1 self-start cursor-pointer"
                >
                  <span>View Medication Schedule</span>
                  <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </button>
              </div>

              {/* Feature 3: Appointment Tracker */}
              <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 border border-slate-200/70 shadow-xs hover:shadow-md hover:border-purple-200 transition-all flex flex-col justify-between gap-6 group">
                <div className="flex flex-col gap-4">
                  <div className="w-10 h-10 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
                    <Calendar className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-slate-900 mb-1.5">
                      Follow-up Visit Timeline
                    </h3>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      Clear chronological timeline of upcoming specialist consultations, wound checks, and diagnostic lab dates.
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => handleLoadSample("/sample_medical_record.pdf", "sample_discharge_summary.pdf", "appointments")}
                  className="text-xs font-semibold text-purple-700 hover:text-purple-800 flex items-center gap-1 self-start cursor-pointer"
                >
                  <span>View Appointment Timeline</span>
                  <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </button>
              </div>

              {/* Feature 4: Conflict Guard */}
              <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 border border-slate-200/70 shadow-xs hover:shadow-md hover:border-rose-200 transition-all flex flex-col justify-between gap-6 group">
                <div className="flex flex-col gap-4">
                  <div className="w-10 h-10 rounded-xl bg-rose-100 text-rose-700 flex items-center justify-center">
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-slate-900 mb-1.5">
                      Multi-Document Conflict Guard
                    </h3>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      Catches conflicting follow-up dates or differing prescriptions across multiple paperwork pages without guessing.
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => handleLoadSample("/sample_conflicting_prescription.pdf", "sample_conflicting_prescription.pdf")}
                  className="text-xs font-semibold text-rose-700 hover:text-rose-800 flex items-center gap-1 self-start cursor-pointer"
                >
                  <span>Test Conflict Demo</span>
                  <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </button>
              </div>

              {/* Feature 5: Multilingual Care */}
              <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 border border-slate-200/70 shadow-xs hover:shadow-md hover:border-teal-200 transition-all flex flex-col justify-between gap-6 group">
                <div className="flex flex-col gap-4">
                  <div className="w-10 h-10 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center">
                    <Globe className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-slate-900 mb-1.5">
                      Source-Preserving Translation
                    </h3>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      Instant Google translation to Hindi, Gujarati, Marathi, Tamil, and Telugu while locking drug names, dosages, and dates.
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => handleLanguageChange("hi")}
                  className="text-xs font-semibold text-teal-700 hover:text-teal-800 flex items-center gap-1 self-start cursor-pointer"
                >
                  <span>Try Hindi / Regional Mode</span>
                  <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </button>
              </div>

              {/* Feature 6: Clinical Audit Hub */}
              <div className="bg-white/80 backdrop-blur-md rounded-2xl p-6 border border-slate-200/70 shadow-xs hover:shadow-md hover:border-indigo-200 transition-all flex flex-col justify-between gap-6 group">
                <div className="flex flex-col gap-4">
                  <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center">
                    <Stethoscope className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-slate-900 mb-1.5">
                      Clinical Reviewer Workspace
                    </h3>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      Side-by-side evidence comparator allowing authorized healthcare staff to audit and resolve flagged ambiguities.
                    </p>
                  </div>
                </div>
                <a 
                  href="/review"
                  className="text-xs font-semibold text-indigo-700 hover:text-indigo-800 flex items-center gap-1 self-start cursor-pointer"
                >
                  <span>Open Audit Queue</span>
                  <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </a>
              </div>
            </div>

            {/* Bottom Stats Banner */}
            <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 border border-slate-200/80 shadow-xs grid grid-cols-1 sm:grid-cols-3 gap-6 text-center divide-y sm:divide-y-0 sm:divide-x divide-slate-100">
              <div className="flex flex-col items-center justify-center pt-2 sm:pt-0">
                <span className="text-3xl font-extrabold text-slate-900">24/7</span>
                <span className="text-xs font-medium text-slate-500 mt-1">Available Care Plan</span>
              </div>
              <div className="flex flex-col items-center justify-center pt-2 sm:pt-0">
                <span className="text-3xl font-extrabold text-brand">100%</span>
                <span className="text-xs font-medium text-slate-500 mt-1">Verbatim Evidence Grounded</span>
              </div>
              <div className="flex flex-col items-center justify-center pt-2 sm:pt-0">
                <span className="text-3xl font-extrabold text-slate-900">6</span>
                <span className="text-xs font-medium text-slate-500 mt-1">Regional Languages (EN, HI, GU, MR, TA, TE)</span>
              </div>
            </div>
          </section>
        </div>
      ) : (
        /* Active Case Document Navigator */
        <div className="flex flex-col gap-8 fade-in" id="care-plan">
          {/* Active Case Top Control Bar */}
          <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 border border-slate-200/80 shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-900 border border-emerald-200">
                  {activeCase.status}
                </span>
                <span className="text-slate-600 text-xs font-mono font-medium">Case #{activeCase.id.substring(0, 8)}</span>
                {isProcessing && (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-900 border border-amber-200 flex items-center gap-1">
                    <Loader2 className="w-3 h-3 animate-spin text-amber-700" /> Processing
                  </span>
                )}
              </div>
              <h2 className="text-2xl font-bold text-slate-900">Your Discharge Care Plan</h2>
              <p className="text-xs text-slate-600 mt-0.5 font-medium">
                Extracted from {activeCase.documents.length} document{activeCase.documents.length === 1 ? '' : 's'}. Items marked for review are not yet confirmed.
              </p>
              {language !== "en" && !isTranslating && Object.keys(translations).length === 0 && facts.some(f => f.status === "VERIFIED") && (
                <p role="status" className="text-xs text-amber-800 mt-1 font-medium">{TRANSLATION_UNAVAILABLE[language]}</p>
              )}
            </div>

            {/* Language Switcher and Action Pills */}
            <div className="flex flex-wrap items-center gap-3 no-print">
              {/* Language Selector Pill */}
              <div className="flex items-center bg-slate-100 rounded-full p-1 border border-slate-200 text-xs font-medium">
                <Globe className="w-3.5 h-3.5 text-slate-600 ml-2 mr-1" />
                <button 
                  onClick={() => handleLanguageChange("en")} 
                  className={`px-3 py-1 rounded-full transition-all cursor-pointer ${language === 'en' ? 'bg-brand text-white shadow-xs font-bold' : 'text-slate-700 hover:text-slate-900 font-semibold'}`}
                >
                  English
                </button>
                <button 
                  onClick={() => handleLanguageChange("hi")} 
                  disabled={isTranslating} 
                  className={`px-3 py-1 rounded-full transition-all cursor-pointer ${language === 'hi' ? 'bg-brand text-white shadow-xs font-bold' : 'text-slate-700 hover:text-slate-900 font-semibold'}`}
                >
                  हिन्दी
                </button>
                <button 
                  onClick={() => handleLanguageChange("gu")} 
                  disabled={isTranslating} 
                  className={`px-3 py-1 rounded-full transition-all cursor-pointer ${language === 'gu' ? 'bg-brand text-white shadow-xs font-bold' : 'text-slate-700 hover:text-slate-900 font-semibold'}`}
                >
                  ગુજરાતી
                </button>
                <button 
                  onClick={() => handleLanguageChange("mr")} 
                  disabled={isTranslating} 
                  className={`px-3 py-1 rounded-full transition-all ${language === 'mr' ? 'bg-brand text-white shadow-xs font-bold' : 'text-slate-700 hover:text-slate-900 font-semibold'}`}
                >
                  मराठी
                </button>
                <button 
                  onClick={() => handleLanguageChange("ta")} 
                  disabled={isTranslating} 
                  className={`px-3 py-1 rounded-full transition-all ${language === 'ta' ? 'bg-brand text-white shadow-xs font-bold' : 'text-slate-700 hover:text-slate-900 font-semibold'}`}
                >
                  தமிழ்
                </button>
                <button 
                  onClick={() => handleLanguageChange("te")} 
                  disabled={isTranslating} 
                  className={`px-3 py-1 rounded-full transition-all ${language === 'te' ? 'bg-brand text-white shadow-xs font-bold' : 'text-slate-700 hover:text-slate-900 font-semibold'}`}
                >
                  తెలుగు
                </button>
                {isTranslating && <Loader2 className="w-3 h-3 animate-spin text-brand ml-1 mr-2" />}
              </div>

              <button
                onClick={() => window.print()}
                className="px-4 py-2 rounded-full bg-white hover:bg-slate-50 border border-slate-300 text-slate-800 text-xs font-bold shadow-xs transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <Printer className="w-3.5 h-3.5 text-slate-700" />
                <span>Print Plan</span>
              </button>

              {/* Voice Accessibility (Phase 2) */}
              <button
                onClick={() => {
                  const synth = window.speechSynthesis;
                  synth.cancel(); // a second click restarts instead of queueing
                  const bcp47 = SPEECH_LANG[language];
                  const voice = synth.getVoices().find(v => v.lang.replace("_", "-").toLowerCase().startsWith(bcp47.split("-")[0]));
                  if (!voice && language !== "en") {
                    alert(`Your browser has no ${bcp47} voice installed, so it cannot read this language aloud.`);
                    return;
                  }
                  const speech = new SpeechSynthesisUtterance(READ_ALOUD_INTRO[language] + " " + facts.filter(f => f.status === "VERIFIED").map(f => getFactTitle(f)).join(". "));
                  speech.lang = bcp47;
                  if (voice) speech.voice = voice;
                  synth.speak(speech);
                }}
                className="px-4 py-2 rounded-full bg-white hover:bg-slate-50 border border-slate-300 text-slate-800 text-xs font-bold shadow-xs transition-colors flex items-center gap-1.5"
                title="Read Aloud (Voice Accessibility)"
              >
                <span>Read Aloud</span>
              </button>

              <button
                onClick={() => { 
                  setActiveCase(null); 
                  setFacts([]);
                  window.scrollTo({ top: 0, behavior: "smooth" });
                }}
                className="px-4 py-2 rounded-full bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-800 text-xs font-bold transition-colors cursor-pointer"
              >
                New Encounter
              </button>
            </div>
          </div>

          {/* Attached Files Strip */}
          <div className="flex items-center gap-3 overflow-x-auto pb-1 no-print">
            <span className="text-xs font-bold text-slate-600 uppercase tracking-wider shrink-0">Attached Files:</span>
            {activeCase.documents.map(doc => (
              <a
                key={doc.id}
                href={`${API_BASE}/documents/${doc.id}/file`}
                target="_blank"
                rel="noreferrer"
                title="Click to view original source document"
                className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white hover:bg-slate-50 border border-slate-300 hover:border-emerald-500 text-xs shrink-0 shadow-xs transition-colors group cursor-pointer"
              >
                <FileText className="w-3.5 h-3.5 text-brand" />
                <span className="font-mono text-slate-900 font-semibold">{doc.filename}</span>
                <span className="text-slate-600 text-[11px] capitalize font-medium">• {doc.processing_status.toLowerCase()}</span>
                <ExternalLink className="w-3 h-3 text-slate-400 group-hover:text-emerald-600 ml-0.5" />
              </a>
            ))}
          </div>

          {/* Red-Flag Conflict Warning Banner (if any) */}
          {facts.some(f => f.status === "CONFLICT_DETECTED") && (
            <div className="p-5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-900 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xs no-print">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-xl bg-rose-100 text-rose-700 flex items-center justify-center shrink-0">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-rose-900">Clinical Conflict Detected Across Documents</h4>
                  <p className="text-xs text-rose-700 leading-relaxed mt-0.5">
                    Your paperwork contains contradictory dates or prescriptions. CARELYNX does not guess which one is correct. These have been flagged for human clinician review.
                  </p>
                </div>
              </div>
              <a
                href="/review"
                className="px-4 py-2 rounded-full bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold whitespace-nowrap shadow-xs transition-colors cursor-pointer"
              >
                View in Review Queue →
              </a>
            </div>
          )}

          {/* Care Plan Categorized Sections */}
          {facts.length === 0 && isProcessing ? (
            <div className="py-24 bg-white/60 rounded-3xl border border-slate-200 flex flex-col items-center justify-center text-center">
              <Loader2 className="w-8 h-8 text-brand animate-spin mb-3" />
              <p className="text-base font-bold text-slate-900">Extracting & verifying clinical facts...</p>
              <p className="text-xs text-slate-500 mt-1">Grounding instructions against verbatim source sentences</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* 1. Critical Warnings & Precautions */}
              {warnings.length > 0 && (
                <section className="col-span-1 lg:col-span-2 p-6 rounded-3xl bg-rose-50/70 border border-rose-200/80 flex flex-col gap-4 shadow-xs" id="warnings">
                  <div className="flex items-center gap-2.5 border-b border-rose-200 pb-3">
                    <div className="w-8 h-8 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center">
                      <AlertTriangle className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="font-bold text-base text-rose-950">Emergency Warning Signs & Red Flags</h3>
                      <p className="text-xs text-rose-700">Seek immediate medical care if you experience any of the following</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {warnings.map(f => (
                      <div 
                        key={f.id} 
                        onClick={() => viewEvidence(f)}
                        className="p-4 rounded-2xl bg-white border border-rose-200 hover:border-rose-400 cursor-pointer transition-all flex flex-col justify-between gap-3 shadow-xs group"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-xs font-semibold text-rose-900 leading-relaxed">
                            {getFactTitle(f)}
                          </p>
                          <ChevronRight className="w-4 h-4 text-rose-400 group-hover:translate-x-0.5 transition-transform shrink-0" />
                        </div>
                        <div className="flex items-center justify-between text-[11px] text-rose-600 pt-2 border-t border-rose-100">
                          <StatusBadge status={f.status} lang={language} />
                          <span className="font-semibold underline decoration-rose-300">View Source Proof →</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* 2. Upcoming Follow-up Appointments */}
              <section className="p-6 rounded-3xl bg-white/80 backdrop-blur-md border border-slate-200/80 flex flex-col gap-4 shadow-xs" id="appointments">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
                      <Calendar className="w-4 h-4" />
                    </div>
                    <h3 className="font-bold text-base text-slate-900">Follow-up Appointments</h3>
                  </div>
                  <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full">{appointments.length} scheduled</span>
                </div>

                {appointments.length === 0 ? (
                  <p className="text-xs text-slate-500 py-4">No follow-up dates extracted from uploaded pages.</p>
                ) : (
                  <div className="flex flex-col gap-3">
                    {appointments.map(f => (
                      <div 
                        key={f.id} 
                        onClick={() => viewEvidence(f)}
                        className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-3 group ${
                          f.status === "CONFLICT_DETECTED" 
                            ? "bg-rose-50 border-rose-300 hover:bg-rose-100/50" 
                            : "bg-white hover:bg-slate-50 border-slate-200 shadow-xs"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-xl bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-700 shrink-0">
                            <Clock className="w-5 h-5" />
                          </div>
                          <div>
                            <span className="text-xs font-bold text-slate-900 block">
                              {getFactTitle(f)}
                            </span>
                            <span className="text-[11px] text-slate-500 block mt-0.5">
                              Clinical Follow-up Visit
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <StatusBadge status={f.status} lang={language} />
                          <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              {/* 3. Prescription Medications */}
              <section className="p-6 rounded-3xl bg-white/80 backdrop-blur-md border border-slate-200/80 flex flex-col gap-4 shadow-xs" id="prescriptions">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center">
                      <Pill className="w-4 h-4" />
                    </div>
                    <h3 className="font-bold text-base text-slate-900">Prescribed Medications</h3>
                  </div>
                  <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full">{medications.length} active</span>
                </div>

                {medications.length === 0 ? (
                  <p className="text-xs text-slate-500 py-4">No discharge prescriptions identified.</p>
                ) : (
                  <div className="flex flex-col gap-3">
                    {medications.map(f => {
                      const val = f.value || {};
                      const tr = language !== "en" ? translations[f.id] : undefined;
                      return (
                        <div 
                          key={f.id} 
                          onClick={() => viewEvidence(f)}
                          className={`p-4 rounded-2xl border transition-all cursor-pointer flex flex-col gap-2 group ${
                            f.status === "CONFLICT_DETECTED" 
                              ? "bg-rose-50 border-rose-300 hover:bg-rose-100/50" 
                              : "bg-white hover:bg-slate-50 border-slate-200 shadow-xs"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                              <Pill className="w-3.5 h-3.5 text-brand" />
                              {String(val.name || getFactTitle(f))}
                            </span>
                            <span className="flex items-center gap-1.5">
                              {Boolean(val.strength) && (
                                <span className="text-[11px] font-mono font-semibold text-emerald-800 px-2.5 py-0.5 rounded-full bg-emerald-100">
                                  {String(val.strength)}
                                </span>
                              )}
                              <StatusBadge status={f.status} lang={language} />
                            </span>
                          </div>

                          <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                            <span>{tr?.subtitle || (val.frequency ? `Instructions: ${String(val.frequency)}` : "")}</span>
                            <span className="font-semibold text-brand underline decoration-emerald-200 group-hover:decoration-brand">Proof →</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>

              {/* 4. Home Care & Recovery Instructions */}
              <section className="col-span-1 lg:col-span-2 p-6 rounded-3xl bg-white/80 backdrop-blur-md border border-slate-200/80 flex flex-col gap-4 shadow-xs" id="instructions">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center">
                      <Activity className="w-4 h-4" />
                    </div>
                    <h3 className="font-bold text-base text-slate-900">Home Care & Daily Instructions</h3>
                  </div>
                  <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full">{instructions.length} guidelines</span>
                </div>

                {instructions.length === 0 ? (
                  <p className="text-xs text-slate-500 py-4">No specific home instructions extracted.</p>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {instructions.map(f => (
                      <div 
                        key={f.id} 
                        onClick={() => viewEvidence(f)}
                        className="p-4 rounded-2xl bg-white hover:bg-slate-50 border border-slate-200 cursor-pointer transition-all flex flex-col justify-between gap-3 shadow-xs group"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-xs font-medium text-slate-800 leading-relaxed">
                            {getFactTitle(f)}
                          </p>
                          <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform shrink-0" />
                        </div>
                        <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-100">
                          <StatusBadge status={f.status} lang={language} />
                          <span className="font-semibold text-brand underline decoration-emerald-200">View Proof →</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </div>
          )}
        </div>
      )}

      {/* Floating Centered Verbatim Evidence Modal Pop-Up */}
      {selectedFact && (
        <div 
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-md z-50 flex items-center justify-center p-4 sm:p-6 no-print animate-in fade-in duration-150"
          onClick={() => setSelectedFact(null)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="evidence-modal-title"
        >
          <div 
            className="w-full max-w-xl max-h-[85vh] rounded-3xl bg-white border border-slate-200 shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-150"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/60">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h2 id="evidence-modal-title" className="text-base font-bold text-slate-900">Verbatim Source Proof</h2>
                  <p className="text-[11px] text-slate-500">Grounding verification from original hospital paperwork</p>
                </div>
              </div>
              <button 
                onClick={() => setSelectedFact(null)} 
                className="p-1.5 rounded-full bg-white hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors border border-slate-200 cursor-pointer"
                aria-label="Close evidence popup"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Scrollable Body */}
            <div className="p-6 overflow-y-auto flex flex-col gap-5 custom-scrollbar">
              {/* Fact Summary */}
              <div>
                <span className="text-[11px] text-slate-700 uppercase tracking-wider font-bold">Extracted Clinical Fact</span>
                <div className="mt-1.5 p-3.5 rounded-2xl bg-slate-50 border border-slate-300 text-sm font-bold text-slate-900 shadow-xs">
                  {getFactTitle(selectedFact)}
                </div>

                {/* Status Badge */}
                <div className="mt-2.5 flex items-center gap-2">
                  <StatusBadge status={selectedFact.status} lang={language} />
                </div>

                {selectedFact.status_reasons && selectedFact.status_reasons.length > 0 && (
                  <div className="mt-3 p-3.5 bg-amber-50 border border-amber-300 rounded-2xl text-xs text-amber-950">
                    <span className="font-bold text-amber-900 block mb-1">Status Rationale:</span>
                    <ul className="list-disc list-inside space-y-1 text-amber-900 font-medium">
                      {selectedFact.status_reasons.map((r, i) => <li key={i}>{r}</li>)}
                    </ul>
                  </div>
                )}
              </div>

              {/* Source Document Citations */}
              <div className="flex flex-col gap-3">
                <span className="text-[11px] text-slate-700 uppercase tracking-wider font-bold">Exact Excerpt in Source Paperwork</span>
                
                {isFetchingEvidence ? (
                  <div className="p-8 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-brand" /></div>
                ) : evidence.length > 0 ? (
                  evidence.map(ev => {
                    const doc = activeCase?.documents.find(d => d.id === ev.document_id);
                    return (
                      <div key={ev.id} className="p-4 rounded-2xl bg-slate-50 border border-slate-300 flex flex-col gap-3 shadow-xs">
                        <div className="flex items-center justify-between text-xs text-slate-700 border-b border-slate-200 pb-2">
                          <span className="font-mono font-bold text-slate-900 truncate max-w-[240px]">{doc?.filename || "Medical Document"}</span>
                          <span className="px-2.5 py-0.5 rounded-full bg-white border border-slate-300 text-slate-800 font-mono text-[11px] font-semibold">Page {ev.page_number}</span>
                        </div>

                        {ev.snippet ? (
                          <div className="p-3.5 bg-amber-50 border-l-4 border-amber-500 rounded-r-xl text-xs leading-relaxed italic text-slate-900 font-medium select-text">
                            &quot;{ev.snippet}&quot;
                          </div>
                        ) : (
                          <p className="text-xs text-amber-900 italic font-medium">No direct excerpt captured.</p>
                        )}
                      </div>
                    );
                  })
                ) : (
                  <p className="text-xs text-slate-600 text-center p-4 font-medium">No evidence citations linked.</p>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-slate-100 bg-slate-50/60 flex justify-end">
              <button
                onClick={() => setSelectedFact(null)}
                className="px-5 py-2 rounded-full bg-brand hover:bg-brand-light text-white text-xs font-semibold transition-colors shadow-xs cursor-pointer"
              >
                Close Proof
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Pre-Upload Health Data Privacy & Legal Consent Gateway Modal */}
      {showUploadConsentModal && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="upload-consent-title"
          aria-describedby="upload-consent-desc"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn"
          onClick={() => setShowUploadConsentModal(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-xl bg-white border border-slate-200 rounded-3xl shadow-2xl p-6 sm:p-8 flex flex-col gap-6 text-slate-900 max-h-[90vh] overflow-y-auto custom-scrollbar"
          >
            {/* Modal Header */}
            <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center shrink-0">
                  <Lock className="w-5 h-5 text-emerald-700" aria-hidden="true" />
                </div>
                <div>
                  <h2 id="upload-consent-title" className="text-lg font-bold text-slate-900">
                    Patient Paperwork Privacy & Consent
                  </h2>
                  <p id="upload-consent-desc" className="text-xs text-slate-500">
                    Required active consent under GDPR, CCPA, and HIPAA guidelines
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowUploadConsentModal(false)}
                className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer focus-visible:outline-2 focus-visible:outline-emerald-600"
                aria-label="Close upload consent dialog"
              >
                <X className="w-5 h-5" aria-hidden="true" />
              </button>
            </div>

            {/* Safeguards Summary */}
            <div className="flex flex-col gap-2.5 text-xs text-slate-600 leading-relaxed bg-slate-50 p-4 rounded-2xl border border-slate-200">
              <div className="flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <strong className="text-slate-900">Isolated & Private Processing:</strong> Your discharge paperwork is stored securely under randomized UUID keys and never exposed to public directories.
                </div>
              </div>
              <div className="flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <strong className="text-slate-900">Zero Commercial Model Training:</strong> Your clinical paperwork is never ingested or shared to train public commercial AI models.
                </div>
              </div>
              <div className="flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <strong className="text-slate-900">Data Minimization:</strong> Only clinical instructions, follow-ups, and medications from the document are extracted.
                </div>
              </div>
            </div>

            {/* Unchecked Active Opt-in Checkboxes */}
            <div className="flex flex-col gap-3.5">
              <div className="flex items-start gap-3 p-3.5 rounded-xl border border-slate-200 hover:bg-slate-50 transition-colors">
                <input
                  id="consent-age-check"
                  type="checkbox"
                  checked={consentAge}
                  onChange={(e) => setConsentAge(e.target.checked)}
                  className="w-4 h-4 mt-0.5 rounded border-slate-300 text-emerald-600 focus-visible:outline-2 focus-visible:outline-emerald-600 shrink-0 cursor-pointer"
                />
                <label htmlFor="consent-age-check" className="text-xs text-slate-800 leading-relaxed cursor-pointer">
                  <strong>Age & Authority Attestation:</strong> I confirm that I am at least 18 years old, or the legally authorized parent, guardian, or primary caregiver of the patient.
                </label>
              </div>

              <div className="flex items-start gap-3 p-3.5 rounded-xl border border-slate-200 hover:bg-slate-50 transition-colors">
                <input
                  id="consent-privacy-check"
                  type="checkbox"
                  checked={consentPrivacy}
                  onChange={(e) => setConsentPrivacy(e.target.checked)}
                  className="w-4 h-4 mt-0.5 rounded border-slate-300 text-emerald-600 focus-visible:outline-2 focus-visible:outline-emerald-600 shrink-0 cursor-pointer"
                />
                <label htmlFor="consent-privacy-check" className="text-xs text-slate-800 leading-relaxed cursor-pointer">
                  <strong>Health Data Processing Consent:</strong> I grant explicit consent to extract and translate discharge directions from this paperwork in accordance with the{" "}
                  <a href="/privacy" target="_blank" rel="noopener noreferrer" className="text-emerald-700 underline font-semibold">
                    Privacy Policy
                  </a>{" "}
                  and{" "}
                  <a href="/terms" target="_blank" rel="noopener noreferrer" className="text-emerald-700 underline font-semibold">
                    Terms of Service
                  </a>.
                </label>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex flex-col sm:flex-row items-center justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowUploadConsentModal(false)}
                className="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-100 text-slate-700 font-semibold text-xs transition-colors cursor-pointer focus-visible:outline-2 focus-visible:outline-emerald-600"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!consentAge || !consentPrivacy}
                onClick={handleConfirmUploadConsent}
                className={`w-full sm:w-auto px-6 py-2.5 rounded-xl font-bold text-xs shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer focus-visible:outline-2 focus-visible:outline-emerald-600 ${
                  consentAge && consentPrivacy
                    ? "bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/20"
                    : "bg-slate-200 text-slate-400 cursor-not-allowed shadow-none"
                }`}
                id="btn-confirm-upload-consent"
              >
                <Check className="w-4 h-4" aria-hidden="true" />
                <span>Agree & Select Document</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Home() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex items-center justify-center p-12">
        <Loader2 className="w-8 h-8 animate-spin text-brand" />
      </div>
    }>
      <HomeContent />
    </Suspense>
  );
}

type Lang = "en" | "hi" | "gu" | "mr" | "ta" | "te";

// Status wording must never read as more certain than the backend status (SAFETY.md §5).
const STATUS_LABELS: Record<string, Record<Lang, string>> = {
  VERIFIED: { en: "✓ Verified", hi: "✓ सत्यापित", gu: "✓ ચકાસાયેલ", mr: "✓ पडताळलेले", ta: "✓ சரிபார்க்கப்பட்டது", te: "✓ ధృవీకరించబడింది" },
  NEEDS_REVIEW: { en: "⚠ Needs review", hi: "⚠ समीक्षा आवश्यक", gu: "⚠ સમીક્ષા જરૂરી", mr: "⚠ पुनरावलोकन आवश्यक", ta: "⚠ மதிப்பாய்வு தேவை", te: "⚠ సమీక్ష అవసరం" },
  HUMAN_REQUIRED: { en: "🔴 Human review required", hi: "🔴 मानव समीक्षा आवश्यक", gu: "🔴 માનવ સમીક્ષા જરૂરી", mr: "🔴 मानवी पुनरावलोकन आवश्यक", ta: "🔴 மனித மதிப்பாய்வு தேவை", te: "🔴 మానవ సమీక్ష అవసరం" },
  CONFLICT_DETECTED: { en: "🔴 Conflict — human review required", hi: "🔴 विरोधाभास — मानव समीक्षा आवश्यक", gu: "🔴 વિરોધાભાસ — માનવ સમીક્ષા જરૂરી", mr: "🔴 विसंगती — मानवी पुनरावलोकन आवश्यक", ta: "🔴 முரண்பாடு — மனித மதிப்பாய்வு தேவை", te: "🔴 వైరుధ్యం — మానవ సమీక్ష అవసరం" },
};

const STATUS_STYLES: Record<string, string> = {
  VERIFIED: "bg-emerald-100 text-emerald-900 border-emerald-300",
  NEEDS_REVIEW: "bg-amber-100 text-amber-900 border-amber-300",
  HUMAN_REQUIRED: "bg-rose-100 text-rose-900 border-rose-300",
  CONFLICT_DETECTED: "bg-rose-100 text-rose-900 border-rose-300",
};

function StatusBadge({ status, lang }: { status: string; lang: Lang }) {
  const label = STATUS_LABELS[status]?.[lang] ?? STATUS_LABELS.NEEDS_REVIEW[lang];
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${STATUS_STYLES[status] ?? STATUS_STYLES.NEEDS_REVIEW}`}>
      {label}
    </span>
  );
}

const SPEECH_LANG: Record<Lang, string> = { en: "en-IN", hi: "hi-IN", gu: "gu-IN", mr: "mr-IN", ta: "ta-IN", te: "te-IN" };

const READ_ALOUD_INTRO: Record<Lang, string> = {
  en: "Reading your care plan.",
  hi: "आपकी देखभाल योजना पढ़ी जा रही है।",
  gu: "તમારી સંભાળ યોજના વાંચવામાં આવી રહી છે.",
  mr: "तुमची काळजी योजना वाचली जात आहे.",
  ta: "உங்கள் பராமரிப்பு திட்டம் வாசிக்கப்படுகிறது.",
  te: "మీ సంరక్షణ ప్రణాళిక చదవబడుతోంది.",
};

const TRANSLATION_UNAVAILABLE: Record<Lang, string> = {
  en: "",
  hi: "अनुवाद सेवा अभी उपलब्ध नहीं है — मूल अंग्रेज़ी पाठ दिखाया जा रहा है।",
  gu: "અનુવાદ સેવા હાલમાં ઉપલબ્ધ નથી — મૂળ અંગ્રેજી લખાણ બતાવવામાં આવી રહ્યું છે.",
  mr: "भाषांतर सेवा सध्या उपलब्ध नाही — मूळ इंग्रजी मजकूर दाखवला जात आहे.",
  ta: "மொழிபெயர்ப்பு சேவை இப்போது கிடைக்கவில்லை — அசல் ஆங்கில உரை காட்டப்படுகிறது.",
  te: "అనువాద సేవ ప్రస్తుతం అందుబాటులో లేదు — అసలు ఆంగ్ల వచనం చూపబడుతోంది.",
};
