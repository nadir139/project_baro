import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SpeedLead AI - Dashboard",
  description:
    "Il tuo venditore AI che risponde su WhatsApp, Email e Telefono in italiano, 24/7",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="it">
      <body className="bg-gray-50 text-gray-900 antialiased">{children}</body>
    </html>
  );
}
