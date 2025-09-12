/**
 * Event Handlers - Centralized event handling for CSP compliance
 * Replaces inline onclick handlers to remove 'unsafe-inline' from CSP
 */

document.addEventListener('DOMContentLoaded', function () {
  // Landing page event handlers
  initializeLandingHandlers()

  // Super admin handlers (if on admin pages)
  initializeSuperAdminHandlers()

  // Public vote handlers
  initializePublicVoteHandlers()

  // Handle special cases like font loading
  initializeSpecialHandlers()
})

/**
 * Landing page event handlers
 */
function initializeLandingHandlers() {
  // Generic action handler
  document.addEventListener('click', function (e) {
    const action = e.target.getAttribute('data-action')
    if (!action) return

    switch (action) {
      // Authentication modals
      case 'show-login':
        if (typeof showLoginModal === 'function') showLoginModal()
        break
      case 'show-register':
        if (typeof showRegisterModal === 'function') showRegisterModal()
        break

      // Navigation
      case 'scroll-to-features':
        if (typeof scrollToFeatures === 'function') scrollToFeatures()
        break

      // Modal controls
      case 'close-modal':
        const modalId = e.target.getAttribute('data-modal')
        if (modalId && typeof closeModal === 'function') closeModal(modalId)
        break

      // Form actions
      case 'show-forgot-password':
        if (typeof showForgotPassword === 'function') showForgotPassword()
        break
      case 'switch-to-register':
        if (typeof switchToRegister === 'function') switchToRegister()
        break
      case 'switch-to-login':
        if (typeof switchToLogin === 'function') switchToLogin()
        break

      // Toast controls
      case 'hide-toast':
        const toastId = e.target.getAttribute('data-toast')
        if (toastId && typeof hideToast === 'function') hideToast(toastId)
        break
    }
  })
}

/**
 * Super Admin event handlers
 */
function initializeSuperAdminHandlers() {
  // Check if we're on an admin page
  if (!document.querySelector('.super-admin-container')) return

  document.addEventListener('click', function (e) {
    const action = e.target.getAttribute('data-action')
    if (!action) return

    switch (action) {
      // Dashboard actions
      case 'open-user-management':
        if (typeof openUserManagement === 'function') openUserManagement()
        break
      case 'bulk-verify-users':
        if (typeof bulkVerifyUsers === 'function') bulkVerifyUsers()
        break
      case 'export-system-stats':
        if (typeof exportSystemStats === 'function') exportSystemStats()
        break
      case 'view-audit-log':
        if (typeof viewAuditLog === 'function') viewAuditLog()
        break

      // Tab switching
      case 'switch-tab':
        const tabName = e.target.getAttribute('data-tab')
        if (tabName && typeof switchTab === 'function') switchTab(tabName)
        break

      // Moderation actions
      case 'refresh-pending-flags':
        if (typeof refreshPendingFlags === 'function') refreshPendingFlags()
        break
      case 'execute-bulk-action':
        if (typeof executeBulkAction === 'function') executeBulkAction()
        break
      case 'clear-bulk-form':
        if (typeof clearBulkForm === 'function') clearBulkForm()
        break

      // Modal controls
      case 'close-flag-review':
        if (typeof closeFlagReviewModal === 'function') closeFlagReviewModal()
        break
      case 'submit-flag-review':
        if (typeof submitFlagReview === 'function') submitFlagReview()
        break
      case 'close-vote-action':
        if (typeof closeVoteActionModal === 'function') closeVoteActionModal()
        break
      case 'submit-moderation-action':
        if (typeof submitModerationAction === 'function') submitModerationAction()
        break

      // Dynamic content actions
      case 'review-flag':
        const flagId = e.target.getAttribute('data-flag-id')
        if (flagId && typeof reviewFlag === 'function') reviewFlag(flagId)
        break
      case 'view-vote-details':
        const voteId = e.target.getAttribute('data-vote-id')
        if (voteId && typeof viewVoteDetails === 'function') viewVoteDetails(voteId)
        break
      case 'take-vote-action':
        const actionVoteId = e.target.getAttribute('data-vote-id')
        if (actionVoteId && typeof takeVoteAction === 'function') takeVoteAction(actionVoteId)
        break
      case 'view-vote-moderation':
        const modVoteId = e.target.getAttribute('data-vote-id')
        if (modVoteId && typeof viewVoteModeration === 'function') viewVoteModeration(modVoteId)
        break
    }
  })

  // Handle change events for filters
  document.addEventListener('change', function (e) {
    const action = e.target.getAttribute('data-action')
    if (action === 'filter-flagged-votes') {
      if (typeof filterFlaggedVotes === 'function') filterFlaggedVotes()
    }
  })
}

/**
 * Public Vote page handlers
 */
function initializePublicVoteHandlers() {
  document.addEventListener('click', function (e) {
    const action = e.target.getAttribute('data-action')
    if (action === 'new-vote') {
      window.location.reload()
    }
  })
}

/**
 * Special handlers for non-click events
 */
function initializeSpecialHandlers() {
  // Handle font loading optimization
  const fontLinks = document.querySelectorAll('[data-onload="font-load"]')
  fontLinks.forEach(link => {
    // When font loads, change media from 'print' to 'all'
    link.addEventListener('load', function () {
      this.media = 'all'
    })
  })
}

/**
 * Utility function to dynamically update content with proper event handlers
 * Call this after injecting new HTML content
 */
function refreshEventHandlers(container) {
  // Re-initialize handlers for dynamically added content
  // This is useful when content is added via AJAX
  if (!container) return

  // Find all elements with data-action attributes in the new content
  const actionElements = container.querySelectorAll('[data-action]')
  actionElements.forEach(element => {
    // The global click handler will handle these automatically
    // But we can add specific initialization here if needed
  })
}

// Export for use in other scripts
window.refreshEventHandlers = refreshEventHandlers
