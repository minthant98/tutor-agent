import type { Metadata } from 'next'
import { GeistSans } from 'geist/font/sans'
import 'katex/dist/katex.min.css'
import './globals.css'

export const metadata: Metadata = {
  title: 'Ascend — A-Level AI Tutor',
  description: 'Your personal A-Level tutor. Available 24/7. Less than the cost of one tutoring hour.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`h-full ${GeistSans.className}`}>
      <body className="h-full antialiased">
        {children}
      </body>
    </html>
  )
}
