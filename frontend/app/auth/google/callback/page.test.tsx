import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

const pushMock = vi.fn()
let searchParamsValue = new URLSearchParams()

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
  useSearchParams: () => searchParamsValue,
}))

const apiMock = vi.fn()
vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api')>('@/lib/api')
  return {
    ...actual,
    api: (...args: unknown[]) => apiMock(...args),
  }
})

import GoogleCallbackPage from './page'

beforeEach(() => {
  pushMock.mockReset()
  apiMock.mockReset()
  searchParamsValue = new URLSearchParams()
  localStorage.clear()
})

describe('GoogleCallbackPage', () => {
  it('exchanges the one-time code for a JWT, stores it, and redirects to the dashboard', async () => {
    searchParamsValue = new URLSearchParams({ code: 'one-time-exchange-code' })
    apiMock.mockResolvedValue({ access_token: 'real-jwt-token', token_type: 'bearer' })

    render(<GoogleCallbackPage />)

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith('/dashboard'))

    expect(apiMock).toHaveBeenCalledWith(
      '/auth/google/exchange',
      expect.objectContaining({ method: 'POST', body: { code: 'one-time-exchange-code' } }),
    )
    expect(localStorage.getItem('access_token')).toBe('real-jwt-token')
  })

  it('shows an error and does not store anything if the code is missing', async () => {
    render(<GoogleCallbackPage />)

    expect(await screen.findByText(/sign-in failed/i)).toBeInTheDocument()
    expect(apiMock).not.toHaveBeenCalled()
    expect(localStorage.getItem('access_token')).toBeNull()
  })

  it('shows the server error message if the exchange fails, without redirecting', async () => {
    searchParamsValue = new URLSearchParams({ code: 'expired-code' })

    const { ApiError } = await import('@/lib/api')
    apiMock.mockRejectedValue(new ApiError(400, 'This sign-in code is invalid or has expired.'))

    render(<GoogleCallbackPage />)

    expect(await screen.findByText(/this sign-in code is invalid or has expired/i)).toBeInTheDocument()
    expect(pushMock).not.toHaveBeenCalled()
    expect(localStorage.getItem('access_token')).toBeNull()
  })
})
