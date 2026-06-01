import posthog from 'posthog-js'

let initialized = false

export function initPostHog(): void {
  if (initialized || typeof window === 'undefined') return
  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY
  if (!key) return
  posthog.init(key, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST ?? 'https://us.i.posthog.com',
    capture_pageview: 'history_change',
    capture_pageleave: true,
    autocapture: true,
    persistence: 'localStorage+cookie',
  })
  initialized = true
}

export function identifyUser(userId: string, props?: Record<string, unknown>): void {
  if (typeof window === 'undefined' || !initialized) return
  posthog.identify(userId, props)
}

export function resetUser(): void {
  if (typeof window === 'undefined' || !initialized) return
  posthog.reset()
}

export function track(event: string, props?: Record<string, unknown>): void {
  if (typeof window === 'undefined' || !initialized) return
  posthog.capture(event, props)
}
