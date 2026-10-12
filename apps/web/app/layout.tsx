import type { Metadata } from "next";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
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
        <Navbar />
        <main className="flex-1 flex flex-col">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
