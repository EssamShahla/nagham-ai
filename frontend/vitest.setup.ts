import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// jsdom doesn't implement Element.scrollTo -- any component that
// auto-scrolls a container (e.g. the assistant chat log) throws without
// this stub.
if (!Element.prototype.scrollTo) {
  Element.prototype.scrollTo = () => {}
}

afterEach(() => {
  cleanup()
})
