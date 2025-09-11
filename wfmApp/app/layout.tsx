import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from '../contexts/auth-context'
import { Toaster } from '@/components/ui/toaster';
import { OfflineProvider } from '@/context/OfflineContext';
import OfflineBadge from '@/components/OfflineBadge';

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Field Service Management",
  description: "Admin Dashboard for Workforce Management Operations",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} font-sans antialiased`}
      >
        <AuthProvider>
          <OfflineProvider>
            <OfflineBadge />
            {children}
            <Toaster />
          </OfflineProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
