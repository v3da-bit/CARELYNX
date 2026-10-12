"use client";

import { usePathname } from "next/navigation";
import { ShieldCheck } from "lucide-react";

export default function Footer() {
  const pathname = usePathname();

  // Hide footer on /review so the clinical workspace fits full viewport without whole-page scroll
  if (pathname === "/review") {
    return null;
  }

  return (
    <footer className="border-t border-slate-200/80 bg-white/60 text-xs text-slate-600 py-6 no-print">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row justify-between items-center gap-4 text-center sm:text-left">
        <div className="flex items-center gap-2 text-slate-700">
          <ShieldCheck className="w-4 h-4 text-brand shrink-0" />
          <p>
            <strong className="text-slate-900">CARELYNX Verbatim Evidence Policy:</strong> All facts are anchored directly to original paperwork sentences.
          </p>
        </div>
        <p className="text-slate-600 font-medium text-[11px] shrink-0">
          Non-diagnostic navigation tool • Always verify with your clinical team
        </p>
      </div>
    </footer>
  );
}
