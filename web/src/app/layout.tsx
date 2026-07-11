import type { Metadata } from 'next'
import { GeistSans } from 'geist/font/sans'
import { GeistMono } from 'geist/font/mono'
import 'katex/dist/katex.min.css'
import './globals.css'
import PostHogInit from './posthog-init'
import { ThemeProvider } from '@/lib/theme-provider'
import { Toaster } from '@/components/ui/toast'

export const metadata: Metadata = {
  title: 'Stride — A-Level AI Tutor',
  description: 'Your personal A-Level tutor. Available 24/7. Less than the cost of one tutoring hour.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className={`h-full ${GeistSans.className} ${GeistMono.className}`}>
      <body className="h-full antialiased">
        <PostHogInit />
        <ThemeProvider>
          {children}
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  )
}
