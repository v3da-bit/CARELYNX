import type { Metadata, Viewport } from "next";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import SkipLink from "./components/SkipLink";
import CookieConsent from "./components/CookieConsent";
import "./globals.css";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  themeColor: "#0d9488",
};

export const metadata: Metadata = {
  title: "CARELYNX — Clear, Evidence-Linked Discharge Instructions",
  description:
    "Helping patients and caregivers navigate hospital discharge paperwork safely with line-by-line evidence, verified medications, and human review.",
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
      { url: "/favicon-48x48.png", sizes: "48x48", type: "image/png" },
    ],
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
    other: [
      { rel: "icon", url: "/android-chrome-192x192.png", sizes: "192x192", type: "image/png" },
      { rel: "icon", url: "/android-chrome-512x512.png", sizes: "512x512", type: "image/png" },
    ],
  },
  manifest: "/site.webmanifest",
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
