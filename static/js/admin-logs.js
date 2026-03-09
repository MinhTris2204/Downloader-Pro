// Admin Logs - Combined Error Logs and System Logs
// Tab management
let currentTab = 'error-logs';

// Error Logs state
let errorCurrentPage = 0;
let errorCurrentType = 'all';
let errorSearchTerm = '';
let errorAllLogs = [];
const errorLimit = 50;

// System Logs state
let systemCurrentPage = 0;
let systemCurrentLevel = 'all';
let systemCurrentSource = 'all';
let systemSearchTerm = '';
let systemAllLogs = [];
const systemLimit = 100;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    loadErrorLogs();
});

// Tab Management
function setupTabs() {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.dataset.tab;
            
            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Update active content
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            
            currentTab = tabId;
            
            // Load data for the active tab
            if (tabId === 'error-logs') {
                loadErrorLogs();
            } else if (tabId === 'system-logs') {
                loadSystemLogs();
            }
        });
    });
}

// ==================== ERROR LOGS ====================

document.getElementById('errorFilterType').addEventListener('change', (e) => {
    errorCurrentType = e.target.value;
    errorCurrentPage = 0;
    loadErrorLogs();
});

document.getElementById('errorSearchBox').addEventListener('input', (e) => {
    errorSearchTerm = e.target.value.toLowerCase();
    filterAndRenderErrorLogs();
});

async function loadErrorLogs() {
    try {
        const response = await fetch(`/api/admin/error-logs?type=${errorCurrentType}&limit=${errorLimit}&offset=${errorCurrentPage * errorLimit}`);
        const data = await response.json();

        if (data.error) {
            alert('Lỗi: ' + data.error);
            return;
        }

        errorAllLogs = data.logs;
        updateErrorStats(data.stats, data.total);
        filterAndRenderErrorLogs();
        updateErrorPagination(data.total);

    } catch (error) {
        console.error('Error loading error logs:', error);
        document.getElementById('errorLogsContent').innerHTML = `
            <div class="empty-state">
                <div>❌ Lỗi khi tải logs: ${error.message}</div>
            </div>
        `;
    }
}

function updateErrorStats(stats, total) {
    const statsGrid = document.getElementById('errorStatsGrid');
    statsGrid.innerHTML = `
        <div class="stat-card ${errorCurrentType === 'all' ? 'active' : ''}" onclick="filterErrorByType('all')">
            <div class="label">Tất cả lỗi</div>
            <div class="value">${total}</div>
        </div>
    `;

    const typeLabels = {
        'extraction_failed': 'Extraction Failed',
        'geo_blocked': 'Geo Blocked',
        'bot_detection': 'Bot Detection',
        'video_unavailable': 'Video Unavailable',
        'age_restricted': 'Age Restricted',
        'copyright': 'Copyright',
        'network_error': 'Network Error',
        'live_video': 'Live Video',
        'unknown_error': 'Unknown Error'
    };

    for (const [type, count] of Object.entries(stats)) {
        if (type === 'all' || count === 0) continue;
        
        statsGrid.innerHTML += `
            <div class="stat-card ${errorCurrentType === type ? 'active' : ''}" onclick="filterErrorByType('${type}')">
                <div class="label">${typeLabels[type] || type}</div>
                <div class="value">${count}</div>
            </div>
        `;
    }
}

function filterErrorByType(type) {
    errorCurrentType = type;
    errorCurrentPage = 0;
    document.getElementById('errorFilterType').value = type;
    loadErrorLogs();
}

function filterAndRenderErrorLogs() {
    let filtered = errorAllLogs;

    if (errorSearchTerm) {
        filtered = errorAllLogs.filter(log => 
            log.error_message.toLowerCase().includes(errorSearchTerm) ||
            (log.url && log.url.toLowerCase().includes(errorSearchTerm))
        );
    }

    renderErrorLogs(filtered);
}

function renderErrorLogs(logs) {
    const container = document.getElementById('errorLogsContent');

    if (logs.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div>📭 Không có lỗi nào được ghi nhận</div>
            </div>
        `;
        return;
    }

    container.innerHTML = logs.map(log => `
        <div class="log-item" data-id="${log.id}">
            <div class="log-header">
                <span class="log-badge ${log.error_type}">${log.error_type}</span>
                <span class="log-time">${formatDate(log.created_at)}</span>
            </div>
            
            <div class="log-message">${escapeHtml(log.error_message)}</div>
            
            <div class="log-details">
                ${log.url ? `<div class="log-detail"><strong>URL:</strong> ${escapeHtml(log.url)}</div>` : ''}
                ${log.platform ? `<div class="log-detail"><strong>Platform:</strong> ${log.platform}</div>` : ''}
                ${log.format ? `<div class="log-detail"><strong>Format:</strong> ${log.format}</div>` : ''}
                ${log.quality ? `<div class="log-detail"><strong>Quality:</strong> ${log.quality}</div>` : ''}
                ${log.ip_address ? `<div class="log-detail"><strong>IP:</strong> ${log.ip_address}</div>` : ''}
                ${log.user_id ? `<div class="log-detail"><strong>User ID:</strong> ${log.user_id}</div>` : ''}
            </div>
            
            ${log.stack_trace ? `<div class="log-stack" id="error-stack-${log.id}">${escapeHtml(log.stack_trace)}</div>` : ''}
            
            <div class="log-actions">
                ${log.stack_trace ? `<button class="btn-toggle" onclick="toggleErrorStack(${log.id})">📋 Stack Trace</button>` : ''}
                <button class="btn-delete" onclick="deleteErrorLog(${log.id})">🗑️ Xóa</button>
            </div>
        </div>
    `).join('');
}

function toggleErrorStack(id) {
    const stack = document.getElementById(`error-stack-${id}`);
    stack.classList.toggle('show');
}

async function deleteErrorLog(id) {
    if (!confirm('Xóa log này?')) return;

    try {
        const response = await fetch(`/api/admin/error-logs/${id}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            loadErrorLogs();
        } else {
            alert('Lỗi: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Lỗi: ' + error.message);
    }
}

async function clearErrorLogs() {
    if (!confirm('Xóa TẤT CẢ error logs?')) return;

    try {
        const response = await fetch('/api/admin/error-logs/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: errorCurrentType })
        });

        const data = await response.json();

        if (data.success) {
            alert(`Đã xóa ${data.deleted} logs`);
            loadErrorLogs();
        } else {
            alert('Lỗi: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Lỗi: ' + error.message);
    }
}

async function clearOldErrorLogs() {
    if (!confirm('Xóa error logs cũ hơn 7 ngày?')) return;

    try {
        const response = await fetch('/api/admin/error-logs/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ days: 7 })
        });

        const data = await response.json();

        if (data.success) {
            alert(`Đã xóa ${data.deleted} logs cũ`);
            loadErrorLogs();
        } else {
            alert('Lỗi: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Lỗi: ' + error.message);
    }
}

function refreshErrorLogs() {
    loadErrorLogs();
}

function updateErrorPagination(total) {
    const pagination = document.getElementById('errorPagination');
    const prevBtn = document.getElementById('errorPrevBtn');
    const nextBtn = document.getElementById('errorNextBtn');
    const pageInfo = document.getElementById('errorPageInfo');

    const totalPages = Math.ceil(total / errorLimit);

    if (totalPages <= 1) {
        pagination.style.display = 'none';
        return;
    }

    pagination.style.display = 'flex';
    prevBtn.disabled = errorCurrentPage === 0;
    nextBtn.disabled = errorCurrentPage >= totalPages - 1;
    pageInfo.textContent = `Trang ${errorCurrentPage + 1} / ${totalPages}`;
}

function prevErrorPage() {
    if (errorCurrentPage > 0) {
        errorCurrentPage--;
        loadErrorLogs();
    }
}

function nextErrorPage() {
    errorCurrentPage++;
    loadErrorLogs();
}

// ==================== SYSTEM LOGS ====================

document.getElementById('systemFilterLevel').addEventListener('change', (e) => {
    systemCurrentLevel = e.target.value;
    systemCurrentPage = 0;
    loadSystemLogs();
});

document.getElementById('systemFilterSource').addEventListener('change', (e) => {
    systemCurrentSource = e.target.value;
    systemCurrentPage = 0;
    loadSystemLogs();
});

document.getElementById('systemSearchBox').addEventListener('input', (e) => {
    systemSearchTerm = e.target.value.toLowerCase();
    filterAndRenderSystemLogs();
});

async function loadSystemLogs() {
    try {
        const response = await fetch(`/api/admin/system-logs?level=${systemCurrentLevel}&source=${systemCurrentSource}&limit=${systemLimit}&offset=${systemCurrentPage * systemLimit}`);
        const data = await response.json();

        if (data.error) {
            alert('Lỗi: ' + data.error);
            return;
        }

        systemAllLogs = data.logs;
        updateSystemStats(data.level_stats, data.source_stats, data.total);
        filterAndRenderSystemLogs();
        updateSystemPagination(data.total);

    } catch (error) {
        console.error('Error loading system logs:', error);
        document.getElementById('systemLogsContent').innerHTML = `
            <div class="empty-state">
                <div>❌ Lỗi khi tải logs: ${error.message}</div>
            </div>
        `;
    }
}

function updateSystemStats(levelStats, sourceStats, total) {
    const statsGrid = document.getElementById('systemStatsGrid');
    statsGrid.innerHTML = `
        <div class="stat-card ${systemCurrentLevel === 'all' ? 'active' : ''}" onclick="filterSystemByLevel('all')">
            <div class="label">Tất cả</div>
            <div class="value">${total}</div>
        </div>
    `;

    const levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'];
    for (const level of levels) {
        const count = levelStats[level] || 0;
        if (count === 0) continue;
        
        statsGrid.innerHTML += `
            <div class="stat-card ${systemCurrentLevel === level ? 'active' : ''}" onclick="filterSystemByLevel('${level}')">
                <div class="label">${level}</div>
                <div class="value">${count}</div>
            </div>
        `;
    }

    // Update source filter
    const sourceFilter = document.getElementById('systemFilterSource');
    const currentValue = sourceFilter.value;
    sourceFilter.innerHTML = '<option value="all">Tất cả sources</option>';
    
    for (const [source, count] of Object.entries(sourceStats)) {
        const option = document.createElement('option');
        option.value = source;
        option.textContent = `${source} (${count})`;
        sourceFilter.appendChild(option);
    }
    
    sourceFilter.value = currentValue;
}

function filterSystemByLevel(level) {
    systemCurrentLevel = level;
    systemCurrentPage = 0;
    document.getElementById('systemFilterLevel').value = level;
    loadSystemLogs();
}

function filterAndRenderSystemLogs() {
    let filtered = systemAllLogs;

    if (systemSearchTerm) {
        filtered = systemAllLogs.filter(log => 
            log.log_message.toLowerCase().includes(systemSearchTerm) ||
            (log.log_source && log.log_source.toLowerCase().includes(systemSearchTerm)) ||
            (log.url && log.url.toLowerCase().includes(systemSearchTerm))
        );
    }

    renderSystemLogs(filtered);
}

function renderSystemLogs(logs) {
    const container = document.getElementById('systemLogsContent');

    if (logs.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div>📭 Không có logs nào</div>
            </div>
        `;
        return;
    }

    container.innerHTML = logs.map(log => `
        <div class="log-item" data-id="${log.id}">
            <div class="log-header">
                <span class="log-badge ${log.log_level}">${log.log_level}</span>
                <span class="log-time">${formatDate(log.created_at)}</span>
            </div>
            
            <div class="log-content">
                ${log.log_source ? `<span class="log-source">${escapeHtml(log.log_source)}</span>` : ''}
                <div class="log-message">${escapeHtml(log.log_message)}</div>
            </div>
            
            <div class="log-details">
                ${log.url ? `<div class="log-detail"><strong>URL:</strong> ${escapeHtml(log.url)}</div>` : ''}
                ${log.method ? `<div class="log-detail"><strong>Method:</strong> ${log.method}</div>` : ''}
                ${log.status_code ? `<div class="log-detail"><strong>Status:</strong> ${log.status_code}</div>` : ''}
                ${log.execution_time ? `<div class="log-detail"><strong>Time:</strong> ${log.execution_time.toFixed(3)}s</div>` : ''}
                ${log.ip_address ? `<div class="log-detail"><strong>IP:</strong> ${log.ip_address}</div>` : ''}
                ${log.user_id ? `<div class="log-detail"><strong>User:</strong> ${log.user_id}</div>` : ''}
            </div>
            
            ${log.additional_data ? `
                <div class="log-data" id="system-data-${log.id}">${escapeHtml(JSON.stringify(log.additional_data, null, 2))}</div>
                <div class="log-actions">
                    <button class="btn-toggle" onclick="toggleSystemData(${log.id})">📋 Data</button>
                    <button class="btn-delete" onclick="deleteSystemLog(${log.id})">🗑️</button>
                </div>
            ` : `
                <div class="log-actions">
                    <button class="btn-delete" onclick="deleteSystemLog(${log.id})">🗑️</button>
                </div>
            `}
        </div>
    `).join('');
}

function toggleSystemData(id) {
    const data = document.getElementById(`system-data-${id}`);
    data.classList.toggle('show');
}

async function deleteSystemLog(id) {
    if (!confirm('Xóa log này?')) return;

    try {
        const response = await fetch(`/api/admin/system-logs/${id}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            loadSystemLogs();
        } else {
            alert('Lỗi: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Lỗi: ' + error.message);
    }
}

async function clearSystemLogs() {
    if (!confirm('Xóa TẤT CẢ system logs?')) return;

    try {
        const response = await fetch('/api/admin/system-logs/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ level: systemCurrentLevel, source: systemCurrentSource })
        });

        const data = await response.json();

        if (data.success) {
            alert(`Đã xóa ${data.deleted} logs`);
            loadSystemLogs();
        } else {
            alert('Lỗi: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Lỗi: ' + error.message);
    }
}

async function clearOldSystemLogs() {
    if (!confirm('Xóa system logs cũ hơn 7 ngày?')) return;

    try {
        const response = await fetch('/api/admin/system-logs/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ days: 7 })
        });

        const data = await response.json();

        if (data.success) {
            alert(`Đã xóa ${data.deleted} logs cũ`);
            loadSystemLogs();
        } else {
            alert('Lỗi: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Lỗi: ' + error.message);
    }
}

function refreshSystemLogs() {
    loadSystemLogs();
}

function updateSystemPagination(total) {
    const pagination = document.getElementById('systemPagination');
    const prevBtn = document.getElementById('systemPrevBtn');
    const nextBtn = document.getElementById('systemNextBtn');
    const pageInfo = document.getElementById('systemPageInfo');

    const totalPages = Math.ceil(total / systemLimit);

    if (totalPages <= 1) {
        pagination.style.display = 'none';
        return;
    }

    pagination.style.display = 'flex';
    prevBtn.disabled = systemCurrentPage === 0;
    nextBtn.disabled = systemCurrentPage >= totalPages - 1;
    pageInfo.textContent = `Trang ${systemCurrentPage + 1} / ${totalPages}`;
}

function prevSystemPage() {
    if (systemCurrentPage > 0) {
        systemCurrentPage--;
        loadSystemLogs();
    }
}

function nextSystemPage() {
    systemCurrentPage++;
    loadSystemLogs();
}

// ==================== UTILITY FUNCTIONS ====================

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleString('vi-VN');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
