import { useEffect, useState } from 'react'
import type { Student } from './types'

const TOKEN_KEY = 'ascend_token'

export function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export function isAuthenticated(): boolean {
  return getToken() !== null
}

/** Sign out the current user and clear stored credentials. */
export async function signOut(): Promise<void> {
  clearToken()
}

/**
 * Returns the current Student from the /auth/me endpoint, or null if not
 * authenticated or still loading. Refreshes once per mount.
 */
export function useStudent(): Student | null {
  const [student, setStudent] = useState<Student | null>(null)

  useEffect(() => {
    if (!isAuthenticated()) return

    // Lazy import to avoid circular deps with api.ts
    import('./api').then(({ getMe }) =>
      getMe()
        .then(setStudent)
        .catch(() => setStudent(null))
    )
  }, [])

  return student
}
