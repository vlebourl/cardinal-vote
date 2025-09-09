/**
 * Dashboard JavaScript functionality
 * Handles navigation, vote management, and user interactions
 */

class DashboardManager {
    constructor() {
        this.currentUser = null;
        this.currentSection = 'dashboard';
        this.votes = [];
        this.currentPage = 1;
        this.votesPerPage = 10;
        this.totalVotes = 0;

        // DOM elements
        this.navItems = document.querySelectorAll('.nav-item');
        this.sections = document.querySelectorAll('.dashboard-section');
        this.userMenu = document.querySelector('.user-menu');
        this.userDropdown = document.querySelector('.user-dropdown');
        this.logoutBtn = document.querySelector('.logout-btn');
        this.liveRegion = document.getElementById('live-region');

        // Dashboard elements
        this.userInitials = document.getElementById('user-initials');
        this.userName = document.getElementById('user-name');
        this.totalVotesEl = document.getElementById('total-votes');
        this.activeVotesEl = document.getElementById('active-votes');
        this.totalParticipantsEl = document.getElementById('total-participants');
        this.totalResponsesEl = document.getElementById('total-responses');

        // Votes section elements
        this.statusFilter = document.getElementById('status-filter');
        this.searchInput = document.getElementById('search-votes');
        this.votesList = document.getElementById('votes-list');
        this.emptyState = document.getElementById('empty-votes');
        this.pagination = document.getElementById('votes-pagination');
        this.prevPageBtn = document.getElementById('prev-page');
        this.nextPageBtn = document.getElementById('next-page');
        this.paginationInfo = document.getElementById('pagination-info');

        // Modals
        this.voteDetailsModal = document.getElementById('vote-details-modal');
        this.deleteVoteModal = document.getElementById('delete-vote-modal');
        this.confirmDeleteBtn = document.getElementById('confirm-delete-btn');

        this.selectedVoteId = null;

        this.initializeEventListeners();
        this.loadUserData();
        this.loadDashboardData();
    }

    initializeEventListeners() {
        // Navigation
        this.navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.dataset.section;
                this.navigateToSection(section);
            });
        });

        // User menu
        this.userMenu.addEventListener('click', () => this.toggleUserMenu());
        this.userMenu.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.toggleUserMenu();
            }
        });

        // Close user menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.userMenu.contains(e.target)) {
                this.closeUserMenu();
            }
        });

        // Logout
        this.logoutBtn.addEventListener('click', () => this.handleLogout());

        // Filters and search
        this.statusFilter.addEventListener('change', () => this.filterVotes());
        this.searchInput.addEventListener('input', this.debounce(() => this.filterVotes(), 300));

        // Pagination
        this.prevPageBtn.addEventListener('click', () => this.goToPreviousPage());
        this.nextPageBtn.addEventListener('click', () => this.goToNextPage());

        // Create vote buttons
        const createVoteButtons = document.querySelectorAll('[data-action="create-vote"]');
        createVoteButtons.forEach(btn => {
            btn.addEventListener('click', () => this.navigateToSection('create'));
        });

        // Modal close handlers
        const modalCloses = document.querySelectorAll('.modal-close');
        modalCloses.forEach(close => {
            close.addEventListener('click', () => this.closeAllModals());
        });

        // Close modals on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });

        // Close modals on backdrop click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeAllModals();
                }
            });
        });

        // Delete confirmation
        this.confirmDeleteBtn.addEventListener('click', () => this.confirmDeleteVote());

        // Cancel delete
        const cancelButtons = document.querySelectorAll('[data-action="cancel"]');
        cancelButtons.forEach(btn => {
            btn.addEventListener('click', () => this.closeAllModals());
        });
    }

    loadUserData() {
        try {
            const userDataScript = document.getElementById('user-data');
            if (userDataScript && userDataScript.textContent) {
                this.currentUser = JSON.parse(userDataScript.textContent);
                this.updateUserUI();
            } else {
                // Try to get user from token
                this.getCurrentUser();
            }
        } catch (error) {
            console.error('Failed to load user data:', error);
            this.handleAuthError();
        }
    }

    async getCurrentUser() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                this.handleAuthError();
                return;
            }

            const response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.currentUser = data.user;
                this.updateUserUI();
            } else {
                this.handleAuthError();
            }
        } catch (error) {
            console.error('Failed to get current user:', error);
            this.handleAuthError();
        }
    }

    updateUserUI() {
        if (!this.currentUser) return;

        const initials = `${this.currentUser.first_name?.[0] || ''}${this.currentUser.last_name?.[0] || ''}`.toUpperCase();
        const fullName = `${this.currentUser.first_name || ''} ${this.currentUser.last_name || ''}`.trim();

        this.userInitials.textContent = initials || 'U';
        this.userName.textContent = fullName || this.currentUser.email || 'Utilisateur';
    }

    async loadDashboardData() {
        try {
            await Promise.all([
                this.loadStats(),
                this.loadRecentActivity(),
                this.loadPopularVotes()
            ]);
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    }

    async loadStats() {
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch('/api/votes/stats', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateStats(data);
            }
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    updateStats(stats) {
        this.totalVotesEl.textContent = stats.total_votes || 0;
        this.activeVotesEl.textContent = stats.active_votes || 0;
        this.totalParticipantsEl.textContent = stats.total_participants || 0;
        this.totalResponsesEl.textContent = stats.total_responses || 0;
    }

    async loadRecentActivity() {
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch('/api/votes/activity', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateRecentActivity(data.activities || []);
            }
        } catch (error) {
            console.error('Failed to load recent activity:', error);
            this.updateRecentActivity([]);
        }
    }

    updateRecentActivity(activities) {
        const activityList = document.getElementById('recent-activity');

        if (!activities.length) {
            activityList.innerHTML = `
                <div class="activity-item">
                    <div class="activity-icon">📝</div>
                    <div class="activity-content">
                        <div class="activity-text">Aucune activité récente</div>
                        <div class="activity-time">Créez votre premier vote pour commencer</div>
                    </div>
                </div>
            `;
            return;
        }

        activityList.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon">${this.getActivityIcon(activity.type)}</div>
                <div class="activity-content">
                    <div class="activity-text">${activity.description}</div>
                    <div class="activity-time">${this.formatTimeAgo(activity.created_at)}</div>
                </div>
            </div>
        `).join('');
    }

    async loadPopularVotes() {
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch('/api/votes/popular', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updatePopularVotes(data.votes || []);
            }
        } catch (error) {
            console.error('Failed to load popular votes:', error);
            this.updatePopularVotes([]);
        }
    }

    updatePopularVotes(votes) {
        const popularVotes = document.getElementById('popular-votes');

        if (!votes.length) {
            popularVotes.innerHTML = `
                <div class="vote-item">
                    <div class="vote-title">Aucun vote populaire</div>
                    <div class="vote-stats">Créez des votes pour voir les statistiques</div>
                </div>
            `;
            return;
        }

        popularVotes.innerHTML = votes.map(vote => `
            <div class="vote-item" data-vote-id="${vote.id}">
                <div class="vote-title">${vote.title}</div>
                <div class="vote-stats">${vote.participant_count || 0} participants</div>
            </div>
        `).join('');

        // Add click handlers
        popularVotes.querySelectorAll('.vote-item').forEach(item => {
            item.addEventListener('click', () => {
                const voteId = item.dataset.voteId;
                this.showVoteDetails(voteId);
            });
        });
    }

    navigateToSection(sectionName) {
        // Update nav items
        this.navItems.forEach(item => {
            item.classList.remove('active');
            if (item.dataset.section === sectionName) {
                item.classList.add('active');
            }
        });

        // Update sections
        this.sections.forEach(section => {
            section.classList.remove('active');
            if (section.id === `${sectionName}-section`) {
                section.classList.add('active');
            }
        });

        this.currentSection = sectionName;

        // Load section-specific data
        if (sectionName === 'votes') {
            this.loadVotes();
        }

        // Announce navigation to screen readers
        this.liveRegion.textContent = `Navigation vers ${this.getSectionName(sectionName)}`;
    }

    getSectionName(sectionName) {
        const names = {
            dashboard: 'Tableau de bord',
            votes: 'Mes votes',
            create: 'Créer un vote'
        };
        return names[sectionName] || sectionName;
    }

    async loadVotes() {
        try {
            this.showVotesLoading();

            const token = localStorage.getItem('access_token');
            const params = new URLSearchParams({
                page: this.currentPage,
                limit: this.votesPerPage,
                status: this.statusFilter.value !== 'all' ? this.statusFilter.value : '',
                search: this.searchInput.value
            });

            const response = await fetch(`/api/votes/my?${params}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.votes = data.votes || [];
                this.totalVotes = data.total || 0;
                this.updateVotesList();
                this.updatePagination();
            } else {
                throw new Error('Failed to load votes');
            }
        } catch (error) {
            console.error('Failed to load votes:', error);
            this.showVotesError();
        }
    }

    showVotesLoading() {
        this.votesList.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>Chargement de vos votes...</p>
            </div>
        `;
        this.emptyState.hidden = true;
        this.pagination.hidden = true;
    }

    showVotesError() {
        this.votesList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <h3>Erreur de chargement</h3>
                <p>Impossible de charger vos votes. Veuillez réessayer.</p>
                <button class="btn btn-primary" onclick="location.reload()">Actualiser</button>
            </div>
        `;
        this.emptyState.hidden = true;
        this.pagination.hidden = true;
    }

    updateVotesList() {
        if (!this.votes.length) {
            this.votesList.innerHTML = '';
            this.emptyState.hidden = false;
            this.pagination.hidden = true;
            return;
        }

        this.emptyState.hidden = true;

        this.votesList.innerHTML = this.votes.map(vote => `
            <div class="vote-card" data-vote-id="${vote.id}">
                <div class="vote-info">
                    <div class="vote-card-title">${vote.title}</div>
                    <div class="vote-card-meta">
                        <span class="vote-meta-item">
                            <span class="meta-icon">📅</span>
                            Créé le ${this.formatDate(vote.created_at)}
                        </span>
                        <span class="vote-meta-item">
                            <span class="meta-icon">👥</span>
                            ${vote.participant_count || 0} participants
                        </span>
                        <span class="vote-meta-item">
                            <span class="meta-icon">💬</span>
                            ${vote.response_count || 0} réponses
                        </span>
                    </div>
                    <span class="vote-status ${vote.status}">${this.getStatusText(vote.status)}</span>
                </div>
                <div class="vote-actions">
                    <button class="action-btn" onclick="dashboard.showVoteDetails('${vote.id}')" title="Voir les détails">
                        👁️
                    </button>
                    <a href="/vote/${vote.slug}" target="_blank" class="action-btn" title="Voir le vote public">
                        🔗
                    </a>
                    <button class="action-btn" onclick="dashboard.editVote('${vote.id}')" title="Modifier">
                        ✏️
                    </button>
                    <button class="action-btn danger" onclick="dashboard.confirmDeleteVote('${vote.id}')" title="Supprimer">
                        🗑️
                    </button>
                </div>
            </div>
        `).join('');
    }

    updatePagination() {
        const totalPages = Math.ceil(this.totalVotes / this.votesPerPage);

        if (totalPages <= 1) {
            this.pagination.hidden = true;
            return;
        }

        this.pagination.hidden = false;
        this.prevPageBtn.disabled = this.currentPage <= 1;
        this.nextPageBtn.disabled = this.currentPage >= totalPages;
        this.paginationInfo.textContent = `Page ${this.currentPage} sur ${totalPages}`;
    }

    filterVotes() {
        this.currentPage = 1;
        this.loadVotes();
    }

    goToPreviousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadVotes();
        }
    }

    goToNextPage() {
        const totalPages = Math.ceil(this.totalVotes / this.votesPerPage);
        if (this.currentPage < totalPages) {
            this.currentPage++;
            this.loadVotes();
        }
    }

    toggleUserMenu() {
        const isExpanded = this.userMenu.getAttribute('aria-expanded') === 'true';
        this.userMenu.setAttribute('aria-expanded', !isExpanded);

        if (!isExpanded) {
            // Focus first menu item
            setTimeout(() => {
                const firstItem = this.userDropdown.querySelector('.dropdown-item');
                if (firstItem) firstItem.focus();
            }, 100);
        }
    }

    closeUserMenu() {
        this.userMenu.setAttribute('aria-expanded', 'false');
    }

    async showVoteDetails(voteId) {
        // Implementation for showing vote details modal
        console.log('Show vote details:', voteId);
        // This would load and display detailed vote information
    }

    editVote(voteId) {
        // Implementation for editing a vote
        console.log('Edit vote:', voteId);
        // This would navigate to the edit interface
    }

    confirmDeleteVote(voteId) {
        this.selectedVoteId = voteId;
        this.deleteVoteModal.hidden = false;

        // Focus the cancel button
        const cancelBtn = this.deleteVoteModal.querySelector('[data-action="cancel"]');
        if (cancelBtn) cancelBtn.focus();
    }

    async confirmDeleteVote() {
        if (!this.selectedVoteId) return;

        try {
            this.setDeleteLoading(true);

            const token = localStorage.getItem('access_token');
            const response = await fetch(`/api/votes/${this.selectedVoteId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                this.closeAllModals();
                this.loadVotes();
                this.liveRegion.textContent = 'Vote supprimé avec succès';
            } else {
                throw new Error('Failed to delete vote');
            }
        } catch (error) {
            console.error('Failed to delete vote:', error);
            alert('Erreur lors de la suppression du vote');
        } finally {
            this.setDeleteLoading(false);
        }
    }

    setDeleteLoading(loading) {
        const btnText = this.confirmDeleteBtn.querySelector('.btn-text');
        const btnLoading = this.confirmDeleteBtn.querySelector('.btn-loading');

        if (loading) {
            btnText.hidden = true;
            btnLoading.hidden = false;
            this.confirmDeleteBtn.disabled = true;
        } else {
            btnText.hidden = false;
            btnLoading.hidden = true;
            this.confirmDeleteBtn.disabled = false;
        }
    }

    closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.hidden = true;
        });
        this.selectedVoteId = null;
    }

    async handleLogout() {
        try {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('remember_email');
            localStorage.removeItem('remember_me');

            // Optional: call logout endpoint
            const token = localStorage.getItem('access_token');
            if (token) {
                try {
                    await fetch('/api/auth/logout', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });
                } catch (error) {
                    console.log('Logout endpoint error (non-critical):', error);
                }
            }

            this.liveRegion.textContent = 'Déconnexion en cours...';
            window.location.href = '/auth/login';
        } catch (error) {
            console.error('Logout error:', error);
            window.location.href = '/auth/login';
        }
    }

    handleAuthError() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/auth/login';
    }

    // Utility functions
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('fr-FR');
    }

    formatTimeAgo(dateString) {
        const now = new Date();
        const date = new Date(dateString);
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) return 'À l\'instant';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} min`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h`;
        return `${Math.floor(diffInSeconds / 86400)}j`;
    }

    getStatusText(status) {
        const statusTexts = {
            draft: 'Brouillon',
            active: 'Actif',
            ended: 'Terminé',
            archived: 'Archivé'
        };
        return statusTexts[status] || status;
    }

    getActivityIcon(type) {
        const icons = {
            vote_created: '✅',
            vote_published: '🚀',
            response_received: '💬',
            vote_ended: '⏰',
            default: '📝'
        };
        return icons[type] || icons.default;
    }
}

// Initialize dashboard when DOM is loaded
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new DashboardManager();
});

// Make dashboard available globally for onclick handlers
window.dashboard = dashboard;
