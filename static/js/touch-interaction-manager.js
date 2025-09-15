/**
 * Touch Interaction Manager - Material Design 3
 * Enhanced touch interactions for T-010
 *
 * Provides natural touch feedback, gesture recognition, and optimized
 * touch event handling for mobile devices following Material Design principles.
 */

class TouchInteractionManager {
  constructor() {
    this.touchStartTime = 0
    this.touchStartPosition = { x: 0, y: 0 }
    this.touchMoveThreshold = 10
    this.longPressThreshold = 500
    this.swipeThreshold = 50
    this.activeTouchTargets = new Set()
    this.longPressTimer = null
    this.isLongPress = false
    this.isSwiping = false

    // Feature detection
    this.isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0
    this.hasHapticFeedback = 'vibrate' in navigator

    this.initializeTouchEvents()
    this.initializeGestureRecognition()
    this.preventDesktopArtifacts()
  }

  static init() {
    if (window.touchInteractionManager) {
      return window.touchInteractionManager
    }

    window.touchInteractionManager = new TouchInteractionManager()
    return window.touchInteractionManager
  }

  // ==========================================================================
  // TOUCH FEEDBACK SYSTEM
  // ==========================================================================

  initializeTouchEvents() {
    if (!this.isTouchDevice) return

    // Touch feedback events
    document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false })
    document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false })
    document.addEventListener('touchcancel', this.handleTouchCancel.bind(this), { passive: false })

    console.log('🤏 Touch interaction manager initialized')
  }

  handleTouchStart(event) {
    const touchTarget = this.findTouchTarget(event.target)
    if (!touchTarget) return

    const touch = event.touches[0]
    this.touchStartTime = Date.now()
    this.touchStartPosition = { x: touch.clientX, y: touch.clientY }
    this.isLongPress = false
    this.isSwiping = false

    // Add immediate touch feedback
    this.addTouchFeedback(touchTarget)
    this.activeTouchTargets.add(touchTarget)

    // Start long press detection
    this.startLongPressDetection(touchTarget, event)

    // Provide haptic feedback for important actions
    this.provideHapticFeedback(touchTarget)
  }

  handleTouchEnd(event) {
    const touchTarget = this.findTouchTarget(event.target)
    if (!touchTarget) return

    // Clear long press timer
    this.clearLongPressTimer()

    // Remove touch feedback with delay for visual confirmation
    setTimeout(() => {
      this.removeTouchFeedback(touchTarget)
      this.activeTouchTargets.delete(touchTarget)
    }, 150)

    // Handle tap if it wasn't a long press or swipe
    if (!this.isLongPress && !this.isSwiping) {
      this.handleTap(touchTarget, event)
    }
  }

  handleTouchCancel(event) {
    // Clean up any active touch states
    this.clearLongPressTimer()
    this.activeTouchTargets.forEach(target => {
      this.removeTouchFeedback(target)
    })
    this.activeTouchTargets.clear()
  }

  findTouchTarget(element) {
    // Find the nearest touch-interactive element
    return element.closest(`
      .md-button, .md-icon-button, .md-text-button,
      button, .touch-target, .clickable,
      .md-card[data-clickable], .vote-option,
      .image-preview-item, .sharing-card,
      .md-menu-item, .option-item,
      .md-text-field, input, textarea,
      .md-fab, .creation-fab
    `)
  }

  addTouchFeedback(element) {
    element.classList.add('touch-active', 'touch-feedback')

    // Add ripple effect for Material Design consistency
    this.createRippleEffect(element)
  }

  removeTouchFeedback(element) {
    element.classList.remove('touch-active')

    // Keep feedback class briefly for animation
    setTimeout(() => {
      element.classList.remove('touch-feedback')
    }, 300)
  }

  createRippleEffect(element) {
    // Skip if element already has active ripple
    if (element.querySelector('.touch-ripple')) return

    const ripple = document.createElement('div')
    ripple.className = 'touch-ripple'

    const rect = element.getBoundingClientRect()
    const size = Math.max(rect.width, rect.height) * 1.2
    const x = this.touchStartPosition.x - rect.left - size / 2
    const y = this.touchStartPosition.y - rect.top - size / 2

    ripple.style.cssText = `
      position: absolute;
      border-radius: 50%;
      background-color: rgba(255, 255, 255, 0.3);
      pointer-events: none;
      left: ${x}px;
      top: ${y}px;
      width: ${size}px;
      height: ${size}px;
      transform: scale(0);
      animation: touch-ripple 0.6s ease-out;
      z-index: 1;
    `

    // Ensure element has relative positioning for ripple
    const computedStyle = getComputedStyle(element)
    if (computedStyle.position === 'static') {
      element.style.position = 'relative'
    }

    element.style.overflow = 'hidden'
    element.appendChild(ripple)

    // Remove ripple after animation
    setTimeout(() => {
      if (ripple.parentNode) {
        ripple.parentNode.removeChild(ripple)
      }
    }, 600)
  }

  provideHapticFeedback(element) {
    if (!this.hasHapticFeedback) return

    // Different feedback intensity based on element importance
    if (element.matches('.md-fab, .danger-button, [data-action="delete"]')) {
      // Strong feedback for important/destructive actions
      navigator.vibrate([10, 50, 10])
    } else if (element.matches('.md-button, button')) {
      // Light feedback for regular buttons
      navigator.vibrate(10)
    }
  }

  // ==========================================================================
  // GESTURE RECOGNITION
  // ==========================================================================

  initializeGestureRecognition() {
    if (!this.isTouchDevice) return

    document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false })

    // Initialize swipe gesture handlers for specific components
    this.initializeImageGallerySwipes()
    this.initializeCardSwipes()
  }

  handleTouchMove(event) {
    if (event.touches.length !== 1) return

    const touch = event.touches[0]
    const deltaX = touch.clientX - this.touchStartPosition.x
    const deltaY = touch.clientY - this.touchStartPosition.y
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY)

    // Cancel long press if touch moved too much
    if (distance > this.touchMoveThreshold) {
      this.clearLongPressTimer()
      this.isLongPress = false
    }

    // Detect swipe gestures
    if (distance > this.swipeThreshold) {
      this.isSwiping = true
      this.handleSwipeGesture(event, deltaX, deltaY)
    }
  }

  handleSwipeGesture(event, deltaX, deltaY) {
    const element = this.findSwipeTarget(event.target)
    if (!element) return

    const isHorizontal = Math.abs(deltaX) > Math.abs(deltaY)

    if (isHorizontal) {
      const direction = deltaX > 0 ? 'right' : 'left'
      this.triggerSwipeEvent(element, direction, event)
    } else {
      const direction = deltaY > 0 ? 'down' : 'up'
      this.triggerSwipeEvent(element, direction, event)
    }
  }

  findSwipeTarget(element) {
    return element.closest(`
      .image-gallery, .image-preview-grid,
      .vote-cards-container, .sharing-options,
      .profile-sections, .swipeable
    `)
  }

  triggerSwipeEvent(element, direction, originalEvent) {
    const swipeEvent = new CustomEvent('swipe', {
      detail: {
        direction,
        element,
        originalEvent,
        deltaX: originalEvent.touches[0].clientX - this.touchStartPosition.x,
        deltaY: originalEvent.touches[0].clientY - this.touchStartPosition.y
      }
    })

    element.dispatchEvent(swipeEvent)
  }

  // ==========================================================================
  // LONG PRESS ACTIONS
  // ==========================================================================

  startLongPressDetection(element, event) {
    this.longPressTimer = setTimeout(() => {
      this.isLongPress = true
      this.handleLongPress(element, event)
    }, this.longPressThreshold)
  }

  clearLongPressTimer() {
    if (this.longPressTimer) {
      clearTimeout(this.longPressTimer)
      this.longPressTimer = null
    }
  }

  handleLongPress(element, event) {
    // Provide stronger haptic feedback for long press
    if (this.hasHapticFeedback) {
      navigator.vibrate([20, 100, 20])
    }

    // Add long press visual feedback
    element.classList.add('long-press-active')

    // Trigger context-appropriate long press actions
    this.triggerLongPressAction(element, event)
  }

  triggerLongPressAction(element, event) {
    // Custom long press event
    const longPressEvent = new CustomEvent('longpress', {
      detail: {
        element,
        originalEvent: event,
        position: this.touchStartPosition
      }
    })

    element.dispatchEvent(longPressEvent)

    // Built-in long press actions
    if (element.matches('.vote-card, .md-card[data-long-press]')) {
      this.showCardContextMenu(element, event)
    } else if (element.matches('.image-preview-item')) {
      this.showImageContextMenu(element, event)
    } else if (element.matches('[data-copyable]')) {
      this.copyToClipboard(element)
    }
  }

  showCardContextMenu(element, event) {
    // Example: Show context menu for vote cards
    console.log('Long press on card:', element.dataset.voteId)

    // In a real implementation, this would show a context menu
    // For now, just provide visual feedback
    this.showTemporaryTooltip(element, 'Long press detected')
  }

  showImageContextMenu(element, event) {
    // Example: Show image options
    console.log('Long press on image:', element.dataset.imageId)

    this.showTemporaryTooltip(element, 'Image options')
  }

  copyToClipboard(element) {
    const textToCopy = element.dataset.copyText || element.textContent

    if (navigator.clipboard) {
      navigator.clipboard.writeText(textToCopy).then(() => {
        this.showTemporaryTooltip(element, 'Copied!')
      })
    }
  }

  showTemporaryTooltip(element, message) {
    const tooltip = document.createElement('div')
    tooltip.className = 'touch-tooltip'
    tooltip.textContent = message

    const rect = element.getBoundingClientRect()
    tooltip.style.cssText = `
      position: fixed;
      background: var(--md-sys-color-inverse-surface);
      color: var(--md-sys-color-inverse-on-surface);
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 14px;
      white-space: nowrap;
      z-index: 10000;
      pointer-events: none;
      left: ${rect.left + rect.width / 2}px;
      top: ${rect.top - 40}px;
      transform: translateX(-50%);
      opacity: 0;
      animation: touch-tooltip-fade 2s ease-out;
    `

    document.body.appendChild(tooltip)

    setTimeout(() => {
      if (tooltip.parentNode) {
        tooltip.parentNode.removeChild(tooltip)
      }
    }, 2000)
  }

  // ==========================================================================
  // SPECIFIC COMPONENT INTEGRATIONS
  // ==========================================================================

  initializeImageGallerySwipes() {
    document.addEventListener('swipe', event => {
      const gallery = event.target.closest('.image-gallery, .image-preview-grid')
      if (!gallery) return

      const { direction } = event.detail

      if (direction === 'left') {
        this.navigateImageGallery(gallery, 'next')
      } else if (direction === 'right') {
        this.navigateImageGallery(gallery, 'prev')
      }
    })
  }

  navigateImageGallery(gallery, direction) {
    // Find current active image or use first
    const images = gallery.querySelectorAll('.image-preview-item')
    const currentIndex = Array.from(images).findIndex(
      img => img.classList.contains('active') || img.classList.contains('selected')
    )

    let nextIndex
    if (direction === 'next') {
      nextIndex = currentIndex < images.length - 1 ? currentIndex + 1 : 0
    } else {
      nextIndex = currentIndex > 0 ? currentIndex - 1 : images.length - 1
    }

    // Update selection with smooth transition
    images.forEach((img, index) => {
      img.classList.toggle('active', index === nextIndex)
      img.classList.toggle('selected', index === nextIndex)
    })

    // Scroll to the selected image
    if (images[nextIndex]) {
      images[nextIndex].scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
        inline: 'center'
      })
    }

    // Provide haptic feedback
    if (this.hasHapticFeedback) {
      navigator.vibrate(5)
    }
  }

  initializeCardSwipes() {
    document.addEventListener('swipe', event => {
      const card = event.target.closest('.vote-card, .swipeable-card')
      if (!card) return

      const { direction } = event.detail

      // Add swipe animation
      card.classList.add('swiping', `swipe-${direction}`)

      // Remove animation class after completion
      setTimeout(() => {
        card.classList.remove('swiping', `swipe-${direction}`)
      }, 300)
    })
  }

  // ==========================================================================
  // DESKTOP ARTIFACT PREVENTION
  // ==========================================================================

  preventDesktopArtifacts() {
    if (!this.isTouchDevice) return

    // Remove hover states on touch devices
    const style = document.createElement('style')
    style.textContent = `
      @media (hover: none) and (pointer: coarse) {
        *:hover {
          /* Reset hover styles on touch devices */
        }

        .md-button:hover,
        button:hover,
        .md-card:hover {
          /* Prevent hover states that don't work on touch */
          background-color: inherit;
          transform: none;
          box-shadow: inherit;
        }
      }
    `
    document.head.appendChild(style)

    // Prevent 300ms click delay on mobile
    document.addEventListener('touchstart', function () {}, { passive: true })
  }

  // ==========================================================================
  // PERFORMANCE OPTIMIZATIONS
  // ==========================================================================

  handleTap(element, event) {
    // Optimize tap handling for performance
    if (element.matches('input, textarea, select')) {
      // Let native focus handling work for form elements
      return
    }

    // Trigger click for other elements to maintain compatibility
    const clickEvent = new MouseEvent('click', {
      bubbles: true,
      cancelable: true,
      view: window
    })

    element.dispatchEvent(clickEvent)
  }

  // ==========================================================================
  // PUBLIC API METHODS
  // ==========================================================================

  enableTouchFeedback(element) {
    if (!element) return
    element.classList.add('touch-enhanced')
  }

  disableTouchFeedback(element) {
    if (!element) return
    element.classList.remove('touch-enhanced', 'touch-active', 'touch-feedback')
  }

  addLongPressHandler(element, callback) {
    if (!element || typeof callback !== 'function') return

    element.addEventListener('longpress', callback)
  }

  addSwipeHandler(element, callback) {
    if (!element || typeof callback !== 'function') return

    element.addEventListener('swipe', callback)
  }

  // Clean up method
  destroy() {
    if (this.longPressTimer) {
      clearTimeout(this.longPressTimer)
    }

    this.activeTouchTargets.clear()

    // Remove event listeners would go here in a full implementation
    console.log('🤏 Touch interaction manager destroyed')
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  TouchInteractionManager.init()
})

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TouchInteractionManager
}
