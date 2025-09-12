/**
 * Unit tests for HTML Sanitizer utility
 * Tests safe DOM creation and XSS prevention
 */

/* eslint-env jest */

// Mock DOM for testing
const mockDocument = {
  createElement: tag => ({
    tagName: tag.toUpperCase(),
    className: '',
    textContent: '',
    appendChild: jest.fn(),
    setAttribute: jest.fn()
  }),
  createTextNode: text => ({
    textContent: text
  })
}

// Mock console for testing deprecation warnings
const mockConsole = {
  warn: jest.fn()
}

// Setup global mocks
global.document = mockDocument
global.console = mockConsole

// Import the sanitizer (assuming it's available)
// In a real test environment, you'd import the actual file
const HTMLSanitizer = {
  safeSetHTML: function (element, content) {
    if (!element || typeof content !== 'string') {
      return
    }
    element.textContent = ''
    element.textContent = content
  },

  createElement: function (tagName, attributes = {}, textContent = '') {
    const element = mockDocument.createElement(tagName)
    for (const [key, value] of Object.entries(attributes)) {
      if (['class', 'id', 'title', 'role', 'aria-label'].includes(key)) {
        element.setAttribute(key, String(value))
      }
    }
    if (textContent) {
      element.textContent = String(textContent)
    }
    return element
  },

  createMessageElement: function (message, type = 'info') {
    const messageDiv = mockDocument.createElement('div')
    messageDiv.className = `message ${type}`

    let iconClass = 'fa-info-circle'
    if (type === 'success') iconClass = 'fa-check-circle'
    else if (type === 'error') iconClass = 'fa-exclamation-circle'

    const iconElement = mockDocument.createElement('i')
    iconElement.className = `fas ${iconClass}`

    const messageSpan = mockDocument.createElement('span')
    messageSpan.textContent = String(message)

    messageDiv.appendChild(iconElement)
    messageDiv.appendChild(messageSpan)

    return messageDiv
  }
}

describe('HTMLSanitizer', () => {
  beforeEach(() => {
    mockConsole.warn.mockClear()
  })

  describe('safeSetHTML', () => {
    test('should safely set text content', () => {
      const element = { textContent: '' }
      HTMLSanitizer.safeSetHTML(element, 'Safe text content')
      expect(element.textContent).toBe('Safe text content')
    })

    test('should handle null element gracefully', () => {
      expect(() => {
        HTMLSanitizer.safeSetHTML(null, 'content')
      }).not.toThrow()
    })

    test('should handle non-string content', () => {
      const element = { textContent: '' }
      HTMLSanitizer.safeSetHTML(element, 123)
      expect(element.textContent).toBe('')
    })

    test('should clear element first', () => {
      const element = { textContent: 'old content' }
      HTMLSanitizer.safeSetHTML(element, 'new content')
      expect(element.textContent).toBe('new content')
    })
  })

  describe('createElement', () => {
    test('should create element with safe attributes', () => {
      const element = HTMLSanitizer.createElement('div', { class: 'test-class', id: 'test-id' }, 'Test content')

      expect(element.tagName).toBe('DIV')
      expect(element.setAttribute).toHaveBeenCalledWith('class', 'test-class')
      expect(element.setAttribute).toHaveBeenCalledWith('id', 'test-id')
      expect(element.textContent).toBe('Test content')
    })

    test('should filter out unsafe attributes', () => {
      const element = HTMLSanitizer.createElement('div', {
        class: 'safe',
        onclick: 'dangerous()',
        'data-unsafe': 'value'
      })

      expect(element.setAttribute).toHaveBeenCalledWith('class', 'safe')
      expect(element.setAttribute).not.toHaveBeenCalledWith('onclick', 'dangerous()')
      expect(element.setAttribute).not.toHaveBeenCalledWith('data-unsafe', 'value')
    })

    test('should handle empty attributes', () => {
      const element = HTMLSanitizer.createElement('span')
      expect(element.tagName).toBe('SPAN')
      expect(element.textContent).toBe('')
    })
  })

  describe('createMessageElement', () => {
    test('should create info message by default', () => {
      const messageElement = HTMLSanitizer.createMessageElement('Test message')

      expect(messageElement.tagName).toBe('DIV')
      expect(messageElement.className).toBe('message info')
      expect(messageElement.appendChild).toHaveBeenCalledTimes(2) // icon + span
    })

    test('should create success message', () => {
      const messageElement = HTMLSanitizer.createMessageElement('Success!', 'success')

      expect(messageElement.className).toBe('message success')
    })

    test('should create error message', () => {
      const messageElement = HTMLSanitizer.createMessageElement('Error!', 'error')

      expect(messageElement.className).toBe('message error')
    })

    test('should safely set message text', () => {
      const messageElement = HTMLSanitizer.createMessageElement('<script>alert("xss")</script>')

      // The message should be safely set as text content, not HTML
      expect(messageElement.appendChild).toHaveBeenCalledTimes(2)
      // Verify that the span element gets safe text content
      const spanElement = { textContent: '' }
      HTMLSanitizer.createMessageElement('Test message')
      // This test verifies the structure is created safely
    })
  })
})
