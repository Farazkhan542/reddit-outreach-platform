import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Reddit Outreach",
  description: "AI-assisted, human-approved Reddit outreach",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
