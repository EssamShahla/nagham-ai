import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import { GoogleButton } from './google-button'

describe('GoogleButton', () => {
  it('links straight to the backend Google login endpoint (full page navigation, not a fetch)', () => {
    render(<GoogleButton />)

    const link = screen.getByRole('link', { name: /continue with google/i })
    expect(link).toHaveAttribute('href', expect.stringMatching(/\/auth\/google\/login$/))
  })

  it('supports a custom label for the registration page', () => {
    render(<GoogleButton label="Sign up with Google" />)
    expect(screen.getByRole('link', { name: /sign up with google/i })).toBeInTheDocument()
  })
})
