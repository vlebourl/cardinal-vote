/**
 * Vote Manager - Handles all vote-related operations and UI interactions
 * Manages vote creation, editing, deletion, and real-time updates
 */

class VoteManager {
  constructor() {
    this.API_BASE = '/api'
    this.currentVotes = []
    this.currentFilter = 'all'
    this.currentSort = 'created_at_desc'
    this.currentView = 'grid'
    this.searchQuery = ''

    // Pagination
    this.pagination = {
      page: 1,
      limit: 12,
      total: 0,
      hasMore: false
    }

    // Modal states
    this.isCreateModalOpen = false
    this.isEditModalOpen = false
    this.currentEditVote = null

    // Form state
    this.voteOptions = []
    this.maxOptions = 20
    this.minOptions = 2

    // Event handlers storage
    this.eventHandlers = new Map()

    this.init()
  }

  /**
   * Initialize vote manager
   */
  init() {
    this.setupEventListeners()
    this.setupTemplates()
    this.loadVotes()
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Vote creation
    this.addEventHandler('createNewVoteBtn', 'click', () => {
      this.showCreateModal()
    })

    this.addEventHandler('createFirstVoteBtn', 'click', () => {
      this.showCreateModal()
    })

    // Filter and search
    this.addEventHandler('voteSearchInput', 'input', e => {
      this.handleSearch(e.target.value)
    })

    // Filter chips
    document.querySelectorAll('.md-chip[data-filter]').forEach(chip => {
      this.addEventHandler(chip, 'click', () => {
        this.handleFilterChange(chip.dataset.filter)
      })
    })

    // Sort dropdown
    this.addEventHandler('voteSortSelect', 'change', e => {
      this.handleSortChange(e.target.value)
    })

    // View toggle
    document.querySelectorAll('[data-view]').forEach(button => {
      this.addEventHandler(button, 'click', () => {
        this.handleViewChange(button.dataset.view)
      })
    })

    // Load more
    this.addEventHandler('loadMoreVotesBtn', 'click', () => {
      this.loadMoreVotes()
    })

    // Modal controls
    this.addEventHandler('cancelVoteCreation', 'click', () => {
      this.hideCreateModal()
    })

    this.addEventHandler('saveDraftBtn', 'click', () => {
      this.saveDraft()
    })

    this.addEventHandler('voteCreationForm', 'submit', e => {
      this.handleVoteCreation(e)
    })

    // Vote options
    this.addEventHandler('addOptionBtn', 'click', () => {
      this.addVoteOption()
    })

    // Advanced settings toggle
    this.addEventHandler('advancedToggle', 'click', () => {
      this.toggleAdvancedSettings()
    })

    // Modal close handlers
    document.querySelectorAll('.dialog-close').forEach(button => {
      this.addEventHandler(button, 'click', () => {
        this.hideAllModals()
      })
    })

    // Modal backdrop clicks
    this.addEventHandler('voteCreationModalScrim', 'click', e => {
      if (e.target === e.currentTarget) {
        this.hideCreateModal()
      }
    })
  }

  /**
   * Setup templates
   */
  setupTemplates() {
    this.voteCardTemplate = document.getElementById('voteCardTemplate')
    this.voteListItemTemplate = document.getElementById('voteListItemTemplate')
    this.voteOptionTemplate = document.getElementById('voteOptionTemplate')
    this.voteActionsMenuTemplate = document.getElementById('voteActionsMenuTemplate')

    // Initialize vote options in create modal
    this.initializeVoteOptions()
  }

  /**
   * Load votes with current filters and pagination
   */
  async loadVotes(reset = false) {
    try {
      if (reset) {
        this.pagination.page = 1
        this.currentVotes = []
      }

      this.showVoteListLoading()

      const params = new URLSearchParams({
        limit: this.pagination.limit,
        offset: (this.pagination.page - 1) * this.pagination.limit
      })

      // Only add optional parameters if they have values
      if (this.currentFilter && this.currentFilter !== 'all') {
        params.append('status', this.currentFilter)
      }
      if (this.currentSort) {
        params.append('sort', this.currentSort)
      }
      if (this.searchQuery) {
        params.append('search', this.searchQuery)
      }

      const response = await this.apiRequest(`/dashboard/my-votes?${params}`)

      if (reset) {
        this.currentVotes = response.votes
      } else {
        this.currentVotes = [...this.currentVotes, ...response.votes]
      }

      this.pagination = response.pagination
      this.updateVotesList()
      this.updateFilterCounts(response.counts)
    } catch (error) {
      console.error('Failed to load votes:', error)
      this.showError('Failed to load votes')
    } finally {
      this.hideVoteListLoading()
    }
  }

  /**
   * Load more votes (pagination)
   */
  async loadMoreVotes() {
    if (!this.pagination.hasMore) return

    this.pagination.page++
    await this.loadVotes(false)
  }

  /**
   * Update votes list UI
   */
  updateVotesList() {
    const container = document.getElementById('voteListContainer')
    if (!container) return

    if (this.currentVotes.length === 0) {
      this.showEmptyState()
      return
    }

    const votesHTML = this.currentVotes.map(vote => this.createVoteItem(vote)).join('')

    container.innerHTML = votesHTML

    // Update load more button
    this.updateLoadMoreButton()

    // Setup vote item event listeners
    this.setupVoteItemListeners()
  }

  /**
   * Create vote item HTML based on current view
   */
  createVoteItem(vote) {
    if (this.currentView === 'list') {
      return this.createVoteListItem(vote)
    } else {
      return this.createVoteCard(vote)
    }
  }

  /**
   * Create vote card HTML
   */
  createVoteCard(vote) {
    const template = this.voteCardTemplate.content.cloneNode(true)
    const card = template.querySelector('.vote-card')

    // Set vote ID
    card.dataset.voteId = vote.id

    // Update status
    const statusBadge = card.querySelector('.vote-status-badge')
    const statusDot = statusBadge.querySelector('.status-dot')
    const statusText = statusBadge.querySelector('.status-text')

    statusBadge.dataset.status = vote.status
    statusText.textContent = this.getStatusText(vote.status)

    // Update content
    card.querySelector('.vote-title').textContent = vote.title
    card.querySelector('.vote-description').textContent = vote.description || 'No description'
    card.querySelector('.created-date').textContent = this.formatDate(vote.created_at)
    card.querySelector('.choice-count').textContent = `${vote.choice_count || 0} choices`
    card.querySelector('.response-count').textContent = `${vote.response_count || 0} responses`

    // Update stats if available
    if (vote.stats) {
      const statsSection = card.querySelector('.vote-stats')
      statsSection.style.display = 'block'
      card.querySelector('.participation-rate').textContent = `${vote.stats.participation_rate || 0}%`
      card.querySelector('.avg-rating').textContent = (vote.stats.avg_rating || 0).toFixed(1)
      card.querySelector('.completion-rate').textContent = `${vote.stats.completion_rate || 0}%`
    }

    // Update progress for active votes
    if (vote.status === 'active' && vote.progress) {
      const progressSection = card.querySelector('.vote-progress')
      progressSection.style.display = 'block'
      card.querySelector('.progress-percentage').textContent = `${vote.progress.percentage || 0}%`
      card.querySelector('.progress-fill').style.width = `${vote.progress.percentage || 0}%`
    }

    // Update primary action based on status
    const primaryAction = card.querySelector('.primary-action')
    this.updatePrimaryAction(primaryAction, vote)

    // Show/hide secondary actions based on status
    this.updateSecondaryActions(card, vote)

    return card.outerHTML
  }

  /**
   * Create vote list item HTML
   */
  createVoteListItem(vote) {
    const template = this.voteListItemTemplate.content.cloneNode(true)
    const item = template.querySelector('.vote-list-item')

    // Set vote ID
    item.dataset.voteId = vote.id

    // Update status indicator
    const statusIndicator = item.querySelector('.vote-status-indicator')
    statusIndicator.dataset.status = vote.status

    // Update content
    item.querySelector('.vote-title').textContent = vote.title
    item.querySelector('.vote-description').textContent = vote.description || 'No description'
    item.querySelector('.created-date').textContent = this.formatDate(vote.created_at)
    item.querySelector('.choice-count').textContent = `${vote.choice_count || 0} choices`
    item.querySelector('.response-count').textContent = `${vote.response_count || 0} responses`

    // Update quick stats
    item.querySelector('.participation-rate').textContent = `${vote.stats?.participation_rate || 0}%`
    item.querySelector('.avg-rating').textContent = (vote.stats?.avg_rating || 0).toFixed(1)

    // Update primary action
    const primaryAction = item.querySelector('.primary-action')
    this.updatePrimaryAction(primaryAction, vote)

    return item.outerHTML
  }

  /**
   * Update primary action button based on vote status
   */
  updatePrimaryAction(button, vote) {
    const icon = button.querySelector('.action-icon')
    const text = button.querySelector('.action-text')

    switch (vote.status) {
      case 'draft':
        button.dataset.action = 'publish'
        icon.textContent = 'publish'
        text.textContent = 'Publish'
        button.className = 'md-button md-button-filled primary-action'
        break
      case 'active':
        button.dataset.action = 'view'
        icon.textContent = 'visibility'
        text.textContent = 'View'
        button.className = 'md-button md-button-outlined primary-action'
        break
      case 'closed':
        button.dataset.action = 'results'
        icon.textContent = 'analytics'
        text.textContent = 'Results'
        button.className = 'md-button md-button-outlined primary-action'
        break
      default:
        button.dataset.action = 'view'
        icon.textContent = 'visibility'
        text.textContent = 'View'
        button.className = 'md-button md-button-outlined primary-action'
    }
  }

  /**
   * Update secondary actions based on vote status
   */
  updateSecondaryActions(card, vote) {
    const editBtn = card.querySelector('[data-action="edit"]')

    // Show edit button only for drafts
    if (vote.status === 'draft') {
      editBtn.style.display = 'inline-flex'
    } else {
      editBtn.style.display = 'none'
    }
  }

  /**
   * Setup event listeners for vote items
   */
  setupVoteItemListeners() {
    // Primary action buttons
    document.querySelectorAll('.primary-action').forEach(button => {
      button.addEventListener('click', e => {
        const voteId = e.target.closest('[data-vote-id]').dataset.voteId
        const action = button.dataset.action
        this.handleVoteAction(voteId, action)
      })
    })

    // Secondary action buttons
    document.querySelectorAll('[data-action]').forEach(button => {
      if (!button.classList.contains('primary-action')) {
        button.addEventListener('click', e => {
          const voteId = e.target.closest('[data-vote-id]').dataset.voteId
          const action = button.dataset.action
          this.handleVoteAction(voteId, action)
        })
      }
    })

    // Vote menu buttons
    document.querySelectorAll('.vote-menu-btn').forEach(button => {
      button.addEventListener('click', e => {
        const voteId = e.target.closest('[data-vote-id]').dataset.voteId
        this.showVoteMenu(voteId, e.target)
      })
    })
  }

  /**
   * Handle vote actions
   */
  async handleVoteAction(voteId, action) {
    const vote = this.currentVotes.find(v => v.id === voteId)
    if (!vote) return

    try {
      switch (action) {
        case 'view':
          this.viewVote(voteId)
          break
        case 'edit':
          this.editVote(vote)
          break
        case 'publish':
          await this.publishVote(voteId)
          break
        case 'close':
          await this.closeVote(voteId)
          break
        case 'results':
          this.viewResults(voteId)
          break
        case 'analytics':
          this.viewAnalytics(voteId)
          break
        case 'share':
          this.shareVote(voteId)
          break
        case 'duplicate':
          await this.duplicateVote(voteId)
          break
        case 'export':
          await this.exportVote(voteId)
          break
        case 'archive':
          await this.archiveVote(voteId)
          break
        case 'delete':
          await this.deleteVote(voteId)
          break
        default:
          console.warn('Unknown vote action:', action)
      }
    } catch (error) {
      console.error(`Failed to execute action ${action} on vote ${voteId}:`, error)
      this.showError(`Failed to ${action} vote`)
    }
  }

  /**
   * Show vote creation modal
   */
  showCreateModal() {
    const modal = document.getElementById('voteCreationModalScrim')
    if (modal) {
      modal.style.display = 'flex'
      modal.setAttribute('aria-hidden', 'false')
      document.body.style.overflow = 'hidden'
      this.isCreateModalOpen = true

      // Focus first input
      const firstInput = document.getElementById('newVoteTitle')
      if (firstInput) {
        setTimeout(() => firstInput.focus(), 100)
      }
    }
  }

  /**
   * Hide vote creation modal
   */
  hideCreateModal() {
    const modal = document.getElementById('voteCreationModalScrim')
    if (modal) {
      modal.style.display = 'none'
      modal.setAttribute('aria-hidden', 'true')
      document.body.style.overflow = ''
      this.isCreateModalOpen = false

      // Reset form
      this.resetCreateForm()
    }
  }

  /**
   * Hide all modals
   */
  hideAllModals() {
    this.hideCreateModal()
    // Hide other modals as they're implemented
  }

  /**
   * Initialize vote options in create modal
   */
  initializeVoteOptions() {
    this.voteOptions = []
    this.addVoteOption()
    this.addVoteOption()
    this.updateOptionCounter()
  }

  /**
   * Add vote option
   */
  addVoteOption() {
    if (this.voteOptions.length >= this.maxOptions) {
      this.showError(`Maximum ${this.maxOptions} options allowed`)
      return
    }

    const template = this.voteOptionTemplate.content.cloneNode(true)
    const optionField = template.querySelector('.vote-option-field')
    const input = optionField.querySelector('.option-text')
    const removeBtn = optionField.querySelector('.remove-option')

    // Set up remove button
    removeBtn.addEventListener('click', () => {
      this.removeVoteOption(optionField)
    })

    // Add to container
    const container = document.getElementById('voteOptionsContainer')
    container.appendChild(optionField)

    this.voteOptions.push({
      element: optionField,
      input
    })

    this.updateOptionCounter()
    this.updateAddOptionButton()

    // Focus new input
    input.focus()
  }

  /**
   * Remove vote option
   */
  removeVoteOption(optionElement) {
    if (this.voteOptions.length <= this.minOptions) {
      this.showError(`Minimum ${this.minOptions} options required`)
      return
    }

    // Remove from array
    this.voteOptions = this.voteOptions.filter(option => option.element !== optionElement)

    // Remove from DOM
    optionElement.remove()

    this.updateOptionCounter()
    this.updateAddOptionButton()
  }

  /**
   * Update option counter
   */
  updateOptionCounter() {
    const counter = document.getElementById('optionCount')
    if (counter) {
      counter.textContent = this.voteOptions.length
    }
  }

  /**
   * Update add option button state
   */
  updateAddOptionButton() {
    const button = document.getElementById('addOptionBtn')
    if (button) {
      button.disabled = this.voteOptions.length >= this.maxOptions
    }
  }

  /**
   * Toggle advanced settings
   */
  toggleAdvancedSettings() {
    const content = document.getElementById('advancedContent')
    const toggle = document.getElementById('advancedToggle')
    const icon = toggle.querySelector('.material-icons')

    if (content.style.display === 'none') {
      content.style.display = 'block'
      icon.textContent = 'expand_less'
    } else {
      content.style.display = 'none'
      icon.textContent = 'expand_more'
    }
  }

  /**
   * Handle vote creation form submission
   */
  async handleVoteCreation(e) {
    e.preventDefault()

    try {
      this.showVoteActionLoading('Creating vote...')

      const formData = this.getVoteFormData()
      const validationErrors = this.validateVoteForm(formData)

      if (validationErrors.length > 0) {
        this.showFormErrors(validationErrors)
        return
      }

      const response = await this.apiRequest('/votes', {
        method: 'POST',
        body: JSON.stringify(formData)
      })

      this.hideCreateModal()
      this.showSuccess('Vote created successfully!')

      // Refresh votes list
      await this.loadVotes(true)

      // Navigate to vote if published
      if (formData.status === 'published') {
        setTimeout(() => {
          window.open(`/vote/${response.id}`, '_blank')
        }, 1000)
      }
    } catch (error) {
      console.error('Failed to create vote:', error)
      this.showError('Failed to create vote')
    } finally {
      this.hideVoteActionLoading()
    }
  }

  /**
   * Save vote as draft
   */
  async saveDraft() {
    try {
      this.showVoteActionLoading('Saving draft...')

      const formData = this.getVoteFormData()
      formData.status = 'draft'

      // Basic validation for drafts
      if (!formData.title.trim()) {
        this.showFormErrors(['Vote title is required'])
        return
      }

      const response = await this.apiRequest('/votes', {
        method: 'POST',
        body: JSON.stringify(formData)
      })

      this.hideCreateModal()
      this.showSuccess('Draft saved successfully!')

      // Refresh votes list
      await this.loadVotes(true)
    } catch (error) {
      console.error('Failed to save draft:', error)
      this.showError('Failed to save draft')
    } finally {
      this.hideVoteActionLoading()
    }
  }

  /**
   * Get vote form data
   */
  getVoteFormData() {
    const form = document.getElementById('voteCreationForm')
    const formData = new FormData(form)

    const data = {
      title: formData.get('title') || document.getElementById('newVoteTitle').value,
      description: formData.get('description') || document.getElementById('newVoteDescription').value,
      options: this.voteOptions
        .map(option => ({
          text: option.input.value.trim()
        }))
        .filter(option => option.text),
      settings: {
        allow_multiple_choices: document.getElementById('allowMultipleChoices').checked,
        require_auth: document.getElementById('requireAuth').checked,
        show_results: document.getElementById('showResults').checked,
        allow_comments: document.getElementById('allowComments').checked,
        close_date: document.getElementById('voteCloseDate').value || null,
        access_code: document.getElementById('accessCode').value || null,
        max_responses: document.getElementById('maxResponses').value || null
      },
      status: 'published' // Default to published, can be overridden
    }

    return data
  }

  /**
   * Validate vote form
   */
  validateVoteForm(data) {
    const errors = []

    // Title validation
    if (!data.title || data.title.trim().length === 0) {
      errors.push('Vote title is required')
    } else if (data.title.trim().length > 200) {
      errors.push('Vote title must be 200 characters or less')
    }

    // Description validation
    if (data.description && data.description.length > 1000) {
      errors.push('Vote description must be 1000 characters or less')
    }

    // Options validation
    if (data.options.length < this.minOptions) {
      errors.push(`At least ${this.minOptions} options are required`)
    }

    if (data.options.length > this.maxOptions) {
      errors.push(`Maximum ${this.maxOptions} options allowed`)
    }

    // Check for duplicate options
    const optionTexts = data.options.map(opt => opt.text.toLowerCase())
    const uniqueTexts = new Set(optionTexts)
    if (optionTexts.length !== uniqueTexts.size) {
      errors.push('Duplicate options are not allowed')
    }

    // Check option text length
    for (const option of data.options) {
      if (option.text.length > 200) {
        errors.push('Option text must be 200 characters or less')
      }
    }

    // Date validation
    if (data.settings.close_date) {
      const closeDate = new Date(data.settings.close_date)
      const now = new Date()
      if (closeDate <= now) {
        errors.push('Close date must be in the future')
      }
    }

    // Max responses validation
    if (data.settings.max_responses && data.settings.max_responses < 1) {
      errors.push('Maximum responses must be at least 1')
    }

    return errors
  }

  /**
   * Show form errors
   */
  showFormErrors(errors) {
    const errorsContainer = document.getElementById('voteCreationErrors')
    const errorsList = document.getElementById('errorMessagesList')

    if (errorsContainer && errorsList) {
      errorsList.innerHTML = errors.map(error => `<div class="error-message">${this.escapeHtml(error)}</div>`).join('')
      errorsContainer.style.display = 'block'
    }
  }

  /**
   * Reset create form
   */
  resetCreateForm() {
    const form = document.getElementById('voteCreationForm')
    if (form) {
      form.reset()
    }

    // Clear vote options
    const container = document.getElementById('voteOptionsContainer')
    if (container) {
      container.innerHTML = ''
    }

    // Reset options array and reinitialize
    this.voteOptions = []
    this.initializeVoteOptions()

    // Hide errors
    const errorsContainer = document.getElementById('voteCreationErrors')
    if (errorsContainer) {
      errorsContainer.style.display = 'none'
    }

    // Reset advanced settings
    const advancedContent = document.getElementById('advancedContent')
    if (advancedContent) {
      advancedContent.style.display = 'none'
    }
  }

  /**
   * Handle filter changes
   */
  handleFilterChange(filter) {
    if (this.currentFilter === filter) return

    this.currentFilter = filter
    this.updateFilterUI()
    this.loadVotes(true)
  }

  /**
   * Handle sort changes
   */
  handleSortChange(sort) {
    if (this.currentSort === sort) return

    this.currentSort = sort
    this.loadVotes(true)
  }

  /**
   * Handle view changes
   */
  handleViewChange(view) {
    if (this.currentView === view) return

    this.currentView = view
    this.updateViewUI()
    this.updateVotesList()
  }

  /**
   * Handle search
   */
  handleSearch(query) {
    this.searchQuery = query

    // Debounce search
    clearTimeout(this.searchTimeout)
    this.searchTimeout = setTimeout(() => {
      this.loadVotes(true)
    }, 500)
  }

  /**
   * Update filter UI
   */
  updateFilterUI() {
    document.querySelectorAll('.md-chip[data-filter]').forEach(chip => {
      if (chip.dataset.filter === this.currentFilter) {
        chip.classList.add('md-chip-selected')
      } else {
        chip.classList.remove('md-chip-selected')
      }
    })
  }

  /**
   * Update view UI
   */
  updateViewUI() {
    document.querySelectorAll('[data-view]').forEach(button => {
      if (button.dataset.view === this.currentView) {
        button.classList.add('md-segmented-button-selected')
      } else {
        button.classList.remove('md-segmented-button-selected')
      }
    })

    // Update container class
    const container = document.getElementById('voteListContainer')
    if (container) {
      container.className = this.currentView === 'list' ? 'vote-list' : 'vote-grid'
    }
  }

  /**
   * Update filter counts
   */
  updateFilterCounts(counts) {
    if (!counts) return

    this.updateElement('allVotesCount', counts.all || 0)
    this.updateElement('draftVotesCount', counts.draft || 0)
    this.updateElement('activeVotesCount', counts.active || 0)
    this.updateElement('closedVotesCount', counts.closed || 0)
  }

  /**
   * Update load more button
   */
  updateLoadMoreButton() {
    const container = document.getElementById('loadMoreVotesContainer')
    if (container) {
      container.style.display = this.pagination.hasMore ? 'block' : 'none'
    }
  }

  /**
   * Vote action methods
   */
  viewVote(voteId) {
    window.open(`/vote/${voteId}`, '_blank')
  }

  async editVote(vote) {
    // Implementation for edit modal
    this.showError('Edit functionality coming soon!')
  }

  async publishVote(voteId) {
    if (!confirm('Are you sure you want to publish this vote? It will become active and visible to voters.')) {
      return
    }

    try {
      await this.apiRequest(`/dashboard/votes/${voteId}/publish`, {
        method: 'POST'
      })

      this.showSuccess('Vote published successfully!')
      await this.loadVotes(true)
    } catch (error) {
      console.error('Failed to publish vote:', error)
      this.showError('Failed to publish vote')
    }
  }

  async closeVote(voteId) {
    if (!confirm('Are you sure you want to close this vote? This action cannot be undone.')) {
      return
    }

    try {
      await this.apiRequest(`/dashboard/votes/${voteId}/close`, {
        method: 'POST',
        body: JSON.stringify({
          send_notifications: true
        })
      })

      this.showSuccess('Vote closed successfully!')
      await this.loadVotes(true)
    } catch (error) {
      console.error('Failed to close vote:', error)
      this.showError('Failed to close vote')
    }
  }

  async deleteVote(voteId) {
    const vote = this.currentVotes.find(v => v.id === voteId)
    if (!vote) return

    const message =
      vote.response_count > 0
        ? `Are you sure you want to delete "${vote.title}"? This vote has ${vote.response_count} responses and this action cannot be undone.`
        : `Are you sure you want to delete "${vote.title}"? This action cannot be undone.`

    if (!confirm(message)) {
      return
    }

    try {
      await this.apiRequest(`/dashboard/votes/${voteId}`, {
        method: 'DELETE'
      })

      this.showSuccess('Vote deleted successfully!')
      await this.loadVotes(true)
    } catch (error) {
      console.error('Failed to delete vote:', error)
      this.showError('Failed to delete vote')
    }
  }

  viewResults(voteId) {
    window.open(`/vote/${voteId}/results`, '_blank')
  }

  viewAnalytics(voteId) {
    if (window.dashboardController) {
      window.dashboardController.showSection('analytics')
      // Set analytics to show this specific vote
    }
  }

  shareVote(voteId) {
    const vote = this.currentVotes.find(v => v.id === voteId)
    if (!vote) return

    const shareUrl = `${window.location.origin}/vote/${voteId}`

    if (navigator.share) {
      navigator.share({
        title: vote.title,
        text: vote.description || `Vote on: ${vote.title}`,
        url: shareUrl
      })
    } else {
      // Fallback to clipboard
      navigator.clipboard
        .writeText(shareUrl)
        .then(() => {
          this.showSuccess('Share link copied to clipboard!')
        })
        .catch(() => {
          this.showError('Failed to copy share link')
        })
    }
  }

  async duplicateVote(voteId) {
    try {
      const response = await this.apiRequest(`/dashboard/votes/${voteId}/duplicate`, {
        method: 'POST'
      })

      this.showSuccess('Vote duplicated successfully!')
      await this.loadVotes(true)
    } catch (error) {
      console.error('Failed to duplicate vote:', error)
      this.showError('Failed to duplicate vote')
    }
  }

  async exportVote(voteId) {
    try {
      const response = await fetch(`${this.API_BASE}/dashboard/votes/${voteId}/export`, {
        headers: {
          Authorization: `Bearer ${this.getToken()}`
        }
      })

      if (!response.ok) throw new Error('Export failed')

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `vote-${voteId}-export.csv`
      a.click()
      URL.revokeObjectURL(url)

      this.showSuccess('Vote data exported successfully!')
    } catch (error) {
      console.error('Failed to export vote:', error)
      this.showError('Failed to export vote data')
    }
  }

  /**
   * Handle real-time updates
   */
  handleRealtimeUpdate(data) {
    if (data.vote_id) {
      const voteIndex = this.currentVotes.findIndex(v => v.id === data.vote_id)
      if (voteIndex !== -1) {
        // Update vote data
        if (data.response_count !== undefined) {
          this.currentVotes[voteIndex].response_count = data.response_count
        }
        if (data.status) {
          this.currentVotes[voteIndex].status = data.status
        }

        // Update UI
        this.updateVoteItem(data.vote_id, data)
      }
    }
  }

  /**
   * Update specific vote item in UI
   */
  updateVoteItem(voteId, data) {
    const voteElement = document.querySelector(`[data-vote-id="${voteId}"]`)
    if (!voteElement) return

    // Update response count
    if (data.response_count !== undefined) {
      const responseCountEl = voteElement.querySelector('.response-count')
      if (responseCountEl) {
        responseCountEl.textContent = `${data.response_count} responses`
      }
    }

    // Update status
    if (data.status) {
      const statusBadge = voteElement.querySelector('.vote-status-badge')
      if (statusBadge) {
        statusBadge.dataset.status = data.status
        const statusText = statusBadge.querySelector('.status-text')
        if (statusText) {
          statusText.textContent = this.getStatusText(data.status)
        }
      }
    }
  }

  /**
   * Update vote response count (called by real-time client)
   */
  updateVoteResponseCount(voteId, responseCount) {
    this.updateVoteItem(voteId, { response_count: responseCount })
  }

  /**
   * Show empty state
   */
  showEmptyState() {
    const container = document.getElementById('voteListContainer')
    const emptyState = document.getElementById('voteListEmpty')

    if (container) container.innerHTML = ''

    if (emptyState) {
      // Update message based on current filter
      const message = document.getElementById('emptyStateMessage')
      if (message) {
        switch (this.currentFilter) {
          case 'draft':
            message.textContent = 'No draft votes found. Create a new vote to get started.'
            break
          case 'active':
            message.textContent = 'No active votes found. Publish a draft or create a new vote.'
            break
          case 'closed':
            message.textContent = 'No closed votes found. Votes will appear here after they are closed.'
            break
          default:
            message.textContent = 'No votes found. Create your first vote to get started.'
        }
      }

      emptyState.style.display = 'block'
    }
  }

  /**
   * Show/hide loading states
   */
  showVoteListLoading() {
    const loading = document.getElementById('voteListLoading')
    if (loading) loading.style.display = 'block'
  }

  hideVoteListLoading() {
    const loading = document.getElementById('voteListLoading')
    if (loading) loading.style.display = 'none'
  }

  showVoteActionLoading(message = 'Processing...') {
    const overlay = document.getElementById('voteActionLoading')
    const messageEl = document.getElementById('loadingMessage')

    if (overlay) overlay.style.display = 'flex'
    if (messageEl) messageEl.textContent = message
  }

  hideVoteActionLoading() {
    const overlay = document.getElementById('voteActionLoading')
    if (overlay) overlay.style.display = 'none'
  }

  /**
   * Utility methods
   */
  async apiRequest(endpoint, options = {}) {
    const token = this.getToken()

    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers
      }
    }

    const response = await fetch(`${this.API_BASE}${endpoint}`, {
      ...defaultOptions,
      ...options
    })

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`)
    }

    return await response.json()
  }

  getToken() {
    return localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
  }

  addEventHandler(elementOrId, event, handler) {
    const element = typeof elementOrId === 'string' ? document.getElementById(elementOrId) : elementOrId

    if (element) {
      element.addEventListener(event, handler)

      const key = `${elementOrId}-${event}`
      this.eventHandlers.set(key, { element, event, handler })
    }
  }

  updateElement(id, content) {
    const element = document.getElementById(id)
    if (element) {
      element.textContent = content
    }
  }

  getStatusText(status) {
    const statusMap = {
      draft: 'Draft',
      active: 'Active',
      closed: 'Closed',
      completed: 'Completed'
    }
    return statusMap[status] || 'Unknown'
  }

  formatDate(dateString) {
    const date = new Date(dateString)
    return date.toLocaleDateString()
  }

  escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;')
  }

  showSuccess(message) {
    if (window.dashboardController) {
      window.dashboardController.showSnackbar(message, 'success')
    }
  }

  showError(message) {
    if (window.dashboardController) {
      window.dashboardController.showSnackbar(message, 'error')
    }
  }

  /**
   * Cleanup method
   */
  cleanup() {
    // Clear timeouts
    if (this.searchTimeout) clearTimeout(this.searchTimeout)

    // Remove event listeners
    this.eventHandlers.forEach(({ element, event, handler }) => {
      element.removeEventListener(event, handler)
    })
    this.eventHandlers.clear()
  }
}

// Export for use in other modules
window.VoteManager = VoteManager
