/**
 * WORKFORCE INTELLIGENCE & MANAGEMENT PLATFORM
 * Core Frontend Interactive Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    initThemeAndViewport();
    initSidebarToggle();
    initNotifications();
    initModals();
    initProgressSliders();
    initTableSearchAndFilters();
});

/* ==========================================================================
   Toast Notification System
   ========================================================================== */
function showToast(title, message, type = 'info', duration = 4500) {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;

    const iconMap = {
        success: 'fa-check-circle text-emerald-500',
        danger: 'fa-circle-xmark text-rose-500',
        warning: 'fa-triangle-exclamation text-amber-500',
        info: 'fa-circle-info text-sky-500'
    };
    const iconClass = iconMap[type] || 'fa-bell text-indigo-500';

    toast.innerHTML = `
        <i class="fas ${iconClass}" style="font-size: 20px; margin-top: 2px;"></i>
        <div class="toast-content">
            <div class="toast-title">${escapeHTML(title)}</div>
            <div class="toast-message">${escapeHTML(message)}</div>
        </div>
        <button type="button" style="background:none; border:none; color:#94a3b8; cursor:pointer; font-size:16px;" onclick="this.parentElement.remove()">
            <i class="fas fa-xmark"></i>
        </button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/* ==========================================================================
   Modal Controller
   ========================================================================== */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

function initModals() {
    // Close modal on click outside dialog
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    });

    // Close on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay.active').forEach(m => {
                m.classList.remove('active');
            });
            document.body.style.overflow = '';
        }
    });
}

/* ==========================================================================
   Leave Review Modal Populator (Team Lead)
   ========================================================================== */
function openLeaveReviewModal(leaveId, empName, leaveType, dates, reason, hasImpact, impactText) {
    const form = document.getElementById('leaveReviewForm');
    if (!form) return;

    form.action = `/team-lead/leaves/${leaveId}/action`;
    document.getElementById('lrModalEmpName').textContent = empName;
    document.getElementById('lrModalType').textContent = leaveType;
    document.getElementById('lrModalDates').textContent = dates;
    document.getElementById('lrModalReason').textContent = reason;

    const impactBox = document.getElementById('lrModalImpactBox');
    const impactContent = document.getElementById('lrModalImpactContent');

    if (hasImpact === 'true' || hasImpact === true) {
        impactBox.style.display = 'flex';
        impactContent.innerText = impactText;
    } else {
        impactBox.style.display = 'none';
    }

    // Reset rejection reason box
    const rejBox = document.getElementById('rejectionReasonBox');
    if (rejBox) rejBox.style.display = 'none';

    openModal('leaveReviewModal');
}

function toggleRejectionInput() {
    const rejBox = document.getElementById('rejectionReasonBox');
    if (rejBox) {
        rejBox.style.display = rejBox.style.display === 'none' ? 'block' : 'none';
        if (rejBox.style.display === 'block') {
            document.getElementById('rejectionReasonInput').focus();
        }
    }
}

/* ==========================================================================
   Task Completion Confirmation Modal (Employee)
   ========================================================================== */
function confirmTaskCompletion(taskId, taskTitle) {
    const form = document.getElementById('completeTaskForm');
    if (!form) return;
    
    document.getElementById('completeTaskTitle').textContent = taskTitle;
    document.getElementById('completeTaskIdInput').value = taskId;
    openModal('completeTaskModal');
}

/* ==========================================================================
   Task Reassignment Modal Populator (Team Lead)
   ========================================================================== */
function openReassignModal(taskId, taskTitle, currentAssignee) {
    const form = document.getElementById('reassignTaskForm');
    if (!form) return;

    form.action = `/team-lead/tasks/${taskId}/reassign`;
    document.getElementById('reassignTaskTitle').textContent = taskTitle;
    document.getElementById('reassignCurrentAssignee').textContent = currentAssignee;
    openModal('reassignTaskModal');
}

/* ==========================================================================
   Sidebar & Mobile Navigation
   ========================================================================== */
function initSidebarToggle() {
    const toggleBtn = document.getElementById('sidebarToggleBtn');
    const sidebar = document.getElementById('appSidebar');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });

        // Close sidebar on click outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 1024 && !sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
                sidebar.classList.remove('show');
            }
        });
    }
}

/* ==========================================================================
   Notification Dropdown & Mark Read
   ========================================================================== */
function initNotifications() {
    const bellBtn = document.getElementById('notificationBellBtn');
    const dropdown = document.getElementById('notificationDropdown');

    if (bellBtn && dropdown) {
        bellBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('active');
            if (dropdown.classList.contains('active')) {
                loadNotificationsList();
            }
        });

        document.addEventListener('click', (e) => {
            if (!dropdown.contains(e.target) && !bellBtn.contains(e.target)) {
                dropdown.classList.remove('active');
            }
        });
    }
}

async function loadNotificationsList() {
    const listContainer = document.getElementById('notificationItemsContainer');
    if (!listContainer) return;

    listContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: #94a3b8;"><i class="fas fa-spinner fa-spin"></i> Loading notifications...</div>';

    try {
        const resp = await fetch('/api/notifications/list');
        const data = await resp.json();

        if (!data.notifications || data.notifications.length === 0) {
            listContainer.innerHTML = `
                <div style="padding: 30px 20px; text-align: center; color: #94a3b8;">
                    <i class="far fa-bell-slash" style="font-size: 28px; margin-bottom: 8px; display: block;"></i>
                    <p style="font-size: 13px; font-weight: 600;">No notifications right now</p>
                </div>
            `;
            return;
        }

        listContainer.innerHTML = data.notifications.map(n => `
            <div class="notif-row ${n.is_read ? 'read' : 'unread'}" onclick="markNotificationRead(${n.id}, '${n.link || ''}')" style="padding: 12px 16px; border-bottom: 1px solid #f1f5f9; cursor: pointer; transition: background 0.15s; background: ${n.is_read ? '#ffffff' : '#f8faff'};">
                <div style="display: flex; gap: 10px; align-items: flex-start;">
                    <div style="margin-top: 2px;">
                        <span class="badge ${n.is_read ? 'badge-secondary' : 'badge-primary'}" style="padding: 2px 6px; font-size: 9px;">${escapeHTML(n.type)}</span>
                    </div>
                    <div style="flex: 1;">
                        <div style="font-size: 13px; font-weight: ${n.is_read ? '600' : '700'}; color: #0f172a;">${escapeHTML(n.title)}</div>
                        <div style="font-size: 12px; color: #64748b; margin-top: 2px;">${escapeHTML(n.message)}</div>
                        <div style="font-size: 10px; color: #94a3b8; margin-top: 4px;">${n.time_ago}</div>
                    </div>
                </div>
            </div>
        `).join('');

    } catch (err) {
        listContainer.innerHTML = '<div style="padding: 15px; color: #ef4444; font-size: 12px;">Failed to load notifications.</div>';
    }
}

async function markNotificationRead(notifId, link) {
    try {
        await fetch(`/api/notifications/${notifId}/mark-read`, { method: 'POST' });
        const badge = document.getElementById('notificationCountBadge');
        if (badge) {
            let count = parseInt(badge.textContent || '0');
            if (count > 1) {
                badge.textContent = count - 1;
            } else {
                badge.style.display = 'none';
            }
        }
        if (link && link !== 'null' && link !== '') {
            window.location.href = link;
        } else {
            loadNotificationsList();
        }
    } catch (err) {
        console.error("Error marking notification as read:", err);
    }
}

async function markAllNotificationsRead() {
    try {
        await fetch('/api/notifications/mark-all-read', { method: 'POST' });
        const badge = document.getElementById('notificationCountBadge');
        if (badge) badge.style.display = 'none';
        loadNotificationsList();
        showToast('Success', 'All notifications marked as read', 'success');
    } catch (err) {
        console.error(err);
    }
}

/* ==========================================================================
   Task Progress Slider
   ========================================================================== */
function initProgressSliders() {
    const sliders = document.querySelectorAll('.task-progress-slider');
    sliders.forEach(slider => {
        const valDisplay = document.getElementById(`valDisplay_${slider.dataset.taskId}`);
        slider.addEventListener('input', (e) => {
            if (valDisplay) {
                valDisplay.textContent = `${e.target.value}%`;
            }
        });
    });
}

/* ==========================================================================
   Table Search & Filtering Utility
   ========================================================================== */
function initTableSearchAndFilters() {
    const searchInputs = document.querySelectorAll('[data-table-search]');
    searchInputs.forEach(input => {
        const targetTableId = input.dataset.tableSearch;
        const table = document.getElementById(targetTableId);
        if (!table) return;

        input.addEventListener('input', () => {
            const query = input.value.toLowerCase().trim();
            const rows = table.querySelectorAll('tbody tr');

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        });
    });
}

/* ==========================================================================
   Security Utility
   ========================================================================== */
function escapeHTML(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

/* ==========================================================================
   Theme & Responsive Viewport Toggle Controller
   ========================================================================== */
function initThemeAndViewport() {
    // 1. Theme Toggle (Top-Right, Icon Only)
    const themeBtn = document.getElementById('themeToggleBtn');
    const themeIcon = document.getElementById('themeToggleIcon');

    // Load saved theme
    const savedTheme = localStorage.getItem('workforce_theme') || 'light';
    applyTheme(savedTheme);

    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
        });
    }

    function applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
            document.body.setAttribute('data-theme', 'dark');
            if (themeIcon) {
                themeIcon.className = 'fas fa-sun';
                themeIcon.style.color = '#f59e0b';
            }
            localStorage.setItem('workforce_theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
            document.body.removeAttribute('data-theme');
            if (themeIcon) {
                themeIcon.className = 'fas fa-moon';
                themeIcon.style.color = '';
            }
            localStorage.setItem('workforce_theme', 'light');
        }
    }

    // 2. Viewport Preview Toggle (Top-Left, Icon Only)
    const viewportBtn = document.getElementById('viewportPreviewToggleBtn');
    const viewportIcon = document.getElementById('viewportPreviewIcon');
    const container = document.querySelector('.app-container');

    if (viewportBtn && container) {
        viewportBtn.addEventListener('click', () => {
            const isMobile = container.classList.toggle('device-preview-mobile');
            if (isMobile) {
                viewportIcon.className = 'fas fa-desktop';
                viewportBtn.title = 'Switch to Desktop View';
                showToast('View Preview', 'Previewing Mobile View Layout', 'info', 2000);
            } else {
                viewportIcon.className = 'fas fa-mobile-screen-button';
                viewportBtn.title = 'Switch to Mobile View';
                showToast('View Preview', 'Restored Desktop View Layout', 'info', 2000);
            }
        });
    }
}
