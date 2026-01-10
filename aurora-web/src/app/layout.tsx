import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AURORA - AI Wildfire Response System",
  description: "Real-time wildfire simulation with hybrid PPO + LLM multi-agent coordination",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased bg-[#030304] text-white font-body">
        {children}
      </body>
    </html>
  );
}
