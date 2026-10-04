import type { Metadata } from "next";
import { Inter, Noto_Sans_Devanagari, Noto_Sans_Gujarati } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const deva = Noto_Sans_Devanagari({ variable: "--font-deva", subsets: ["devanagari"], weight: ["400", "600"] });
const guj = Noto_Sans_Gujarati({ variable: "--font-guj", subsets: ["gujarati"], weight: ["400", "600"] });

export const metadata: Metadata = {
  title: "CARELYNX — Clearer discharge instructions",
  description:
    "CARELYNX turns discharge documents into clear, evidence-linked, multilingual information and flags anything uncertain for human review.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.variable} ${deva.variable} ${guj.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col" suppressHydrationWarning>
        <header className="border-b border-line/70 bg-bg/60 backdrop-blur sticky top-0 z-20">
          <nav className="mx-auto max-w-6xl px-5 h-14 flex items-center justify-between" aria-label="Main">
            <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight" id="nav-home">
              <span className="inline-block h-6 w-6 rounded-md bg-gradient-to-br from-accent to-accent-2" aria-hidden />
              CARELYNX
            </Link>
            <div className="flex items-center gap-5 text-sm text-muted">
              <Link href="/" className="hover:text-fg transition-colors" id="nav-patient">
                Patient view
              </Link>
              <Link href="/review" className="hover:text-fg transition-colors" id="nav-review">
                Reviewer queue
              </Link>
            </div>
          </nav>
        </header>
        <main className="flex-1">{children}</main>
        <footer className="border-t border-line/70 text-xs text-muted">
          <div className="mx-auto max-w-6xl px-5 py-4">
            CARELYNX shows what your documents say. It does not diagnose, prescribe or change treatment. Always
            follow your care team&apos;s instructions.
          </div>
        </footer>
      </body>
    </html>
  );
}
