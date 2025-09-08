/**
 * Admin JavaScript for Cardinal Vote Voting Platform
 * Provides common functionality for admin interface
 */

// Global admin utilities
window.AdminUtils = {
    // Message display system
    showMessage: function(message, type = 'info', duration = 5000) {
        const messageContainer = document.getElementById('messageContainer');
        if (!messageContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        let icon = 'fa-info-circle';
        if (type === 'success') icon = 'fa-check-circle';
        else if (type === 'error') icon = 'fa-exclamation-circle';

        messageDiv.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
        `;

        messageContainer.appendChild(messageDiv);

        // Auto-remove message after duration
        setTimeout(() => {
            messageDiv.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.parentNode.removeChild(messageDiv);
                }
            }, 300);
        }, duration);

        // Add click to dismiss
        messageDiv.addEventListener('click', () => {
            messageDiv.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.parentNode.removeChild(messageDiv);
                }
            }, 300);
        });
    },

    // Loading overlay
    showLoading: function() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.add('show');
        }
    },

    hideLoading: function() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('show');
        }
    },

    // Confirmation modal
    showConfirm: function(title, message, onConfirm, onCancel = null) {
        const modal = document.getElementById('confirmModal');
        const titleEl = document.getElementById('confirmTitle');
        const messageEl = document.getElementById('confirmMessage');
        const cancelBtn = document.getElementById('confirmCancel');
        const okBtn = document.getElementById('confirmOk');

        if (!modal) return;

        titleEl.textContent = title;
        messageEl.textContent = message;

        modal.classList.add('show');

        // Event handlers
        const handleConfirm = () => {
            modal.classList.remove('show');
            if (onConfirm) onConfirm();
            cleanup();
        };

        const handleCancel = () => {
            modal.classList.remove('show');
            if (onCancel) onCancel();
            cleanup();
        };

        const cleanup = () => {
            okBtn.removeEventListener('click', handleConfirm);
            cancelBtn.removeEventListener('click', handleCancel);
            modal.removeEventListener('click', handleModalClick);
        };

        const handleModalClick = (e) => {
            if (e.target === modal) {
                handleCancel();
            }
        };

        okBtn.addEventListener('click', handleConfirm);
        cancelBtn.addEventListener('click', handleCancel);
        modal.addEventListener('click', handleModalClick);
    },

    // CSRF helper
    getCsrfToken: function() {
        return window.csrfToken || '';
    },

    // Fetch wrapper with CSRF token
    fetchWithCsrf: async function(url, options = {}) {
        const defaultOptions = {
            headers: {
                'X-CSRF-Token': this.getCsrfToken(),
                ...options.headers
            }
        };

        return fetch(url, { ...options, ...defaultOptions });
    },

    // Format file size
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    },

    // Format date
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Form serialization
    serializeForm: function(form) {
        const formData = new FormData(form);
        const data = {};
        for (let [key, value] of formData.entries()) {
            if (data[key]) {
                if (Array.isArray(data[key])) {
                    data[key].push(value);
                } else {
                    data[key] = [data[key], value];
                }
            } else {
                data[key] = value;
            }
        }
        return data;
    },

    // URL parameter helpers
    getUrlParam: function(param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    },

    setUrlParam: function(param, value) {
        const url = new URL(window.location);
        if (value) {
            url.searchParams.set(param, value);
        } else {
            url.searchParams.delete(param);
        }
        window.history.replaceState({}, '', url);
    }
};

// Make utilities available globally
window.showMessage = window.AdminUtils.showMessage;
window.showLoading = window.AdminUtils.showLoading;
window.hideLoading = window.AdminUtils.hideLoading;
window.showConfirm = window.AdminUtils.showConfirm;

// Logo Management Functions
window.LogoManager = {
    // Upload logo
    uploadLogo: async function(formData) {
        try {
            showLoading();

            const response = await fetch('/admin/logos/upload', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRF-Token': window.csrfToken
                }
            });

            const result = await response.json();

            if (result.success) {
                showMessage(result.message, 'success');
                // Refresh the page or update the logos list
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showMessage(result.message, 'error');
            }

            return result;
        } catch (error) {
            console.error('Logo upload error:', error);
            showMessage('Erreur lors de l\'upload', 'error');
            return { success: false, error: error.message };
        } finally {
            hideLoading();
        }
    },

    // Delete logos
    deleteLogos: async function(logoNames) {
        if (logoNames.length === 0) {
            showMessage('Aucun logo sélectionné', 'error');
            return;
        }

        const confirmMessage = logoNames.length === 1
            ? `Êtes-vous sûr de vouloir supprimer le logo "${logoNames[0]}" ?`
            : `Êtes-vous sûr de vouloir supprimer ${logoNames.length} logos ?`;

        showConfirm('Confirmer la suppression', confirmMessage, async () => {
            try {
                showLoading();

                const formData = new FormData();
                formData.append('operation', 'bulk_delete');
                formData.append('logos', JSON.stringify(logoNames));
                formData.append('csrf_token', window.csrfToken);

                const response = await fetch('/admin/logos/manage', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.success) {
                    showMessage(result.message, 'success');
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    showMessage(result.message, 'error');
                }

            } catch (error) {
                console.error('Delete logos error:', error);
                showMessage('Erreur lors de la suppression', 'error');
            } finally {
                hideLoading();
            }
        });
    },

    // Rename logo
    renameLogo: async function(oldName, newName) {
        if (!newName || newName === oldName) {
            showMessage('Nouveau nom invalide', 'error');
            return;
        }

        try {
            showLoading();

            const formData = new FormData();
            formData.append('operation', 'rename');
            formData.append('logos', JSON.stringify([oldName]));
            formData.append('new_name', newName);
            formData.append('csrf_token', window.csrfToken);

            const response = await fetch('/admin/logos/manage', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                showMessage(result.message, 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showMessage(result.message, 'error');
            }

        } catch (error) {
            console.error('Rename logo error:', error);
            showMessage('Erreur lors du renommage', 'error');
        } finally {
            hideLoading();
        }
    }
};

// Vote Management Functions
window.VoteManager = {
    // Export votes
    exportVotes: async function(format = 'csv') {
        try {
            showLoading();

            const response = await fetch(`/admin/votes/export/${format}`, {
                headers: {
                    'X-CSRF-Token': window.csrfToken
                }
            });

            if (response.ok) {
                // Trigger download
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `votes_export_${new Date().toISOString().slice(0, 10)}.${format}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                showMessage('Export réussi', 'success');
            } else {
                const result = await response.json();
                showMessage(result.message || 'Erreur lors de l\'export', 'error');
            }
        } catch (error) {
            console.error('Export error:', error);
            showMessage('Erreur lors de l\'export', 'error');
        } finally {
            hideLoading();
        }
    },

    // Reset all votes
    resetAllVotes: async function() {
        showConfirm(
            'ATTENTION - Suppression de tous les votes',
            'Cette action supprimera définitivement TOUS les votes de la base de données. Cette action est irréversible. Êtes-vous absolument sûr ?',
            async () => {
                try {
                    showLoading();

                    const formData = new FormData();
                    formData.append('operation', 'reset');
                    formData.append('csrf_token', window.csrfToken);

                    const response = await fetch('/admin/votes/manage', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();

                    if (result.success) {
                        showMessage(result.message, 'success');
                        setTimeout(() => {
                            window.location.reload();
                        }, 1500);
                    } else {
                        showMessage(result.message, 'error');
                    }

                } catch (error) {
                    console.error('Reset votes error:', error);
                    showMessage('Erreur lors de la remise à zéro', 'error');
                } finally {
                    hideLoading();
                }
            }
        );
    },

    // Delete voter votes
    deleteVoterVotes: async function(voterName) {
        if (!voterName) {
            showMessage('Nom du votant requis', 'error');
            return;
        }

        showConfirm(
            'Confirmer la suppression',
            `Supprimer tous les votes de "${voterName}" ?`,
            async () => {
                try {
                    showLoading();

                    const formData = new FormData();
                    formData.append('operation', 'delete_voter');
                    formData.append('voter_name', voterName);
                    formData.append('csrf_token', window.csrfToken);

                    const response = await fetch('/admin/votes/manage', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();

                    if (result.success) {
                        showMessage(result.message, 'success');
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    } else {
                        showMessage(result.message, 'error');
                    }

                } catch (error) {
                    console.error('Delete voter votes error:', error);
                    showMessage('Erreur lors de la suppression', 'error');
                } finally {
                    hideLoading();
                }
            }
        );
    }
};

// System Management Functions
window.SystemManager = {
    // Create backup
    createBackup: async function() {
        showConfirm(
            'Créer une sauvegarde',
            'Créer une sauvegarde de la base de données ?',
            async () => {
                try {
                    showLoading();

                    const formData = new FormData();
                    formData.append('csrf_token', window.csrfToken);

                    const response = await fetch('/admin/system/backup', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();

                    if (result.success) {
                        showMessage(result.message, 'success');
                    } else {
                        showMessage(result.message, 'error');
                    }

                } catch (error) {
                    console.error('Backup error:', error);
                    showMessage('Erreur lors de la sauvegarde', 'error');
                } finally {
                    hideLoading();
                }
            }
        );
    },

    // Clean up sessions
    cleanupSessions: async function() {
        try {
            showLoading();

            const formData = new FormData();
            formData.append('csrf_token', window.csrfToken);

            const response = await fetch('/admin/system/cleanup-sessions', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                showMessage(result.message, 'success');
            } else {
                showMessage(result.message, 'error');
            }

        } catch (error) {
            console.error('Session cleanup error:', error);
            showMessage('Erreur lors du nettoyage', 'error');
        } finally {
            hideLoading();
        }
    }
};

// Initialize admin interface
document.addEventListener('DOMContentLoaded', function() {
    // Add slideOut animation to CSS if not present
    if (!document.querySelector('style[data-admin-animations]')) {
        const style = document.createElement('style');
        style.setAttribute('data-admin-animations', 'true');
        style.textContent = `
            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }

    // Handle navigation active states
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.admin-nav-item');
    navItems.forEach(item => {
        if (item.getAttribute('href') === currentPath) {
            item.classList.add('active');
        }
    });

    // Auto-hide messages after 5 seconds
    const existingMessages = document.querySelectorAll('.message');
    existingMessages.forEach(message => {
        setTimeout(() => {
            if (message.parentNode) {
                message.style.animation = 'slideOut 0.3s ease forwards';
                setTimeout(() => {
                    if (message.parentNode) {
                        message.parentNode.removeChild(message);
                    }
                }, 300);
            }
        }, 5000);
    });

    // Handle session timeout
    let sessionWarningShown = false;
    const checkSession = async () => {
        try {
            const response = await fetch('/admin/api/stats', {
                headers: {
                    'X-CSRF-Token': window.csrfToken
                }
            });

            if (response.status === 401) {
                if (!sessionWarningShown) {
                    sessionWarningShown = true;
                    showMessage('Session expirée. Redirection vers la page de connexion...', 'error');
                    setTimeout(() => {
                        window.location.href = '/admin/login';
                    }, 2000);
                }
            }
        } catch (error) {
            // Silently handle errors - network issues shouldn't trigger redirects
        }
    };

    // Check session every 5 minutes
    setInterval(checkSession, 5 * 60 * 1000);

    console.log('Admin interface initialized');
});
