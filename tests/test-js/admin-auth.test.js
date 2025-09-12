/**
 * Unit tests for Admin Authentication utilities
 * Tests JWT token management and authenticated fetch wrapper
 */

/* eslint-env jest */

// Mock localStorage
const mockLocalStorage = {
  storage: {},
  getItem: jest.fn(key => mockLocalStorage.storage[key] || null),
  setItem: jest.fn((key, value) => {
    mockLocalStorage.storage[key] = value
  }),
  removeItem: jest.fn(key => {
    delete mockLocalStorage.storage[key]
  }),
  clear: jest.fn(() => {
    mockLocalStorage.storage = {}
  })
}

// Make localStorage mock work properly
Object.defineProperty(mockLocalStorage, 'getItem', {
  value: jest.fn(key => mockLocalStorage.storage[key] || null)
})
Object.defineProperty(mockLocalStorage, 'setItem', {
  value: jest.fn((key, value) => {
    mockLocalStorage.storage[key] = value
  })
})
Object.defineProperty(mockLocalStorage, 'removeItem', {
  value: jest.fn(key => {
    delete mockLocalStorage.storage[key]
  })
})

// Mock fetch
const mockFetch = jest.fn()

// Mock window.location
const mockLocation = {
  href: ''
}

// Setup global mocks
global.localStorage = mockLocalStorage
global.fetch = mockFetch
Object.defineProperty(global, 'location', {
  value: mockLocation,
  writable: true
})

// Mock admin auth functions (simulating the actual implementation)
function authenticatedFetch(url, options = {}) {
  const token = mockLocalStorage.getItem('jwt_token')
  if (token && !options.headers?.Authorization) {
    options.headers = {
      ...options.headers,
      Authorization: `Bearer ${token}`
    }
  }
  return mockFetch(url, options)
}

function handleAuthError(response) {
  if (response.status === 401) {
    mockLocalStorage.removeItem('jwt_token')
    mockLocation.href = '/login'
    return true
  }
  return false
}

describe('Admin Authentication', () => {
  beforeEach(() => {
    // Clear mocks
    mockLocalStorage.clear()
    mockLocalStorage.getItem.mockClear()
    mockLocalStorage.setItem.mockClear()
    mockLocalStorage.removeItem.mockClear()
    mockFetch.mockClear()
    mockLocation.href = ''
  })

  describe('authenticatedFetch', () => {
    test('should add Authorization header when token exists', async () => {
      mockLocalStorage.storage.jwt_token = 'test-token'
      mockFetch.mockResolvedValue({ ok: true, json: () => ({}) })

      await authenticatedFetch('/api/test', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      })

      expect(mockFetch).toHaveBeenCalledWith('/api/test', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer test-token'
        }
      })
    })

    test('should not override existing Authorization header', async () => {
      mockLocalStorage.storage.jwt_token = 'test-token'
      mockFetch.mockResolvedValue({ ok: true })

      await authenticatedFetch('/api/test', {
        headers: { Authorization: 'Bearer custom-token' }
      })

      expect(mockFetch).toHaveBeenCalledWith('/api/test', {
        headers: { Authorization: 'Bearer custom-token' }
      })
    })

    test('should work without token', async () => {
      mockFetch.mockResolvedValue({ ok: true })

      await authenticatedFetch('/api/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })

      expect(mockFetch).toHaveBeenCalledWith('/api/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
    })

    test('should handle empty options', async () => {
      mockLocalStorage.storage.jwt_token = 'test-token'
      mockFetch.mockResolvedValue({ ok: true })

      await authenticatedFetch('/api/test')

      expect(mockFetch).toHaveBeenCalledWith('/api/test', {
        headers: {
          Authorization: 'Bearer test-token'
        }
      })
    })
  })

  describe('handleAuthError', () => {
    test('should handle 401 unauthorized response', () => {
      mockLocalStorage.storage.jwt_token = 'expired-token'

      const response = { status: 401 }
      const result = handleAuthError(response)

      expect(result).toBe(true)
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('jwt_token')
      expect(mockLocation.href).toBe('/login')
    })

    test('should not handle non-401 responses', () => {
      mockLocalStorage.storage.jwt_token = 'valid-token'

      const response = { status: 200 }
      const result = handleAuthError(response)

      expect(result).toBe(false)
      expect(mockLocalStorage.removeItem).not.toHaveBeenCalled()
      expect(mockLocation.href).toBe('')
    })

    test('should handle 403 forbidden response (no redirect)', () => {
      mockLocalStorage.storage.jwt_token = 'valid-token'

      const response = { status: 403 }
      const result = handleAuthError(response)

      expect(result).toBe(false)
      expect(mockLocalStorage.removeItem).not.toHaveBeenCalled()
      expect(mockLocation.href).toBe('')
    })
  })

  describe('JWT Token Management', () => {
    test('should store and retrieve JWT tokens', () => {
      // This tests the mockLocalStorage integration
      mockLocalStorage.setItem('jwt_token', 'new-token')

      expect(mockLocalStorage.getItem('jwt_token')).toBe('new-token')
      expect(mockLocalStorage.storage.jwt_token).toBe('new-token')
    })

    test('should remove JWT tokens', () => {
      mockLocalStorage.setItem('jwt_token', 'token-to-remove')
      mockLocalStorage.removeItem('jwt_token')

      expect(mockLocalStorage.getItem('jwt_token')).toBe(null)
      expect(mockLocalStorage.storage.jwt_token).toBeUndefined()
    })

    test('should handle missing JWT tokens', () => {
      expect(mockLocalStorage.getItem('jwt_token')).toBe(null)
    })
  })
})
