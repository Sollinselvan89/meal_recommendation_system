import type React from "react"
import "./globals.css"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { ThemeProvider } from "@/components/theme-provider"
import ApiKeySettings from "@/components/api-key-settings"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Meal Recommendation System",
  description: "Get personalized meal recommendations based on your preferences",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <div className="fixed right-4 top-4 z-50">
            <ApiKeySettings />
          </div>
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}


import './globals.css'