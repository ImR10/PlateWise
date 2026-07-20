import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "PlateWise",
  description: "A student-built campus dining recommendation proof of concept.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
