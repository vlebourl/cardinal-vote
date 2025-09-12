// Moderation dashboard data management
let moderationData = {
    stats: null,
    pendingFlags: [],
    flaggedVotes: [],
    moderationLog: [],
    refreshInterval: null,
    currentTab: 'pending-flags',
    selectedVotes: new Set()
};

// Initialize moderation dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeModerationDashboard();
    startAutoRefresh();
    setupFormHandlers();
});

async function initializeModerationDashboard() {
    try {
        showLoading();
        await loadModerationDashboard();
    } catch (error) {
        console.error('Moderation dashboard initialization error:', error);
        showMessage('Error loading moderation dashboard', 'error');
    } finally {
        hideLoading();
    }
}

async function loadModerationDashboard() {
    try {
        const response = await fetch('/api/admin/moderation/dashboard');

        if (!response.ok) {
            if (handleAuthError(response)) return;
            throw new Error('Failed to load moderation dashboard');
        }

        const data = await response.json();
        moderationData.stats = data.stats;
        moderationData.pendingFlags = data.pending_flags;
        moderationData.flaggedVotes = data.flagged_votes;

        updateModerationStats(data.stats);
        updatePendingFlagsList(data.pending_flags);
        updateFlaggedVotesList(data.flagged_votes);

    } catch (error) {
        console.error('Error loading moderation dashboard:', error);
        showMessage('Error loading moderation dashboard', 'error');
    }
}

function updateModerationStats(stats) {
    document.getElementById('pendingFlags').textContent = stats.pending_flags || 0;
    document.getElementById('moderatedVotes').textContent = stats.total_moderated_votes || 0;
    document.getElementById('hiddenVotes').textContent = stats.moderated_votes_by_status?.hidden || 0;

    // Calculate weekly actions
    const weeklyActions = Object.values(stats.recent_actions_by_type || {}).reduce((a, b) => a + b, 0);
    document.getElementById('weeklyActions').textContent = weeklyActions;

    // Update status indicators
    const flagsStatus = stats.pending_flags > 0 ? 'Requires attention' : 'All clear';
    document.getElementById('flagsStatus').textContent = flagsStatus;

    const disabledCount = stats.moderated_votes_by_status?.disabled || 0;
    document.getElementById('disabledCount').textContent = `${disabledCount} disabled`;
}

function updatePendingFlagsList(flags) {
    const container = document.getElementById('pendingFlagsList');

    if (flags && flags.length > 0) {
        const flagsHTML = flags.map(flag => `
            <div class="flag-item" data-flag-id="${flag.id}">
                <div class="flag-header">
                    <div class="flag-type ${flag.flag_type}">
                        <i class="fas ${getFlagTypeIcon(flag.flag_type)}"></i>
                        ${formatFlagType(flag.flag_type)}
                    </div>
                    <div class="flag-actions">
                        <button class="btn-sm btn-primary" data-action="review-flag" data-flag-id="${flag.id}">
                            <i class="fas fa-gavel"></i> Review
                        </button>
                        <button class="btn-sm btn-secondary" data-action="view-vote-details" data-vote-id="${flag.vote_id}">
                            <i class="fas fa-eye"></i> View Vote
                        </button>
                    </div>
                </div>
                <div class="flag-content">
                    <h4 class="vote-title">${flag.vote_title}</h4>
                    <p class="flag-reason">${flag.reason}</p>
                    <div class="flag-meta">
                        <span class="flagger">By: ${flag.flagger_email}</span>
                        <span class="flag-date">${formatDateTime(flag.created_at)}</span>
                        <span class="vote-creator">Creator: ${flag.creator_email}</span>
                    </div>
                </div>
            </div>
        `).join('');
        safeSetHTML(container, flagsHTML);
    } else {
        safeSetHTML(container, `
            <div class="empty-state">
                <i class="fas fa-check-circle"></i>
                <h3>No Pending Flags</h3>
                <p>All flags have been reviewed. Great job!</p>
            </div>
        `);
    }
}

function updateFlaggedVotesList(votes) {
    const container = document.getElementById('flaggedVotesList');

    if (votes && votes.length > 0) {
        const votesHTML = votes.map(vote => `
            <div class="vote-item" data-vote-id="${vote.id}">
                <div class="vote-header">
                    <div class="vote-checkbox">
                        <input type="checkbox" id="vote-${vote.id}" data-action="toggle-vote-selection" data-vote-id="${vote.id}">
                    </div>
                    <div class="vote-info">
                        <h4 class="vote-title">${vote.title}</h4>
                        <div class="vote-meta">
                            <span class="vote-status status-${vote.status}">${vote.status}</span>
                            <span class="vote-creator">By: ${vote.creator_email}</span>
                            <span class="vote-date">${formatDateTime(vote.created_at)}</span>
                        </div>
                    </div>
                    <div class="vote-actions">
                        <button class="btn-sm btn-primary" data-action="take-vote-action" data-vote-id="${vote.id}">
                            <i class="fas fa-gavel"></i> Take Action
                        </button>
                        <button class="btn-sm btn-secondary" data-action="view-vote-moderation" data-vote-id="${vote.id}">
                            <i class="fas fa-eye"></i> View Details
                        </button>
                    </div>
                </div>
                <div class="vote-flags">
                    ${Object.entries(vote.flag_counts || {}).map(([status, count]) =>
                        `<span class="flag-count flag-${status}">${count} ${status}</span>`
                    ).join(' ')}
                    <span class="total-flags">${vote.total_flags} total flags</span>
                </div>
            </div>
        `).join('');
        safeSetHTML(container, votesHTML);
    } else {
        safeSetHTML(container, `
            <div class="empty-state">
                <i class="fas fa-shield-check"></i>
                <h3>No Flagged Votes</h3>
                <p>No votes have been flagged for review.</p>
            </div>
        `);
    }
}

// Tab switching
function switchTab(tabName) {
    // Update active tab button
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    // Update active tab content
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById(tabName + '-tab').classList.add('active');

    moderationData.currentTab = tabName;

    // Load tab-specific data if needed
    if (tabName === 'moderation-log' && moderationData.moderationLog.length === 0) {
        loadModerationLog();
    }
}

// Flag review functions
async function reviewFlag(flagId) {
    try {
        // Get flag details
        const flag = moderationData.pendingFlags.find(f => f.id === flagId);
        if (!flag) {
            showMessage('Flag not found', 'error');
            return;
        }

        // Show modal with flag details
        safeSetHTML(document.getElementById('flagDetails'), `
            <div class="flag-review-details">
                <h4>Vote: ${flag.vote_title}</h4>
                <p><strong>Flag Type:</strong> ${formatFlagType(flag.flag_type)}</p>
                <p><strong>Flagged By:</strong> ${flag.flagger_email}</p>
                <p><strong>Date:</strong> ${formatDateTime(flag.created_at)}</p>
                <div class="flag-reason-box">
                    <strong>Reason:</strong>
                    <p>${flag.reason}</p>
                </div>
                <p><strong>Vote Creator:</strong> ${flag.creator_email}</p>
            </div>
        `);

        document.getElementById('flagReviewModal').style.display = 'block';
        document.getElementById('flagReviewModal').setAttribute('data-flag-id', flagId);

    } catch (error) {
        console.error('Error reviewing flag:', error);
        showMessage('Error loading flag details', 'error');
    }
}

async function submitFlagReview() {
    try {
        const modal = document.getElementById('flagReviewModal');
        const flagId = modal.getAttribute('data-flag-id');
        const decision = document.getElementById('reviewDecision').value;
        const notes = document.getElementById('reviewNotes').value;

        if (!decision || !notes.trim()) {
            showMessage('Please select a decision and provide review notes', 'warning');
            return;
        }

        const response = await fetch(`/api/admin/moderation/flags/${flagId}/review`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                status: decision,
                review_notes: notes.trim()
            })
        });

        if (!response.ok) {
            if (handleAuthError(response)) return;
            const error = await response.json();
            throw new Error(error.detail || 'Failed to submit review');
        }

        const result = await response.json();
        showMessage(result.message || 'Flag reviewed successfully', 'success');

        closeFlagReviewModal();
        await refreshPendingFlags();

    } catch (error) {
        console.error('Error submitting flag review:', error);
        showMessage(error.message || 'Error submitting flag review', 'error');
    }
}

function closeFlagReviewModal() {
    document.getElementById('flagReviewModal').style.display = 'none';
    document.getElementById('reviewDecision').value = '';
    document.getElementById('reviewNotes').value = '';
}

// Vote action functions
async function takeVoteAction(voteId) {
    try {
        // Get vote details
        const vote = moderationData.flaggedVotes.find(v => v.id === voteId);
        if (!vote) {
            showMessage('Vote not found', 'error');
            return;
        }

        // Show modal with vote details
        safeSetHTML(document.getElementById('voteDetails'), `
            <div class="vote-action-details">
                <h4>${vote.title}</h4>
                <p><strong>Status:</strong> <span class="status-${vote.status}">${vote.status}</span></p>
                <p><strong>Creator:</strong> ${vote.creator_email}</p>
                <p><strong>Created:</strong> ${formatDateTime(vote.created_at)}</p>
                <p><strong>Responses:</strong> ${vote.total_responses}</p>
                <div class="flag-summary">
                    <strong>Flag Summary:</strong>
                    ${Object.entries(vote.flag_counts || {}).map(([status, count]) =>
                        `<span class="flag-count flag-${status}">${count} ${status}</span>`
                    ).join(' ')}
                </div>
            </div>
        `);

        document.getElementById('voteActionModal').style.display = 'block';
        document.getElementById('voteActionModal').setAttribute('data-vote-id', voteId);

    } catch (error) {
        console.error('Error preparing vote action:', error);
        showMessage('Error loading vote details', 'error');
    }
}

async function submitModerationAction() {
    try {
        const modal = document.getElementById('voteActionModal');
        const voteId = modal.getAttribute('data-vote-id');
        const actionType = document.getElementById('actionType').value;
        const reason = document.getElementById('actionReason').value;

        if (!actionType || !reason.trim()) {
            showMessage('Please select an action type and provide a reason', 'warning');
            return;
        }

        const response = await fetch(`/api/admin/moderation/votes/${voteId}/action`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                action_type: actionType,
                reason: reason.trim()
            })
        });

        if (!response.ok) {
            if (handleAuthError(response)) return;
            const error = await response.json();
            throw new Error(error.detail || 'Failed to take moderation action');
        }

        const result = await response.json();
        showMessage(result.message || 'Moderation action completed successfully', 'success');

        closeVoteActionModal();
        await loadModerationDashboard();

    } catch (error) {
        console.error('Error taking moderation action:', error);
        showMessage(error.message || 'Error taking moderation action', 'error');
    }
}

function closeVoteActionModal() {
    document.getElementById('voteActionModal').style.display = 'none';
    document.getElementById('actionType').value = '';
    document.getElementById('actionReason').value = '';
}

// Bulk actions
function toggleVoteSelection(voteId) {
    const checkbox = document.getElementById(`vote-${voteId}`);
    if (checkbox.checked) {
        moderationData.selectedVotes.add(voteId);
    } else {
        moderationData.selectedVotes.delete(voteId);
    }
    updateBulkSelectionInput();
}

function updateBulkSelectionInput() {
    const selectedIds = Array.from(moderationData.selectedVotes).join(', ');
    document.getElementById('bulkVoteIds').value = selectedIds;
}

async function executeBulkAction() {
    try {
        const voteIds = document.getElementById('bulkVoteIds').value.split(',').map(id => id.trim()).filter(id => id);
        const actionType = document.getElementById('bulkActionType').value;
        const reason = document.getElementById('bulkActionReason').value;

        if (voteIds.length === 0) {
            showMessage('Please provide vote IDs', 'warning');
            return;
        }

        if (!actionType) {
            showMessage('Please select an action type', 'warning');
            return;
        }

        if (!reason.trim()) {
            showMessage('Please provide a reason for the bulk action', 'warning');
            return;
        }

        const confirmMessage = `Are you sure you want to ${actionType.replace('_', ' ')} ${voteIds.length} vote(s)?`;
        if (!confirm(confirmMessage)) {
            return;
        }

        document.getElementById('bulkActionBtn').disabled = true;
        safeSetHTML(document.getElementById('bulkActionBtn'), '<i class="fas fa-spinner fa-spin"></i> Processing...');

        const response = await fetch('/api/admin/moderation/bulk-action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                vote_ids: voteIds,
                action_type: actionType,
                reason: reason.trim()
            })
        });

        if (!response.ok) {
            if (handleAuthError(response)) return;
            const error = await response.json();
            throw new Error(error.detail || 'Failed to execute bulk action');
        }

        const result = await response.json();
        showMessage(`Bulk action completed: ${result.success_count} successful, ${result.error_count} failed`, 'success');

        clearBulkForm();
        await loadModerationDashboard();

    } catch (error) {
        console.error('Error executing bulk action:', error);
        showMessage(error.message || 'Error executing bulk action', 'error');
    } finally {
        document.getElementById('bulkActionBtn').disabled = false;
        safeSetHTML(document.getElementById('bulkActionBtn'), '<i class="fas fa-bolt"></i> Execute Bulk Action');
    }
}

function clearBulkForm() {
    document.getElementById('bulkVoteIds').value = '';
    document.getElementById('bulkActionType').value = '';
    document.getElementById('bulkActionReason').value = '';
    moderationData.selectedVotes.clear();

    // Uncheck all vote checkboxes
    document.querySelectorAll('input[type="checkbox"][id^="vote-"]').forEach(checkbox => {
        checkbox.checked = false;
    });

    updateReasonCharCount();
}

// Utility functions
function getFlagTypeIcon(flagType) {
    const icons = {
        'inappropriate_content': 'fa-exclamation-triangle',
        'spam': 'fa-ban',
        'harassment': 'fa-user-times',
        'copyright': 'fa-copyright',
        'other': 'fa-question-circle'
    };
    return icons[flagType] || 'fa-flag';
}

function formatFlagType(flagType) {
    return flagType.split('_').map(word =>
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

function formatDateTime(dateString) {
    if (!dateString) return 'Unknown';

    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;

    // Less than 1 hour ago
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes} min${minutes !== 1 ? 's' : ''} ago`;
    }

    // Less than 24 hours ago
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    }

    // More than 24 hours ago
    return date.toLocaleDateString();
}

// Form handlers
function setupFormHandlers() {
    // Character counter for bulk action reason
    const reasonTextarea = document.getElementById('bulkActionReason');
    if (reasonTextarea) {
        reasonTextarea.addEventListener('input', updateReasonCharCount);
    }
}

function updateReasonCharCount() {
    const textarea = document.getElementById('bulkActionReason');
    const counter = document.getElementById('reasonCharCount');
    if (textarea && counter) {
        counter.textContent = textarea.value.length;
    }
}

// Auto-refresh functionality
function startAutoRefresh() {
    moderationData.refreshInterval = setInterval(async () => {
        try {
            await loadModerationDashboard();
        } catch (error) {
            console.error('Auto-refresh error:', error);
        }
    }, 60000); // 1 minute
}

async function refreshPendingFlags() {
    await loadModerationDashboard();
}

// Stop auto-refresh when page is hidden
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        if (moderationData.refreshInterval) {
            clearInterval(moderationData.refreshInterval);
        }
    } else {
        startAutoRefresh();
    }
});

// Cleanup when leaving page
window.addEventListener('beforeunload', function() {
    if (moderationData.refreshInterval) {
        clearInterval(moderationData.refreshInterval);
    }
});

// Register event handlers for moderation-specific actions
document.addEventListener('DOMContentLoaded', function() {
    // Register moderation action handlers with the event system
    window.moderationHandlers = {
        'switch-tab': function(element) {
            const tabName = element.dataset.tab;
            if (tabName) {
                switchTab(tabName);
            }
        },
        'review-flag': function(element) {
            const flagId = element.dataset.flagId;
            if (flagId) {
                reviewFlag(flagId);
            }
        },
        'view-vote-details': function(element) {
            const voteId = element.dataset.voteId;
            if (voteId) {
                viewVoteDetails(voteId);
            }
        },
        'take-vote-action': function(element) {
            const voteId = element.dataset.voteId;
            if (voteId) {
                takeVoteAction(voteId);
            }
        },
        'view-vote-moderation': function(element) {
            const voteId = element.dataset.voteId;
            if (voteId) {
                viewVoteModeration(voteId);
            }
        },
        'toggle-vote-selection': function(element) {
            const voteId = element.dataset.voteId;
            if (voteId) {
                toggleVoteSelection(voteId);
            }
        },
        'execute-bulk-action': function(element) {
            executeBulkAction();
        },
        'clear-bulk-form': function(element) {
            clearBulkForm();
        },
        'refresh-pending-flags': function(element) {
            refreshPendingFlags();
        },
        'filter-flagged-votes': function(element) {
            filterFlaggedVotes(element.value);
        },
        'submit-flag-review': function(element) {
            submitFlagReview();
        },
        'close-flag-review-modal': function(element) {
            closeFlagReviewModal();
        },
        'submit-moderation-action': function(element) {
            submitModerationAction();
        },
        'close-vote-action-modal': function(element) {
            closeVoteActionModal();
        }
    };
});

// Placeholder functions that would need implementation
function viewVoteDetails(voteId) {
    console.log('View vote details:', voteId);
    // Implementation needed
}

function viewVoteModeration(voteId) {
    console.log('View vote moderation:', voteId);
    // Implementation needed
}

function filterFlaggedVotes(status) {
    console.log('Filter flagged votes:', status);
    // Implementation needed
}
