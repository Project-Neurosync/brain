import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Providers from '@/components/providers'
import { Toaster } from 'react-hot-toast'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'NeuroSync - AI-Powered Developer Knowledge Transfer',
  description: 'Effortless knowledge transfer for development teams. Your project\'s second brain.',
  keywords: ['AI', 'Developer Tools', 'Knowledge Transfer', 'Project Management', 'Team Collaboration'],
  authors: [{ name: 'NeuroSync Team' }],
  creator: 'NeuroSync',
  publisher: 'NeuroSync',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'https://neurosync.ai'),
  openGraph: {
    title: 'NeuroSync - AI-Powered Developer Knowledge Transfer',
    description: 'Effortless knowledge transfer for development teams. Your project\'s second brain.',
    url: 'https://neurosync.ai',
    siteName: 'NeuroSync',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'NeuroSync - AI-Powered Developer Knowledge Transfer',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'NeuroSync - AI-Powered Developer Knowledge Transfer',
    description: 'Effortless knowledge transfer for development teams. Your project\'s second brain.',
    images: ['/og-image.png'],
    creator: '@neurosync_ai',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: 'your-google-verification-code',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} h-full antialiased`}>
        <Providers>
          <div className="min-h-full bg-gradient-to-br from-gray-50 via-white to-primary-50/30">
            {children}
          </div>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#1e293b',
                color: '#f8fafc',
                border: '1px solid #334155',
                borderRadius: '12px',
                fontSize: '14px',
                padding: '12px 16px',
              },
              success: {
                iconTheme: {
                  primary: '#22c55e',
                  secondary: '#f8fafc',
                },
              },
              error: {
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#f8fafc',
                },
              },
            }}
          />
        </Providers>
      </body>
    </html>
  )
}
