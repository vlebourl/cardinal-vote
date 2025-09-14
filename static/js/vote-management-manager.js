// Vote Management JavaScript
// Handles vote management functionality, editing, deletion, and results visualization

class VoteManagementManager {
  constructor() {
    this.API_BASE = '/api'
    this.currentFilter = 'all'
    this.currentSort = 'created_at'
    this.currentPage = 1
    this.itemsPerPage = 20
    this.hasMoreItems = true
    this.isLoading = false
    this.votes = []

    // Chart instances for cleanup
    this.barChart = null
    this.pieChart = null

    // Polling interval for real-time updates
    this.resultsPollingInterval = null
  }

  static init() {
    const voteManager = new VoteManagementManager()
    voteManager.initializeElements()
    voteManager.initializeEventListeners()
    voteManager.loadVotes()

    // Make available globally for DashboardManager
    window.voteManager = voteManager
    return voteManager
  }

  initializeElements() {
    this.voteList = document.getElementById('voteList')
    this.loadingState = document.getElementById('voteListLoading')
    this.emptyState = document.getElementById('voteListEmpty')
    this.loadMoreContainer = document.getElementById('loadMoreContainer')
    this.loadMoreBtn = document.getElementById('loadMoreBtn')
    this.sortSelect = document.getElementById('sortSelect')

    // Modal elements
    this.editModal = document.getElementById('editVoteModalScrim')
    this.deleteModal = document.getElementById('deleteVoteModalScrim')
    this.resultsModal = document.getElementById('resultsModalScrim')
  }

  initializeEventListeners() {
    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', e => {
        const filter = e.target.dataset.filter
        this.setActiveFilter(filter)
        this.filterVotes(filter)
      })
    })

    // Sort dropdown
    if (this.sortSelect) {
      this.sortSelect.addEventListener('change', e => {
        this.currentSort = e.target.value
        this.resetAndReload()
      })
    }

    // Edit form submission
    const editForm = document.getElementById('editVoteForm')
    if (editForm) {
      editForm.addEventListener('submit', e => {
        e.preventDefault()
        this.saveVoteChanges()
      })
    }

    // Access code toggle in edit modal
    const editUseAccessCode = document.getElementById('editUseAccessCode')
    if (editUseAccessCode) {
      editUseAccessCode.addEventListener('change', e => {
        const accessCodeField = document.getElementById('editAccessCodeField')
        if (accessCodeField) {
          accessCodeField.style.display = e.target.checked ? 'block' : 'none'
        }
      })
    }
  }

  setActiveFilter(filter) {
    // Update button states
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.classList.remove('active')
      if (btn.dataset.filter === filter) {
        btn.classList.remove('md-button-outlined')
        btn.classList.add('md-button-filled', 'active')
      } else {
        btn.classList.remove('md-button-filled')
        btn.classList.add('md-button-outlined')
      }
    })
    this.currentFilter = filter
  }

  async filterVotes(filter) {
    this.currentFilter = filter
    this.resetAndReload()
  }

  resetAndReload() {
    this.currentPage = 1
    this.hasMoreItems = true
    this.votes = []
    this.clearVoteList()
    this.loadVotes()
  }

  async loadVotes(append = false) {
    if (this.isLoading) return

    this.isLoading = true
    this.showLoadingState(!append)

    const token = this.getAccessToken()
    if (!token) {
      this.redirectToLogin()
      return
    }

    try {
      const params = new URLSearchParams({
        page: this.currentPage,
        limit: this.itemsPerPage,
        sort: this.currentSort,
        order: 'desc'
      })

      if (this.currentFilter !== 'all') {
        params.append('status', this.currentFilter)
      }

      const response = await fetch(`${this.API_BASE}/votes/?${params}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        const newVotes = data.votes || []

        if (append) {
          this.votes = [...this.votes, ...newVotes]
        } else {
          this.votes = newVotes
        }

        this.hasMoreItems = newVotes.length === this.itemsPerPage
        this.renderVotes()
        this.updateLoadMoreButton()
      } else if (response.status === 401) {
        this.clearTokens()
        this.redirectToLogin()
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      console.error('Failed to load votes:', error)
      this.showSnackbar('Failed to load votes. Please try again.')
      this.showEmptyState()
    } finally {
      this.isLoading = false
      this.hideLoadingState()
    }
  }

  renderVotes() {
    if (this.votes.length === 0) {
      this.showEmptyState()
      return
    }

    this.hideEmptyState()
    const voteCards = this.votes.map(vote => this.createVoteCard(vote)).join('')

    if (this.currentPage === 1) {
      this.voteList.innerHTML = voteCards
    } else {
      this.voteList.insertAdjacentHTML('beforeend', voteCards)
    }
  }

  createVoteCard(vote) {
    const statusClass = vote.status || 'draft'
    const createdDate = new Date(vote.created_at).toLocaleDateString()
    const responseCount = vote.response_count || 0
    const optionsCount = vote.options?.length || 0

    // Status badge
    const statusBadge = this.getStatusBadge(vote.status)

    return `
      <div class="vote-card md-card md-card-elevated" data-vote-id="${vote.id}" data-status="${statusClass}">
        <div class="vote-card-header">
          <div class="vote-status-info">
            ${statusBadge}
            <div class="vote-meta">
              <span class="created-date">${createdDate}</span>
              <span class="separator">•</span>
              <span class="response-count">${responseCount} responses</span>
              <span class="separator">•</span>
              <span class="options-count">${optionsCount} options</span>
            </div>
          </div>
          <div class="vote-actions">
            <button class="md-button md-button-icon" title="Edit Vote" data-action="edit-vote" data-vote-id="${vote.id}">
              <span class="material-icons">edit</span>
            </button>
            <button class="md-button md-button-icon" title="View Results" data-action="view-results" data-vote-id="${vote.id}">
              <span class="material-icons">analytics</span>
            </button>
            <button class="md-button md-button-icon" title="Delete Vote" data-action="delete-vote" data-vote-id="${vote.id}">
              <span class="material-icons">delete</span>
            </button>
          </div>
        </div>
        <div class="vote-card-content">
          <h3 class="vote-title">${this.escapeHtml(vote.title)}</h3>
          ${vote.description ? `<p class="vote-description">${this.escapeHtml(vote.description)}</p>` : ''}

          <div class="vote-options-preview">
            ${
              vote.options
                ? vote.options
                    .slice(0, 3)
                    .map(option => `<span class="option-chip">${this.escapeHtml(option.text)}</span>`)
                    .join('')
                : ''
            }
            ${vote.options && vote.options.length > 3 ? `<span class="more-options">+${vote.options.length - 3} more</span>` : ''}
          </div>
        </div>

        <div class="vote-card-actions">
          <button class="md-button md-button-text" data-action="view-vote" data-vote-id="${vote.id}">
            <span class="material-icons">visibility</span>
            View Vote
          </button>
          ${
            vote.status === 'active' || vote.status === 'closed'
              ? `<button class="md-button md-button-text" data-action="copy-link" data-vote-id="${vote.id}">
              <span class="material-icons">link</span>
              Copy Link
            </button>`
              : ''
          }
        </div>
      </div>
    `
  }

  getStatusBadge(status) {
    const statusConfig = {
      draft: { icon: 'edit', text: 'Draft', class: 'status-draft' },
      active: { icon: 'trending_up', text: 'Active', class: 'status-active' },
      closed: { icon: 'archive', text: 'Closed', class: 'status-closed' }
    }

    const config = statusConfig[status] || statusConfig.draft
    return `
      <div class="status-badge ${config.class}">
        <span class="material-icons">${config.icon}</span>
        <span>${config.text}</span>
      </div>
    `
  }

  // Edit Vote Functionality
  async openEditModal(voteId) {
    const vote = this.votes.find(v => v.id === parseInt(voteId))
    if (!vote) {
      this.showSnackbar('Vote not found')
      return
    }

    // Populate form fields
    document.getElementById('editVoteId').value = vote.id
    document.getElementById('editVoteTitle').value = vote.title || ''
    document.getElementById('editVoteDescription').value = vote.description || ''
    document.getElementById('editRequireAuth').checked = vote.require_auth || false
    document.getElementById('editUseAccessCode').checked = !!vote.access_code
    document.getElementById('editAccessCode').value = vote.access_code || ''

    // Show/hide access code field
    const accessCodeField = document.getElementById('editAccessCodeField')
    if (accessCodeField) {
      accessCodeField.style.display = vote.access_code ? 'block' : 'none'
    }

    // Handle status-based restrictions
    this.applyEditRestrictions(vote.status)

    // Populate options
    this.populateEditOptions(vote.options || [])

    // Show modal
    this.showModal('edit-vote')
  }

  applyEditRestrictions(status) {
    const isActive = status === 'active'
    const isClosed = status === 'closed'
    const isRestricted = isActive || isClosed

    // Show/hide warning
    const warning = document.getElementById('editStatusWarning')
    const warningMessage = document.getElementById('warningMessage')
    if (warning && warningMessage) {
      if (isRestricted) {
        warning.style.display = 'block'
        if (isClosed) {
          warningMessage.textContent = 'This vote is closed. You can only edit the title and description.'
        } else {
          warningMessage.textContent = 'This vote is active. You can only edit the title and description.'
        }
      } else {
        warning.style.display = 'none'
      }
    }

    // Disable restricted fields
    const restrictedElements = ['editOptionsContainer', 'editAccessSettings']

    restrictedElements.forEach(elementId => {
      const element = document.getElementById(elementId)
      if (element) {
        if (isRestricted) {
          element.style.opacity = '0.5'
          element.style.pointerEvents = 'none'
          // Disable all inputs within
          element.querySelectorAll('input, button, select, textarea').forEach(input => {
            input.disabled = true
          })
        } else {
          element.style.opacity = '1'
          element.style.pointerEvents = 'auto'
          // Enable all inputs within
          element.querySelectorAll('input, button, select, textarea').forEach(input => {
            input.disabled = false
          })
        }
      }
    })
  }

  populateEditOptions(options) {
    const container = document.getElementById('editVoteOptionsContainer')
    const counter = document.getElementById('editOptionCounter')

    if (!container || !counter) return

    container.innerHTML = ''

    options.forEach((option, index) => {
      const optionHtml = this.createEditOptionField(option, index)
      container.insertAdjacentHTML('beforeend', optionHtml)
    })

    counter.textContent = `${options.length} of 20 options`
  }

  createEditOptionField(option, index) {
    return `
      <div class="option-field" data-option-index="${index}">
        <div class="md-text-field md-text-field-outlined">
          <input type="text" class="md-text-field-input option-input"
                 value="${this.escapeHtml(option.text)}" placeholder=" "
                 maxlength="200" required>
          <label class="md-text-field-label">Option ${index + 1}</label>
        </div>
        <button type="button" class="md-button md-button-icon remove-option"
                data-action="remove-edit-option" data-index="${index}">
          <span class="material-icons">remove</span>
        </button>
      </div>
    `
  }

  async saveVoteChanges() {
    const voteId = document.getElementById('editVoteId').value
    const saveBtn = document.getElementById('saveVoteBtn')

    if (!voteId) {
      this.showSnackbar('Vote ID not found')
      return
    }

    this.setButtonLoading(saveBtn, true)

    const token = this.getAccessToken()
    if (!token) {
      this.redirectToLogin()
      return
    }

    try {
      // Collect form data
      const formData = {
        title: document.getElementById('editVoteTitle').value.trim(),
        description: document.getElementById('editVoteDescription').value.trim(),
        require_auth: document.getElementById('editRequireAuth').checked,
        access_code: document.getElementById('editUseAccessCode').checked
          ? document.getElementById('editAccessCode').value.trim()
          : null
      }

      // Collect options (only if not restricted)
      const vote = this.votes.find(v => v.id === parseInt(voteId))
      if (vote && vote.status === 'draft') {
        const optionInputs = document.querySelectorAll('#editVoteOptionsContainer .option-input')
        formData.options = Array.from(optionInputs)
          .map(input => input.value.trim())
          .filter(text => text.length > 0)
          .map(text => ({ text }))
      }

      const response = await fetch(`${this.API_BASE}/votes/${voteId}`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        const updatedVote = await response.json()
        this.updateVoteInList(updatedVote)
        this.closeModal('edit-vote')
        this.showSnackbar('Vote updated successfully!')
      } else if (response.status === 422) {
        const errorData = await response.json()
        this.showEditError(errorData.detail || 'Please check your input and try again.')
      } else if (response.status === 403) {
        this.showEditError('You do not have permission to edit this vote.')
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      console.error('Failed to save vote changes:', error)
      this.showEditError('An unexpected error occurred. Please try again.')
    } finally {
      this.setButtonLoading(saveBtn, false)
    }
  }

  updateVoteInList(updatedVote) {
    const index = this.votes.findIndex(v => v.id === updatedVote.id)
    if (index !== -1) {
      this.votes[index] = updatedVote
      this.renderVotes() // Re-render to reflect changes
    }
  }

  // Delete Vote Functionality
  async openDeleteModal(voteId) {
    const vote = this.votes.find(v => v.id === parseInt(voteId))
    if (!vote) {
      this.showSnackbar('Vote not found')
      return
    }

    document.getElementById('deleteVoteId').value = vote.id
    document.getElementById('deleteVoteTitle').textContent = vote.title

    // Update warning text based on response count
    const responseCount = vote.response_count || 0
    const warningText = document.getElementById('deleteWarningText')
    if (warningText) {
      if (responseCount > 0) {
        warningText.textContent = `This vote has ${responseCount} responses. The vote will be deleted but responses will be preserved for your records.`
      } else {
        warningText.textContent = 'This action cannot be undone. The vote will be permanently deleted.'
      }
    }

    this.showModal('delete-vote')
  }

  async confirmDeleteVote() {
    const voteId = document.getElementById('deleteVoteId').value
    const deleteBtn = document.getElementById('confirmDeleteBtn')

    if (!voteId) {
      this.showSnackbar('Vote ID not found')
      return
    }

    this.setButtonLoading(deleteBtn, true)

    const token = this.getAccessToken()
    if (!token) {
      this.redirectToLogin()
      return
    }

    try {
      const response = await fetch(`${this.API_BASE}/votes/${voteId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (response.ok || response.status === 204) {
        // Remove from local array
        this.votes = this.votes.filter(v => v.id !== parseInt(voteId))
        this.renderVotes()
        this.closeModal('delete-vote')
        this.showSnackbar('Vote deleted successfully')
      } else if (response.status === 403) {
        this.showSnackbar('You do not have permission to delete this vote.')
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      console.error('Failed to delete vote:', error)
      this.showSnackbar('Failed to delete vote. Please try again.')
    } finally {
      this.setButtonLoading(deleteBtn, false)
    }
  }

  // Results Visualization
  async openResultsModal(voteId) {
    const vote = this.votes.find(v => v.id === parseInt(voteId))
    if (!vote) {
      this.showSnackbar('Vote not found')
      return
    }

    document.getElementById('resultsVoteId').value = vote.id
    document.getElementById('resultsVoteTitle').textContent = vote.title

    this.showModal('results')
    await this.loadAndDisplayResults(voteId)
    this.startResultsPolling(voteId)
  }

  async loadAndDisplayResults(voteId) {
    const token = this.getAccessToken()
    if (!token) {
      this.redirectToLogin()
      return
    }

    try {
      const response = await fetch(`${this.API_BASE}/votes/${voteId}/results`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (response.ok) {
        const results = await response.json()
        this.displayResults(results)
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      console.error('Failed to load results:', error)
      this.showSnackbar('Failed to load results. Please try again.')
    }
  }

  displayResults(results) {
    // Update statistics
    document.getElementById('totalVoteResponses').textContent = results.total_responses || 0
    document.getElementById('averageRating').textContent = (results.average_rating || 0).toFixed(1)
    document.getElementById('participationRate').textContent = `${results.participation_rate || 0}%`

    // Update charts
    this.renderResultsCharts(results)

    // Update detailed table
    this.renderResultsTable(results)
  }

  renderResultsCharts(results) {
    const options = results.options || []

    // Prepare data
    const labels = options.map(opt => opt.text)
    const averages = options.map(opt => opt.average_rating || 0)
    const totals = options.map(opt => opt.vote_count || 0)

    // Bar Chart - Average Ratings
    this.renderBarChart(labels, averages)

    // Pie Chart - Vote Distribution
    this.renderPieChart(labels, totals)
  }

  renderBarChart(labels, data) {
    const canvas = document.getElementById('resultsBarChart')
    if (!canvas) return

    const ctx = canvas.getContext('2d')

    // Destroy existing chart
    if (this.barChart) {
      this.barChart.destroy()
    }

    this.barChart = new window.Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Average Rating',
            data,
            backgroundColor: 'rgba(103, 80, 164, 0.8)',
            borderColor: 'rgba(103, 80, 164, 1)',
            borderWidth: 1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            max: 2,
            min: -2,
            ticks: {
              stepSize: 0.5
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                return `Rating: ${context.parsed.y.toFixed(2)}`
              }
            }
          }
        }
      }
    })
  }

  renderPieChart(labels, data) {
    const canvas = document.getElementById('resultsPieChart')
    if (!canvas) return

    const ctx = canvas.getContext('2d')

    // Destroy existing chart
    if (this.pieChart) {
      this.pieChart.destroy()
    }

    const colors = [
      'rgba(103, 80, 164, 0.8)',
      'rgba(33, 150, 243, 0.8)',
      'rgba(76, 175, 80, 0.8)',
      'rgba(255, 193, 7, 0.8)',
      'rgba(255, 87, 34, 0.8)',
      'rgba(233, 30, 99, 0.8)'
    ]

    this.pieChart = new window.Chart(ctx, {
      type: 'pie',
      data: {
        labels,
        datasets: [
          {
            data,
            backgroundColor: colors.slice(0, labels.length),
            borderColor: colors.slice(0, labels.length).map(color => color.replace('0.8', '1')),
            borderWidth: 1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom'
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0)
                const percentage = ((context.parsed / total) * 100).toFixed(1)
                return `${context.label}: ${context.parsed} votes (${percentage}%)`
              }
            }
          }
        }
      }
    })
  }

  renderResultsTable(results) {
    const tbody = document.getElementById('resultsTableBody')
    if (!tbody) return

    const options = results.options || []
    const totalResponses = results.total_responses || 1

    tbody.innerHTML = options
      .map(option => {
        const percentage = totalResponses > 0 ? (((option.vote_count || 0) / totalResponses) * 100).toFixed(1) : 0

        return `
        <tr>
          <td>${this.escapeHtml(option.text)}</td>
          <td>${(option.average_rating || 0).toFixed(2)}</td>
          <td>${option.vote_count || 0}</td>
          <td>
            <div class="distribution-bar">
              <div class="distribution-fill" style="width: ${percentage}%"></div>
              <span class="distribution-text">${percentage}%</span>
            </div>
          </td>
        </tr>
      `
      })
      .join('')
  }

  startResultsPolling(voteId) {
    // Clear existing interval
    if (this.resultsPollingInterval) {
      clearInterval(this.resultsPollingInterval)
    }

    // Poll every 5 seconds
    this.resultsPollingInterval = setInterval(() => {
      this.loadAndDisplayResults(voteId)
    }, 5000)
  }

  stopResultsPolling() {
    if (this.resultsPollingInterval) {
      clearInterval(this.resultsPollingInterval)
      this.resultsPollingInterval = null
    }
  }

  // Export Functionality
  async exportVoteData(voteId, format) {
    const token = this.getAccessToken()
    if (!token) {
      this.redirectToLogin()
      return
    }

    try {
      const response = await fetch(`${this.API_BASE}/votes/${voteId}/export?format=${format}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `vote-${voteId}-${Date.now()}.${format}`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)

        this.showSnackbar(`Export downloaded successfully`)
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      console.error('Failed to export data:', error)
      this.showSnackbar('Failed to export data. Please try again.')
    }
  }

  // Modal Management
  showModal(modalType) {
    const modalMap = {
      'edit-vote': 'editVoteModalScrim',
      'delete-vote': 'deleteVoteModalScrim',
      results: 'resultsModalScrim'
    }

    const modalId = modalMap[modalType]
    const modal = document.getElementById(modalId)

    if (modal) {
      modal.classList.add('md-dialog-scrim-visible')
      modal.setAttribute('aria-hidden', 'false')

      // Add click outside to close
      modal.addEventListener(
        'click',
        e => {
          if (e.target === modal) {
            this.closeModal(modalType)
          }
        },
        { once: true }
      )
    }
  }

  closeModal(modalType) {
    const modalMap = {
      'edit-vote': 'editVoteModalScrim',
      'delete-vote': 'deleteVoteModalScrim',
      results: 'resultsModalScrim'
    }

    const modalId = modalMap[modalType]
    const modal = document.getElementById(modalId)

    if (modal) {
      modal.classList.remove('md-dialog-scrim-visible')
      modal.setAttribute('aria-hidden', 'true')
    }

    // Clear form errors
    this.clearEditError()

    // Stop polling if closing results modal
    if (modalType === 'results') {
      this.stopResultsPolling()

      // Cleanup charts
      if (this.barChart) {
        this.barChart.destroy()
        this.barChart = null
      }
      if (this.pieChart) {
        this.pieChart.destroy()
        this.pieChart = null
      }
    }
  }

  // Utility Methods
  async loadMoreVotes() {
    if (!this.hasMoreItems || this.isLoading) return

    this.currentPage++
    await this.loadVotes(true)
  }

  showLoadingState(showSkeleton = true) {
    if (showSkeleton && this.loadingState) {
      this.loadingState.style.display = 'block'
    }
  }

  hideLoadingState() {
    if (this.loadingState) {
      this.loadingState.style.display = 'none'
    }
  }

  showEmptyState() {
    this.hideLoadingState()
    if (this.emptyState) {
      this.emptyState.style.display = 'flex'
    }
    if (this.loadMoreContainer) {
      this.loadMoreContainer.style.display = 'none'
    }
  }

  hideEmptyState() {
    if (this.emptyState) {
      this.emptyState.style.display = 'none'
    }
  }

  clearVoteList() {
    if (this.voteList) {
      this.voteList.innerHTML = ''
    }
  }

  updateLoadMoreButton() {
    if (this.loadMoreContainer) {
      this.loadMoreContainer.style.display = this.hasMoreItems ? 'flex' : 'none'
    }
  }

  setButtonLoading(button, isLoading) {
    if (!button) return

    const text = button.querySelector('.btn-text')
    const loading = button.querySelector('.btn-loading')

    if (text && loading) {
      if (isLoading) {
        text.style.display = 'none'
        loading.style.display = 'inline-block'
        loading.style.animation = 'spin 1s linear infinite'
        button.disabled = true
      } else {
        text.style.display = 'inline-block'
        loading.style.display = 'none'
        button.disabled = false
      }
    }
  }

  showEditError(message) {
    const errorElement = document.getElementById('editVoteError')
    const errorMessage = document.getElementById('editVoteErrorMessage')

    if (errorElement && errorMessage) {
      errorMessage.textContent = message
      errorElement.style.display = 'flex'
    }
  }

  clearEditError() {
    const errorElement = document.getElementById('editVoteError')
    if (errorElement) {
      errorElement.style.display = 'none'
    }
  }

  // Borrowed utility methods from DashboardManager
  getAccessToken() {
    return sessionStorage.getItem('access_token')
  }

  clearTokens() {
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('refresh_token')
  }

  redirectToLogin() {
    window.location.href = '/'
  }

  showSnackbar(message) {
    const snackbar = document.getElementById('snackbar')
    const snackbarMessage = document.getElementById('snackbar-message')

    if (snackbar && snackbarMessage) {
      snackbarMessage.textContent = message
      snackbar.classList.add('md-snackbar-visible')

      setTimeout(() => {
        snackbar.classList.remove('md-snackbar-visible')
      }, 4000)
    }
  }

  escapeHtml(text) {
    if (!text) return ''
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    }
    return text.replace(/[&<>"']/g, function (m) {
      return map[m]
    })
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  VoteManagementManager.init()
})
