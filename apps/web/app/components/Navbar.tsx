"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  HeartHandshake,
  AlertTriangle,
  Sparkles,
  Menu,
  X,
  Stethoscope,
  FileText,
  Pill,
  Clock,
  User,
  ChevronRight,
  ShieldCheck,
  CheckCircle2
} from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [sidePanelOpen, setSidePanelOpen] = useState(false);
  const [openReviewCount, setOpenReviewCount] = useState<number>(0);
  const [activeTab, setActiveTab] = useState<string>("features");
  const [patientName, setPatientName] = useState<string>("");

  useEffect(() => {
    // Only show review alerts that belong to the current user's active uploaded file
    const handleCaseAlerts = (e: Event) => {
      const custom = e as CustomEvent<{ count: number }>;
      setOpenReviewCount(custom.detail?.count || 0);
    };
    window.addEventListener("carelynx:active-alerts", handleCaseAlerts);

    // Read cached patient profile for display
    const loadProfileName = () => {
      try {
        const raw = localStorage.getItem("carelynx_patient_profile");
        if (raw) {
          const parsed = JSON.parse(raw);
          if (parsed.full_name) {
            setPatientName(parsed.full_name);
          }
        }
      } catch {
        // ignore
      }
    };
    loadProfileName();
    window.addEventListener("carelynx:profile-saved", loadProfileName);

    // Lock body scroll when mobile side panel is open
    if (sidePanelOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }

    return () => {
      window.removeEventListener("carelynx:active-alerts", handleCaseAlerts);
      window.removeEventListener("carelynx:profile-saved", loadProfileName);
      document.body.style.overflow = "";
    };
  }, [sidePanelOpen]);

  const handleUploadClick = () => {
    setSidePanelOpen(false);
    if (pathname === "/") {
      window.dispatchEvent(new CustomEvent("carelynx:upload"));
    } else {
      router.push("/?action=upload");
    }
  };

  const handleNavToSection = (sectionId: string, eventName?: string) => {
    setSidePanelOpen(false);
    setActiveTab(sectionId);
    if (pathname === "/") {
      if (eventName) {
        window.dispatchEvent(new CustomEvent(eventName));
      } else {
        const element = document.getElementById(sectionId);
        if (element) {
          element.scrollIntoView({ behavior: "smooth" });
        }
      }
    } else {
      router.push(`/?action=${sectionId}#${sectionId}`);
    }
  };

  const navigateToReview = () => {
    setSidePanelOpen(false);
    let recentCaseId: string | null = null;
    if (typeof window !== "undefined") {
      recentCaseId = localStorage.getItem("carelynx_recent_case_id");
    }
    if (recentCaseId) {
      router.push(`/review?case_id=${recentCaseId}`);
    } else {
      router.push("/review");
    }
  };

  return (
    <>
      {/* Top Navbar Container — flush to top edge with zero gap */}
      <header className="sticky top-0 z-40 w-full px-3 sm:px-6 lg:px-8 pt-0 pb-2 transition-all no-print">
        <nav
          className="bg-white/90 backdrop-blur-md rounded-t-none rounded-b-2xl p-4 sm:p-5 md:p-6 border border-t-0 border-slate-200/80 shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4 md:gap-6 w-full max-w-[1720px] mx-auto transition-all"
          aria-label="Main Navigation"
        >
          {/* Top Row on Mobile / Left on Desktop: Brand Logo & Mobile Trigger */}
          <div className="w-full md:w-auto flex items-center justify-between gap-4">
            <Link
              href="/"
              onClick={(e) => {
                setSidePanelOpen(false);
                if (pathname === "/") {
                  e.preventDefault();
                  window.dispatchEvent(new CustomEvent("carelynx:home"));
                  window.scrollTo({ top: 0, behavior: "smooth" });
                }
              }}
              className="flex items-center gap-3 font-bold tracking-tight text-slate-900 group cursor-pointer shrink-0"
              id="nav-home"
            >
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand to-emerald-600 text-white flex items-center justify-center shadow-md shadow-emerald-600/20 group-hover:scale-105 transition-transform">
                <HeartHandshake className="w-5 h-5 text-white" />
              </div>
              <div className="flex flex-col sm:flex-row sm:items-center gap-0.5 sm:gap-2">
                <span className="text-xl font-extrabold tracking-tight text-slate-900">CARELYNX</span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-brand-muted text-brand border border-emerald-200/60 w-fit">
                  Discharge Navigator
                </span>
              </div>
            </Link>

            {/* Mobile Header Actions (Alert badge + Hamburger Toggle) */}
            <div className="flex md:hidden items-center gap-2">
              {openReviewCount > 0 && (
                <button
                  onClick={navigateToReview}
                  className="px-2.5 py-1 rounded-full bg-rose-50 border border-rose-200 text-rose-700 text-xs font-bold flex items-center gap-1 shadow-2xs"
                  title={`${openReviewCount} alerts requiring review`}
                >
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                  <span>{openReviewCount}</span>
                </button>
              )}
              <button
                onClick={() => setSidePanelOpen(true)}
                className="p-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 active:bg-slate-300 text-slate-700 transition-colors focus-visible:outline-2 focus-visible:outline-emerald-600 cursor-pointer shadow-2xs"
                aria-label="Open side navigation panel"
                aria-expanded={sidePanelOpen}
                id="mobile-nav-toggle"
              >
                <Menu className="w-5 h-5" aria-hidden="true" />
              </button>
            </div>
          </div>

          {/* Center Desktop Navigation Tabs (Innovative Segmented Pill Layout) */}
          <div className="hidden md:flex items-center bg-slate-100/80 p-1.5 rounded-xl border border-slate-200/70 shadow-2xs">
            <button
              onClick={() => handleNavToSection("features", "carelynx:features")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${activeTab === "features" && pathname === "/"
                ? "bg-white text-emerald-800 shadow-xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-white/60"
                }`}
              id="nav-link-extraction"
            >
              <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
              <span>Fact Extraction</span>
            </button>

            <button
              onClick={() => handleNavToSection("care-plan", "carelynx:careplan")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${activeTab === "care-plan" && pathname === "/"
                ? "bg-white text-emerald-800 shadow-xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-white/60"
                }`}
              id="nav-link-careplan"
            >
              <FileText className="w-3.5 h-3.5 text-blue-600" />
              <span>Care Plan</span>
            </button>

            <button
              onClick={() => handleNavToSection("prescriptions", "carelynx:prescriptions")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${activeTab === "prescriptions" && pathname === "/"
                ? "bg-white text-emerald-800 shadow-xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-white/60"
                }`}
              id="nav-link-prescriptions"
            >
              <Pill className="w-3.5 h-3.5 text-sky-600" />
              <span>Prescriptions</span>
            </button>

            <Link
              href="/review"
              onClick={() => setActiveTab("audit")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${pathname === '/review'
                ? "bg-white text-emerald-800 shadow-xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-white/60"
                }`}
              id="nav-link-audit"
            >
              <Stethoscope className="w-3.5 h-3.5 text-purple-600" />
              <span>Clinical Audit</span>
            </Link>
          </div>

          {/* Right Desktop Action Pills */}
          <div className="hidden md:flex items-center gap-2.5 text-sm shrink-0">
            <button
              onClick={() => window.dispatchEvent(new CustomEvent("carelynx:history"))}
              className="px-3.5 py-2 rounded-xl border border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/50 text-slate-700 font-semibold text-xs flex items-center gap-1.5 transition-all cursor-pointer shadow-2xs"
              id="nav-my-history"
              title="Access private patient case history"
            >
              <Clock className="w-4 h-4 text-emerald-700" />
              <span>My History</span>
            </button>

            <button
              onClick={() => window.dispatchEvent(new CustomEvent("carelynx:profile"))}
              className="px-3.5 py-2 rounded-xl border border-slate-200 hover:border-blue-300 hover:bg-blue-50/50 text-slate-700 font-semibold text-xs flex items-center gap-1.5 transition-all cursor-pointer shadow-2xs"
              id="nav-my-profile"
              title="View and edit profile details"
            >
              <User className="w-4 h-4 text-blue-600" />
              <span className="max-w-[120px] truncate">{patientName || "Profile"}</span>
            </button>

            <button
              onClick={navigateToReview}
              className={`px-3.5 py-2 rounded-xl font-semibold text-xs flex items-center gap-1.5 transition-all cursor-pointer shadow-2xs ${openReviewCount > 0
                ? "bg-rose-500 hover:bg-rose-600 text-white shadow-rose-500/20"
                : "bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200/80"
                }`}
              id="nav-emergency"
              title="Open Clinical Review alerts"
            >
              <AlertTriangle className={`w-4 h-4 ${openReviewCount > 0 ? "text-white" : "text-amber-500"}`} />
              <span>Review Alert</span>
              {openReviewCount > 0 && (
                <span className="ml-1 px-1.5 py-0.2 rounded-full bg-white text-rose-600 text-[10px] font-mono font-extrabold shadow-2xs">
                  {openReviewCount}
                </span>
              )}
            </button>

            <button
              onClick={handleUploadClick}
              className="px-4 py-2 rounded-xl bg-brand hover:bg-brand-light active:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm shadow-emerald-500/20 transition-all cursor-pointer hover:shadow-md"
              id="nav-get-started"
            >
              <Sparkles className="w-4 h-4 text-white" />
              <span>Upload Paperwork</span>
            </button>
          </div>
        </nav>
      </header>

      {/* Mobile Slide-Out Side Panel Drawer */}
      {sidePanelOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex justify-end no-print" role="dialog" aria-modal="true">
          {/* Backdrop Overlay */}
          <div
            onClick={() => setSidePanelOpen(false)}
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs transition-opacity duration-300 animate-in fade-in"
            aria-hidden="true"
          />

          {/* Drawer Panel */}
          <div className="relative w-full max-w-xs sm:max-w-sm bg-white h-full shadow-2xl flex flex-col justify-between z-10 animate-in slide-in-from-right duration-300 border-l border-slate-200">
            {/* Drawer Top Header */}
            <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-brand text-white flex items-center justify-center shadow-xs">
                  <HeartHandshake className="w-5 h-5 text-white" />
                </div>
                <div>
                  <span className="text-base font-extrabold text-slate-900 block leading-tight">CARELYNX</span>
                  <span className="text-[10px] font-semibold text-brand">Mobile Navigator</span>
                </div>
              </div>
              <button
                onClick={() => setSidePanelOpen(false)}
                className="p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-200 transition-colors cursor-pointer"
                aria-label="Close navigation panel"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-6">
              {/* User Profile Card in Side Panel */}
              <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-blue-100 border border-blue-200 text-blue-700 flex items-center justify-center font-bold text-sm">
                    {patientName ? patientName.charAt(0).toUpperCase() : <User className="w-5 h-5" />}
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-900 block truncate max-w-[140px]">
                      {patientName || "Guest Patient"}
                    </span>
                    <span className="text-[10px] text-slate-500 block">Personal Health Profile</span>
                  </div>
                </div>
                <button
                  onClick={() => { setSidePanelOpen(false); window.dispatchEvent(new CustomEvent("carelynx:profile")); }}
                  className="px-2.5 py-1 text-[11px] font-bold text-blue-700 hover:bg-blue-100/60 rounded-lg transition"
                >
                  Edit
                </button>
              </div>

              {/* Navigation Links Group */}
              <div className="flex flex-col gap-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-600 px-3 pb-1">
                  Document Explorer
                </span>

                <button
                  onClick={() => handleNavToSection("features", "carelynx:features")}
                  className="flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-slate-100 text-xs font-bold text-slate-800 transition cursor-pointer text-left"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg bg-emerald-100/70 text-emerald-700 flex items-center justify-center">
                      <Sparkles className="w-3.5 h-3.5" />
                    </div>
                    <span>AI Fact Extraction</span>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                </button>

                <button
                  onClick={() => handleNavToSection("care-plan", "carelynx:careplan")}
                  className="flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-slate-100 text-xs font-bold text-slate-800 transition cursor-pointer text-left"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg bg-blue-100/70 text-blue-700 flex items-center justify-center">
                      <FileText className="w-3.5 h-3.5" />
                    </div>
                    <span>Discharge Care Plan</span>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                </button>

                <button
                  onClick={() => handleNavToSection("prescriptions", "carelynx:prescriptions")}
                  className="flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-slate-100 text-xs font-bold text-slate-800 transition cursor-pointer text-left"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg bg-sky-100/70 text-sky-700 flex items-center justify-center">
                      <Pill className="w-3.5 h-3.5" />
                    </div>
                    <span>Medications & Dosages</span>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                </button>

                <Link
                  href="/review"
                  onClick={() => setSidePanelOpen(false)}
                  className={`flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-slate-100 text-xs font-bold text-slate-800 transition ${pathname === '/review' ? 'bg-purple-50 text-purple-800' : ''}`}
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg bg-purple-100/70 text-purple-700 flex items-center justify-center">
                      <Stethoscope className="w-3.5 h-3.5" />
                    </div>
                    <span>Clinical Audit Workspace</span>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                </Link>
              </div>

              {/* Patient Tools Section */}
              <div className="flex flex-col gap-1 pt-2 border-t border-slate-100">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-600 px-3 pb-1">
                  Personal Dashboard
                </span>

                <button
                  onClick={() => { setSidePanelOpen(false); window.dispatchEvent(new CustomEvent("carelynx:history")); }}
                  className="flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-slate-100 text-xs font-bold text-slate-800 transition cursor-pointer text-left"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg bg-emerald-100/70 text-emerald-700 flex items-center justify-center">
                      <Clock className="w-3.5 h-3.5" />
                    </div>
                    <span>My Patient History</span>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                </button>

                <button
                  onClick={navigateToReview}
                  className={`flex items-center justify-between px-3 py-2.5 rounded-xl transition cursor-pointer text-left ${openReviewCount > 0 ? "bg-rose-50 text-rose-900 border border-rose-200" : "hover:bg-slate-100 text-slate-800"
                    }`}
                >
                  <div className="flex items-center gap-2.5">
                    <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${openReviewCount > 0 ? "bg-rose-500 text-white" : "bg-amber-100 text-amber-700"}`}>
                      <AlertTriangle className="w-3.5 h-3.5" />
                    </div>
                    <span className="text-xs font-bold">Review Alerts</span>
                  </div>
                  {openReviewCount > 0 ? (
                    <span className="px-2 py-0.5 rounded-full bg-rose-600 text-white text-[10px] font-bold">
                      {openReviewCount} Open
                    </span>
                  ) : (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  )}
                </button>
              </div>

              {/* Safety Assurance Note */}
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/60 text-[11px] text-slate-600 flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <p className="leading-snug">
                  Every instruction is grounded verbatim to hospital source documents.
                </p>
              </div>
            </div>

            {/* Drawer Bottom Actions */}
            <div className="p-5 border-t border-slate-100 bg-slate-50/50 flex flex-col gap-2.5">
              <button
                onClick={handleUploadClick}
                className="w-full py-3 rounded-xl bg-brand hover:bg-brand-light text-white font-bold text-xs flex items-center justify-center gap-2 shadow-sm shadow-emerald-600/20 cursor-pointer transition active:scale-[0.98]"
              >
                <Sparkles className="w-4 h-4" />
                <span>Upload Paperwork</span>
              </button>
              <p className="text-[10px] text-slate-600 text-center">
                Emergency? Call <span className="font-bold text-rose-600">108 / 911</span> immediately.
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

