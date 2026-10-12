import type { Metadata } from "next";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import SkipLink from "./components/SkipLink";
import CookieConsent from "./components/CookieConsent";
import "./globals.css";

export const metadata: Metadata = {
  title: "CARELYNX — Clear, Evidence-Linked Discharge Instructions",
  description:
    "Helping patients and caregivers navigate hospital discharge paperwork safely with line-by-line evidence, verified medications, and human review.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full antialiased scroll-smooth">
      <body className="min-h-full flex flex-col bg-bg text-fg selection:bg-brand-muted selection:text-brand">
        <SkipLink />
        <Navbar />
        <main id="main-content" tabIndex={-1} className="flex-1 flex flex-col outline-none">
          {children}
        </main>
        <Footer />
        <CookieConsent />
      </body>
    </html>
  );
}
