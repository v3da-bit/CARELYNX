"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { HeartHandshake, AlertTriangle, Sparkles, Menu, X, Stethoscope, FileText, Pill, Activity, Clock } from "lucide-react";
import { getOpenReviews } from "@/lib/api";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [openReviewCount, setOpenReviewCount] = useState<number>(0);

  useEffect(() => {
    getOpenReviews()
      .then(reviews => setOpenReviewCount(reviews.length))
      .catch(() => setOpenReviewCount(0));
  }, [pathname]);

  const handleUploadClick = () => {
    setMobileMenuOpen(false);
    if (pathname === "/") {
      window.dispatchEvent(new CustomEvent("carelynx:upload"));
    } else {
      router.push("/?action=upload");
    }
  };

  const handleNavToSection = (sectionId: string, eventName?: string) => {
    setMobileMenuOpen(false);
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

  return (
    <header className="border-b border-line/60 bg-white/80 backdrop-blur-md sticky top-0 z-30 shadow-xs">
      <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between" aria-label="Main Navigation">
        {/* Brand Logo */}
        <Link 
          href="/" 
          onClick={(e) => {
            setMobileMenuOpen(false);
            if (pathname === "/") {
              e.preventDefault();
              window.dispatchEvent(new CustomEvent("carelynx:home"));
              window.scrollTo({ top: 0, behavior: "smooth" });
            }
          }}
          className="flex items-center gap-2.5 font-bold tracking-tight text-slate-900 group cursor-pointer" 
          id="nav-home"
        >
          <div className="w-8 h-8 rounded-xl bg-brand text-white flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform">
            <HeartHandshake className="w-5 h-5 text-white" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold tracking-tight text-slate-900">CARELYNX</span>
            <span className="hidden sm:inline px-2 py-0.5 rounded-full text-[11px] font-semibold bg-brand-muted text-brand">
              Discharge Navigator
            </span>
          </div>
        </Link>
        
        {/* Center Desktop Navigation Links */}
        <div className="hidden md:flex items-center gap-6 text-sm font-semibold text-slate-600">
          <button 
            onClick={() => handleNavToSection("features", "carelynx:features")}
            className="hover:text-brand transition-colors text-left font-semibold cursor-pointer"
            id="nav-link-extraction"
          >
            AI Fact Extraction
          </button>
          
          <button 
            onClick={() => handleNavToSection("care-plan", "carelynx:careplan")}
            className="hover:text-brand transition-colors text-left font-semibold cursor-pointer"
            id="nav-link-careplan"
          >
            Care Plan
          </button>
          
          <button 
            onClick={() => handleNavToSection("prescriptions", "carelynx:prescriptions")}
            className="hover:text-brand transition-colors text-left font-semibold cursor-pointer"
            id="nav-link-prescriptions"
          >
            Prescriptions
          </button>
          
          <Link 
            href="/review" 
            className={`hover:text-brand transition-colors ${pathname === '/review' ? 'text-brand font-bold' : ''}`}
            id="nav-link-audit"
          >
            Clinical Audit
          </Link>
        </div>

        {/* Right Desktop Action Pills */}
        <div className="hidden sm:flex items-center gap-2 sm:gap-3 text-sm">
          <button
            onClick={() => window.dispatchEvent(new CustomEvent("carelynx:history"))}
            className="px-3.5 py-2 rounded-full border border-slate-300 hover:border-emerald-400 hover:bg-slate-50 text-slate-700 font-semibold text-xs sm:text-sm flex items-center gap-1.5 transition-all cursor-pointer"
            id="nav-my-history"
            title="Access private patient case history"
          >
            <Clock className="w-4 h-4 text-emerald-700" />
            <span>My History</span>
          </button>
          <Link 
            href="/review" 
            className="px-3.5 sm:px-4 py-2 rounded-full bg-rose-500 hover:bg-rose-600 active:bg-rose-700 text-white font-semibold text-xs sm:text-sm flex items-center gap-1.5 shadow-sm shadow-rose-500/20 transition-all"
            id="nav-emergency"
          >
            <AlertTriangle className="w-4 h-4" />
            <span>Review Alert</span>
            {openReviewCount > 0 && (
              <span className="ml-1 px-1.5 py-0.2 rounded-full bg-white text-rose-600 text-[10px] font-mono font-extrabold">
                {openReviewCount}
              </span>
            )}
          </Link>
          <button 
            onClick={handleUploadClick}
            className="px-4 sm:px-5 py-2 rounded-full bg-brand hover:bg-brand-light active:bg-emerald-700 text-white font-semibold text-xs sm:text-sm flex items-center gap-1.5 shadow-sm shadow-emerald-500/20 transition-all cursor-pointer"
            id="nav-get-started"
          >
            <Sparkles className="w-4 h-4" />
            <span>Upload Paperwork</span>
          </button>
        </div>

        {/* Mobile Hamburger Button */}
        <div className="flex md:hidden items-center gap-2">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors focus-visible:outline-2 focus-visible:outline-emerald-600 cursor-pointer"
            aria-label="Toggle navigation menu"
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="w-5 h-5" aria-hidden="true" /> : <Menu className="w-5 h-5" aria-hidden="true" />}
          </button>
        </div>
      </nav>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200/80 bg-white/95 backdrop-blur-md px-4 pt-3 pb-5 flex flex-col gap-3 shadow-lg">
          <button 
            onClick={() => handleNavToSection("features", "carelynx:features")}
            className="flex items-center gap-2 px-3 py-2.5 rounded-xl hover:bg-slate-100 text-sm font-semibold text-slate-800 text-left cursor-pointer"
          >
            <Sparkles className="w-4 h-4 text-emerald-600" />
            <span>AI Fact Extraction</span>
          </button>
          
          <button 
            onClick={() => handleNavToSection("care-plan", "carelynx:careplan")}
            className="flex items-center gap-2 px-3 py-2.5 rounded-xl hover:bg-slate-100 text-sm font-semibold text-slate-800 text-left"
          >
            <FileText className="w-4 h-4 text-blue-600" />
            <span>Care Plan</span>
          </button>
          
          <button 
            onClick={() => handleNavToSection("prescriptions", "carelynx:prescriptions")}
            className="flex items-center gap-2 px-3 py-2.5 rounded-xl hover:bg-slate-100 text-sm font-semibold text-slate-800 text-left"
          >
            <Pill className="w-4 h-4 text-sky-600" />
            <span>Prescriptions</span>
          </button>
          
          <Link 
            href="/review" 
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-2 px-3 py-2.5 rounded-xl hover:bg-slate-100 text-sm font-semibold text-slate-800"
          >
            <Stethoscope className="w-4 h-4 text-purple-600" />
            <span>Clinical Audit</span>
          </Link>

          <div className="pt-2 border-t border-slate-100 flex flex-col gap-2">
            <Link 
              href="/review" 
              onClick={() => setMobileMenuOpen(false)}
              className="w-full py-2.5 rounded-xl bg-rose-500 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-xs"
            >
              <AlertTriangle className="w-4 h-4" />
              <span>Review Alert {openReviewCount > 0 ? `(${openReviewCount} Open)` : ''}</span>
            </Link>
            <button 
              onClick={handleUploadClick}
              className="w-full py-2.5 rounded-xl bg-brand text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-xs"
            >
              <Sparkles className="w-4 h-4" />
              <span>Upload Paperwork</span>
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
