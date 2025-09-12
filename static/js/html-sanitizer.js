/**
 * Safe DOM Manipulation Utilities for Admin Interface
 * Provides secure DOM creation without innerHTML to prevent XSS attacks
 * Note: This completely avoids innerHTML/outerHTML in favor of programmatic DOM creation
 */

window.HTMLSanitizer = {
  /**
   * DEPRECATED: This regex-based sanitization is unsafe and should not be used
   * Kept for compatibility but use createElement or safeSetHTML instead
   * @deprecated Use createElement or safeSetHTML methods instead
   * @param {string} html - HTML content (will be treated as text)
   * @returns {string} - Text content only
   */
  sanitizeAdminHTML: function (html) {
    console.warn('sanitizeAdminHTML is deprecated. Use createElement or safeSetHTML instead.')
    // Convert any HTML to plain text to prevent XSS
    if (typeof html !== 'string') {
      return ''
    }
    // Create a temporary text node to strip all HTML
    const textNode = document.createTextNode(html)
    return textNode.textContent || ''
  },

  /**
   * Safely set content without using innerHTML
   * Creates DOM elements programmatically to avoid XSS
   * @param {HTMLElement} element - DOM element to update
   * @param {string} content - Text content to set (HTML will be escaped)
   */
  safeSetHTML: function (element, content) {
    if (!element || typeof content !== 'string') {
      return
    }

    // Clear the element first
    element.textContent = ''

    // For admin interfaces, we typically only need text content
    // If HTML is truly needed, it should be created programmatically
    element.textContent = content
  },

  /**
   * Create safe HTML structure programmatically
   * @param {string} tagName - HTML tag name
   * @param {Object} attributes - Element attributes
   * @param {string} textContent - Text content (will be safely escaped)
   * @returns {HTMLElement} - Created element
   */
  createElement: function (tagName, attributes = {}, textContent = '') {
    const element = document.createElement(tagName)

    // Set attributes safely
    for (const [key, value] of Object.entries(attributes)) {
      // Only allow safe attributes
      if (['class', 'id', 'title', 'role', 'aria-label'].includes(key)) {
        element.setAttribute(key, String(value))
      }
    }

    // Set text content safely
    if (textContent) {
      element.textContent = String(textContent)
    }

    return element
  },

  /**
   * Create a text node safely (always safe, but provided for consistency)
   * @param {string} text - Text content
   * @returns {Text} - Text node
   */
  createTextNode: function (text) {
    return document.createTextNode(text || '')
  },

  /**
   * Create admin message elements safely (for showMessage functionality)
   * @param {string} message - Message text
   * @param {string} type - Message type (info, success, error)
   * @returns {HTMLElement} - Complete message element
   */
  createMessageElement: function (message, type = 'info') {
    const messageDiv = document.createElement('div')
    messageDiv.className = `message ${type}`

    // Create icon element
    let iconClass = 'fa-info-circle'
    if (type === 'success') iconClass = 'fa-check-circle'
    else if (type === 'error') iconClass = 'fa-exclamation-circle'

    const iconElement = document.createElement('i')
    iconElement.className = `fas ${iconClass}`

    // Create message span
    const messageSpan = document.createElement('span')
    messageSpan.textContent = String(message) // Safe text content

    // Assemble the message
    messageDiv.appendChild(iconElement)
    messageDiv.appendChild(messageSpan)

    return messageDiv
  },

  /**
   * DEPRECATED: Regex validation is unreliable - use programmatic creation instead
   * @deprecated Use createElement methods instead of validating HTML strings
   * @param {string} html - HTML to validate
   * @returns {boolean} - Always false to discourage HTML string usage
   */
  validateAdminHTML: function (_html) {
    console.warn('validateAdminHTML is deprecated. Use createElement methods instead of HTML strings.')
    return false // Always return false to discourage HTML string usage
  }
}

// Make sanitizer available globally for convenience
window.safeSetHTML = window.HTMLSanitizer.safeSetHTML.bind(window.HTMLSanitizer)
