// Vote Preview Manager - Material Design 3
// Handles vote preview functionality, sharing, and vote management

class VotePreviewManager {
  constructor() {
    this.API_BASE = '/api'
    this.voteData = window.voteData || {}
    this.snackbar = null
    this.snackbarMessage = null
    this.snackbarAction = null
  }

  static init() {
    const manager = new VotePreviewManager()
    manager.initializeElements()
    manager.initializeEventListeners()
    manager.checkSharingParameter()
  }

  initializeElements() {
    this.snackbar = document.getElementById('snackbar')
    this.snackbarMessage = document.getElementById('snackbar-message')
    this.snackbarAction = document.getElementById('snackbar-action')
  }

  initializeEventListeners() {
    // Global click handler for data-action buttons
    document.addEventListener('click', e => {
      const actionElement = e.target.closest('[data-action]')
      if (actionElement) {
        const action = actionElement.dataset.action
        e.preventDefault()
        this.handleAction(action, actionElement)
      }
    })

    // Snackbar dismiss
    if (this.snackbarAction) {
      this.snackbarAction.addEventListener('click', () => {
        this.dismissSnackbar()
      })
    }

    // Auto-dismiss snackbar after 4 seconds
    this.snackbarTimeout = null

    // Handle escape key for snackbar
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && this.isSnackbarVisible()) {
        this.dismissSnackbar()
      }
    })
  }

  checkSharingParameter() {
    // Check if we came here from vote creation with sharing=true
    const urlParams = new URLSearchParams(window.location.search)
    if (urlParams.get('sharing') === 'true') {
      // Show success message and highlight sharing section
      setTimeout(() => {
        this.showSnackbar('Vote created successfully! Share it below.')
        this.highlightSharingSection()
      }, 500)

      // Remove the parameter from URL without reloading
      const newUrl = window.location.pathname
      history.replaceState({}, '', newUrl)
    }
  }

  handleAction(action, element) {
    switch (action) {
      case 'copy-link':
        this.copyToClipboard(element.dataset.target, 'Link copied to clipboard!')
        break
      case 'copy-code':
        this.copyToClipboard(element.dataset.target, 'Embed code copied to clipboard!')
        break
      case 'share-vote':
        this.openNativeShare()
        break
      case 'activate-vote':
        this.activateVote(element.dataset.voteId)
        break
      case 'vote-settings':
        this.openVoteSettings()
        break
      default:
        console.log('Unhandled action:', action)
    }
  }

  async copyToClipboard(targetId, successMessage) {
    const target = document.getElementById(targetId)
    if (!target) return

    try {
      // Select the text
      target.select()
      target.setSelectionRange(0, 99999) // For mobile devices

      // Try modern clipboard API first
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(target.value)
      } else {
        // Fallback to document.execCommand
        document.execCommand('copy')
      }

      this.showSnackbar(successMessage)

      // Animate the copy button
      const button = document.querySelector(`[data-target="${targetId}"]`)
      if (button) {
        this.animateCopySuccess(button)
      }
    } catch (error) {
      console.error('Failed to copy:', error)
      this.showSnackbar('Failed to copy to clipboard')
    }
  }

  animateCopySuccess(button) {
    const icon = button.querySelector('.material-icons')
    if (icon) {
      const originalIcon = icon.textContent
      icon.textContent = 'check'
      button.classList.add('copy-success')

      setTimeout(() => {
        icon.textContent = originalIcon
        button.classList.remove('copy-success')
      }, 2000)
    }
  }

  async openNativeShare() {
    if (navigator.share && this.voteData.sharing) {
      try {
        await navigator.share({
          title: `Vote: ${this.voteData.title}`,
          text: `Cast your vote on: ${this.voteData.title}`,
          url: this.voteData.sharing.public_url
        })
      } catch (error) {
        // User cancelled or share failed, fallback to showing sharing options
        this.scrollToSharingSection()
      }
    } else {
      this.scrollToSharingSection()
    }
  }

  scrollToSharingSection() {
    const sharingSection = document.querySelector('.sharing-section')
    if (sharingSection) {
      sharingSection.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      })
      this.highlightSharingSection()
    }
  }

  highlightSharingSection() {
    const sharingCards = document.querySelectorAll('.sharing-card')
    sharingCards.forEach(card => {
      card.classList.add('highlight-pulse')
      setTimeout(() => {
        card.classList.remove('highlight-pulse')
      }, 2000)
    })
  }

  async activateVote(voteId) {
    if (!voteId) return

    const button = document.querySelector('[data-action="activate-vote"]')
    const originalText = button ? button.textContent.trim() : ''

    try {
      // Show loading state
      if (button) {
        button.disabled = true
        button.innerHTML = `
          <span class="material-icons rotating">refresh</span>
          Activating...
        `
      }

      const response = await fetch(`${this.API_BASE}/votes/${voteId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.getAccessToken()}`
        },
        body: JSON.stringify({
          status: 'active'
        })
      })

      if (response.ok) {
        this.showSnackbar('Vote activated successfully!')

        // Update the page to reflect the new status
        setTimeout(() => {
          window.location.reload()
        }, 1500)
      } else {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to activate vote')
      }
    } catch (error) {
      console.error('Error activating vote:', error)
      this.showSnackbar(error.message || 'Failed to activate vote')

      // Restore button state
      if (button) {
        button.disabled = false
        button.innerHTML = `
          <span class="material-icons">play_arrow</span>
          ${originalText}
        `
      }
    }
  }

  openVoteSettings() {
    // For now, show a coming soon message
    // In the future, this would open a settings modal
    this.showSnackbar('Vote settings coming soon!')
  }

  showSnackbar(message) {
    if (!this.snackbar || !this.snackbarMessage) return

    this.snackbarMessage.textContent = message
    this.snackbar.classList.add('md-snackbar-visible')

    // Clear existing timeout
    if (this.snackbarTimeout) {
      clearTimeout(this.snackbarTimeout)
    }

    // Auto-dismiss after 4 seconds
    this.snackbarTimeout = setTimeout(() => {
      this.dismissSnackbar()
    }, 4000)
  }

  dismissSnackbar() {
    if (this.snackbar) {
      this.snackbar.classList.remove('md-snackbar-visible')
    }

    if (this.snackbarTimeout) {
      clearTimeout(this.snackbarTimeout)
      this.snackbarTimeout = null
    }
  }

  isSnackbarVisible() {
    return this.snackbar && this.snackbar.classList.contains('md-snackbar-visible')
  }

  getAccessToken() {
    return sessionStorage.getItem('access_token')
  }
}

// Utility functions for animation and effects
document.addEventListener('DOMContentLoaded', function () {
  VotePreviewManager.init()

  // Add fade-in animation to sections
  const sections = document.querySelectorAll(
    '.status-banner, .vote-preview-section, .sharing-section, .settings-section'
  )
  sections.forEach((section, index) => {
    section.style.animationDelay = `${index * 0.1}s`
    section.classList.add('fade-in')
  })

  // Add hover effects to sharing cards
  const sharingCards = document.querySelectorAll('.sharing-card')
  sharingCards.forEach(card => {
    card.addEventListener('mouseenter', () => {
      card.style.transform = 'translateY(-2px)'
    })

    card.addEventListener('mouseleave', () => {
      card.style.transform = 'translateY(0)'
    })
  })

  // Add ripple effect to buttons
  const buttons = document.querySelectorAll('.md-button')
  buttons.forEach(button => {
    button.addEventListener('click', function (e) {
      const ripple = document.createElement('span')
      const rect = button.getBoundingClientRect()
      const size = Math.max(rect.height, rect.width)
      const x = e.clientX - rect.left - size / 2
      const y = e.clientY - rect.top - size / 2

      ripple.style.cssText = `
        position: absolute;
        border-radius: 50%;
        background-color: rgba(255, 255, 255, 0.3);
        transform: scale(0);
        animation: ripple 0.6s linear;
        left: ${x}px;
        top: ${y}px;
        width: ${size}px;
        height: ${size}px;
        pointer-events: none;
      `

      button.style.position = 'relative'
      button.style.overflow = 'hidden'
      button.appendChild(ripple)

      setTimeout(() => {
        ripple.remove()
      }, 600)
    })
  })
})

// Add CSS for animations
const style = document.createElement('style')
style.textContent = `
  @keyframes ripple {
    to {
      transform: scale(4);
      opacity: 0;
    }
  }

  .fade-in {
    opacity: 0;
    transform: translateY(20px);
    animation: fadeInUp 0.6s ease forwards;
  }

  @keyframes fadeInUp {
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .highlight-pulse {
    animation: pulse 2s ease-in-out;
  }

  @keyframes pulse {
    0%, 100% { transform: scale(1); box-shadow: var(--md-elevation-level2); }
    50% { transform: scale(1.02); box-shadow: var(--md-elevation-level3); }
  }

  .rotating {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .copy-success {
    background-color: var(--md-sys-color-tertiary-container) !important;
    color: var(--md-sys-color-on-tertiary-container) !important;
  }
`
document.head.appendChild(style)
