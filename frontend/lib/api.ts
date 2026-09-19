export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"

export type QueryParams = Record<
  string,
  string | number | boolean | null | undefined
>

export type ApiMethod = "GET" | "POST" | "PATCH" | "DELETE"

export interface ApiOptions {
  method?: ApiMethod
  body?: unknown
  query?: QueryParams
  auth?: boolean
  headers?: HeadersInit
}

export class ApiError extends Error {
  status: number
  detail: unknown

  constructor(status: number, detail: unknown, message?: string) {
    super(message ?? `Request failed with status ${status}`)
    this.name = "ApiError"
    this.status = status
    this.detail = detail
  }
}

export function formatValidationError(detail: unknown): string {
  if (typeof detail === "string") return detail
  if (!Array.isArray(detail)) return "Please check the form and try again."

  const messages = detail
    .map((item) => {
      if (item && typeof item === "object" && "msg" in item) {
        const msg = (item as { msg: unknown }).msg
        return typeof msg === "string" ? msg : null
      }
      return null
    })
    .filter((m): m is string => Boolean(m))

  return messages.length > 0 ? messages.join(" ") : "Please check the form and try again."
}

function buildQueryString(query?: QueryParams): string {
  if (!query) return ""

  const searchParams = new URLSearchParams()

  for (const [key, value] of Object.entries(query)) {
    if (value === null || value === undefined || value === "") continue
    searchParams.append(key, String(value))
  }

  const text = searchParams.toString()

  return text ? `?${text}` : ""
}

function getAccessToken(): string | null {
  if (typeof window === "undefined") return null
  return window.localStorage.getItem("access_token")
}

export async function api<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { method = "GET", body, query, auth = false, headers } = options

  const requestHeaders: Record<string, string> = {}

  if (body !== undefined) {
    requestHeaders["Content-Type"] = "application/json"
  }

  if (headers) {
    Object.assign(requestHeaders, headers)
  }

  if (auth) {
    const token = getAccessToken()
    if (token) {
      requestHeaders.Authorization = `Bearer ${token}`
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}${buildQueryString(query)}`, {
    method,
    headers: requestHeaders,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (response.status === 204) {
    return undefined as T
  }

  const text = await response.text()

  let data: unknown = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (!response.ok) {
    const detail =
      (typeof data === "object" && data !== null && "detail" in data
        ? (data as { detail: unknown }).detail
        : data) ?? null

    const message =
      typeof detail === "string" ? detail : `Request failed with status ${response.status}`

    throw new ApiError(response.status, detail, message)
  }

  return data as T
}