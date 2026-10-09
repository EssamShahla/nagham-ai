"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import type { UserResponse } from "@/lib/types"

interface UseCurrentUserResult {
  data: UserResponse | null
  isLoading: boolean
  error: unknown
}

export function useCurrentUser(): UseCurrentUserResult {
  const [data, setData] = useState<UserResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<unknown>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      const token =
        typeof window !== "undefined" ? window.localStorage.getItem("access_token") : null

      if (!token) {
        if (!cancelled) {
          setData(null)
          setIsLoading(false)
        }
        return
      }

      try {
        const me = await api<UserResponse>("/auth/me", { auth: true })
        if (!cancelled) setData(me)
      } catch (err) {
        if (!cancelled) {
          setData(null)
          setError(err)
        }
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    load()

    return () => {
      cancelled = true
    }
  }, [])

  return { data, isLoading, error }
}
