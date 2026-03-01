import type { Metadata } from "next";
import "@/app/globals.css";

export const metadata: Metadata = {
  title: "CatchUp - Meeting Recap & Q&A",
  description: "Real-time meeting recap with evidence-based Q&A",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50">{children}</body>
    </html>
  );
}
