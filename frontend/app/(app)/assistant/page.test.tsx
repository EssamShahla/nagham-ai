import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
}))

const apiMock = vi.fn()
vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api')>('@/lib/api')
  return {
    ...actual,
    api: (...args: unknown[]) => apiMock(...args),
  }
})

import AssistantPage from './page'

beforeEach(() => {
  apiMock.mockReset()
  localStorage.clear()
})

async function sendMessage(user: ReturnType<typeof userEvent.setup>, text: string) {
  const textarea = screen.getByPlaceholderText(/ask for songs/i)
  await user.type(textarea, text)
  await user.click(screen.getByRole('button', { name: /send message/i }))
}

describe('AssistantPage conversation history', () => {
  it('sends an empty history on the first message, then accumulates prior turns', async () => {
    apiMock.mockImplementation((path: string) => {
      if (path === '/assistant') {
        return Promise.resolve({
          answer: 'رد تجريبي أول',
          search_type: 'semantic',
          analysis: { intent: 'song_search' },
          results: [{ id: 101, title: 'اغنية تجريبية' }],
        })
      }
      throw new Error(`unexpected call: ${path}`)
    })

    const user = userEvent.setup()
    render(<AssistantPage />)

    await sendMessage(user, 'سؤال اول')
    await waitFor(() => expect(apiMock).toHaveBeenCalledTimes(1))

    const [, firstCallOptions] = apiMock.mock.calls[0]
    expect(firstCallOptions.body.history).toEqual([])

    apiMock.mockImplementation((path: string) => {
      if (path === '/assistant') {
        return Promise.resolve({
          answer: 'رد تجريبي ثاني',
          search_type: 'semantic',
          analysis: { intent: 'follow_up' },
          results: [],
        })
      }
      throw new Error(`unexpected call: ${path}`)
    })

    await sendMessage(user, 'سؤال متابعة')
    await waitFor(() => expect(apiMock).toHaveBeenCalledTimes(2))

    const [, secondCallOptions] = apiMock.mock.calls[1]
    expect(secondCallOptions.body.history).toEqual([
      { role: 'user', content: 'سؤال اول', analysis: null, result_ids: null },
      {
        role: 'assistant',
        content: 'رد تجريبي أول',
        analysis: { intent: 'song_search' },
        result_ids: [101],
      },
    ])
  })
})
