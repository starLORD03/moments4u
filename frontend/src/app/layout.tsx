import type { Metadata } from "next";
import "@/styles/globals.css";
import { AuthProvider } from "@/lib/auth";

export const metadata: Metadata = {
  title: "moments4u — Capture Learning Moments",
  description:
    "A secure photo sharing platform for playgroups. Caregivers capture children's learning moments and parents view them privately.",
  keywords: ["playgroup", "photos", "children", "learning moments", "childcare"],
  viewport: "width=device-width, initial-scale=1, viewport-fit=cover",
  themeColor: "#f97316",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="manifest" href="/manifest.json" />
        <link rel="apple-touch-icon" href="/icon-192.png" />
      </head>
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
