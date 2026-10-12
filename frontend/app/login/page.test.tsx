import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

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

import LoginPage from './page'

beforeEach(() => {
  pushMock.mockReset()
  apiMock.mockReset()
  searchParamsValue = new URLSearchParams()
  localStorage.clear()
})

describe('LoginPage', () => {
  it('renders the Google sign-in option alongside the password form', () => {
    render(<LoginPage />)
    expect(screen.getByRole('link', { name: /continue with google/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
  })

  it('shows the backend-provided Google error message', () => {
    searchParamsValue = new URLSearchParams({ google_error: 'Google sign-in was cancelled.' })
    render(<LoginPage />)
    expect(screen.getByText('Google sign-in was cancelled.')).toBeInTheDocument()
  })

  it('shows an account-linking banner when a google_link_token is present', () => {
    searchParamsValue = new URLSearchParams({ google_link_token: 'some-token' })
    render(<LoginPage />)
    expect(
      screen.getByText(/sign in with your password to link your google account/i),
    ).toBeInTheDocument()
  })

  it('on successful login with a pending link token, confirms the link before navigating away', async () => {
    searchParamsValue = new URLSearchParams({ google_link_token: 'pending-link-token' })

    apiMock.mockImplementation((path: string) => {
      if (path === '/auth/login') {
        return Promise.resolve({ access_token: 'jwt-123', token_type: 'bearer' })
      }
      if (path === '/auth/google/link') {
        return Promise.resolve({})
      }
      throw new Error(`unexpected call: ${path}`)
    })

    const user = userEvent.setup()
    render(<LoginPage />)

    await user.type(screen.getByLabelText(/email/i), 'owner@example.com')
    await user.type(screen.getByLabelText(/password/i), 'correct-password')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith('/dashboard'))

    expect(localStorage.getItem('access_token')).toBe('jwt-123')
    expect(apiMock).toHaveBeenCalledWith(
      '/auth/google/link',
      expect.objectContaining({ body: { link_token: 'pending-link-token' } }),
    )
  })

  it('still navigates to the dashboard even if confirming the Google link fails', async () => {
    searchParamsValue = new URLSearchParams({ google_link_token: 'pending-link-token' })

    apiMock.mockImplementation((path: string) => {
      if (path === '/auth/login') {
        return Promise.resolve({ access_token: 'jwt-456', token_type: 'bearer' })
      }
      if (path === '/auth/google/link') {
        return Promise.reject(new Error('link expired'))
      }
      throw new Error(`unexpected call: ${path}`)
    })

    const user = userEvent.setup()
    render(<LoginPage />)

    await user.type(screen.getByLabelText(/email/i), 'owner@example.com')
    await user.type(screen.getByLabelText(/password/i), 'correct-password')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith('/dashboard'))
    expect(localStorage.getItem('access_token')).toBe('jwt-456')
  })
})
