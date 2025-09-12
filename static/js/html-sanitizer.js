/**
 * HTML Sanitization Utilities for Admin Interface
 * Provides secure HTML manipulation to prevent XSS attacks
 */

window.HTMLSanitizer = {
  /**
   * Sanitize HTML content for admin interface usage
   * Removes dangerous script tags, javascript: URLs, and event handlers
   * @param {string} html - HTML content to sanitize
   * @returns {string} - Sanitized HTML content
   */
  sanitizeAdminHTML: function (html) {
    if (typeof html !== 'string') {
      return ''
    }

    let sanitized = html

    // Remove script tags and their content
    sanitized = sanitized.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')

    // Remove javascript: URLs
    sanitized = sanitized.replace(/javascript:/gi, '')

    // Remove all event handlers (onclick, onload, etc.)
    sanitized = sanitized.replace(/on\w+\s*=/gi, '')

    // Remove data: URLs that could contain HTML/JS
    sanitized = sanitized.replace(/data:\s*text\/html/gi, '')

    // Remove vbscript: URLs
    sanitized = sanitized.replace(/vbscript:/gi, '')

    return sanitized
  },

  /**
   * Safely set innerHTML with sanitization
   * @param {HTMLElement} element - DOM element to update
   * @param {string} html - HTML content to set
   */
  safeSetHTML: function (element, html) {
    if (!element || typeof html !== 'string') {
      return
    }

    const sanitizedHTML = this.sanitizeAdminHTML(html)
    element.innerHTML = sanitizedHTML
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
   * Validate that admin HTML content is safe
   * Used for validating content before display
   * @param {string} html - HTML to validate
   * @returns {boolean} - True if content appears safe
   */
  validateAdminHTML: function (html) {
    if (typeof html !== 'string') {
      return false
    }

    // Check for dangerous patterns
    const dangerousPatterns = [
      /<script/i,
      /javascript:/i,
      /on\w+\s*=/i,
      /data:\s*text\/html/i,
      /vbscript:/i,
      /<iframe/i,
      /<object/i,
      /<embed/i,
      /<applet/i
    ]

    return !dangerousPatterns.some(pattern => pattern.test(html))
  }
}

// Make sanitizer available globally for convenience
window.safeSetHTML = window.HTMLSanitizer.safeSetHTML.bind(window.HTMLSanitizer)
