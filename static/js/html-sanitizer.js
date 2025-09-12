/**
 * HTML Sanitizer utility for safe DOM manipulation
 * Prevents XSS attacks by sanitizing HTML content before insertion
 */

window.HTMLSanitizer = {
    // Basic HTML sanitization - removes dangerous elements and attributes
    sanitizeHTML: function(html) {
        // Create a temporary DOM element to parse HTML safely
        const temp = document.createElement('div');
        temp.textContent = html; // This escapes all HTML

        // For now, we're being very conservative and escaping all HTML
        // In a real implementation, you might want to allow certain safe tags
        return temp.innerHTML;
    },

    // Safe way to set HTML content
    safeSetHTML: function(element, html) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }

        if (!element) {
            console.error('Element not found for safeSetHTML');
            return;
        }

        // For trusted admin content, we'll allow HTML but with basic validation
        // This is a simplified approach - in production you'd want a proper HTML sanitizer
        const sanitized = this.validateAdminHTML(html);
        element.innerHTML = sanitized;
    },

    // Validate HTML content from trusted admin sources
    validateAdminHTML: function(html) {
        // Remove script tags and javascript: URLs
        let sanitized = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
        sanitized = sanitized.replace(/javascript:/gi, '');
        sanitized = sanitized.replace(/on\w+\s*=/gi, ''); // Remove event handlers

        return sanitized;
    },

    // Safe way to set text content (no HTML)
    safeSetText: function(element, text) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }

        if (!element) {
            console.error('Element not found for safeSetText');
            return;
        }

        element.textContent = text;
    },

    // Create element safely with text content
    createElement: function(tagName, textContent, className) {
        const element = document.createElement(tagName);
        if (textContent) {
            element.textContent = textContent;
        }
        if (className) {
            element.className = className;
        }
        return element;
    },

    // Build HTML structure safely using DOM methods
    buildElement: function(config) {
        const element = document.createElement(config.tag || 'div');

        if (config.text) {
            element.textContent = config.text;
        }

        if (config.className) {
            element.className = config.className;
        }

        if (config.attributes) {
            for (const [key, value] of Object.entries(config.attributes)) {
                element.setAttribute(key, value);
            }
        }

        if (config.children) {
            config.children.forEach(childConfig => {
                const child = this.buildElement(childConfig);
                element.appendChild(child);
            });
        }

        return element;
    }
};

// Global helper functions
window.safeSetHTML = window.HTMLSanitizer.safeSetHTML;
window.safeSetText = window.HTMLSanitizer.safeSetText;
