// Admin Dashboard JavaScript

// Menu navigation
document.querySelectorAll('.menu-item').forEach(item => {
    item.addEventListener('click', function() {
        const section = this.dataset.section;
        
        // Update active menu
        document.querySelectorAll('.menu-item').forEach(m => m.classList.remove('active'));
        this.classList.add('active');
        
        // Update active section
        document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
        document.getElementById(section).classList.add('active');
        
        // Update page title
        const titles = {
            'overview': 'Tổng quan',
            'users': 'Quản lý người dùng',
            'premium-history': 'Lịch sử Premium',
            'tracking': 'Thống kê Tracking',
            'downloads': 'Lịch sử tải xuống',
            'settings': 'Cài đặt hệ thống'
        };
        document.getElementById('pageTitle').textContent = titles[section];
        
        // Update URL without reload
        const newUrl = `/admin/dashboard?section=${section}`;
        window.history.pushState({ section }, '', newUrl);
        
        // Load data for section
        if (section === 'tracking') {
            loadTrackingData();
        } else if (section === 'users') {
            loadUsers();
        } else if (section === 'premium-history') {
            loadPremiumHistory();
        } else if (section === 'downloads') {
            loadDownloadsHistory();
        } else if (section === 'settings') {
            loadSettings();
        }
    });
});

// Handle browser back/forward buttons
window.addEventListener('popstate', function(event) {
    if (event.state && event.state.section) {
        const section = event.state.section;
        document.querySelectorAll('.menu-item').forEach(m => m.classList.remove('active'));
        document.querySelector(`[data-section="${section}"]`)?.classList.add('active');
        
        document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
        document.getElementById(section)?.classList.add('active');
        
        const titles = {
            'overview': 'Tổng quan',
            'users': 'Quản lý người dùng',
            'premium-history': 'Lịch sử Premium',
            'tracking': 'Thống kê Tracking',
            'downloads': 'Lịch sử tải xuống',
            'settings': 'Cài đặt hệ thống'
        };
        document.getElementById('pageTitle').textContent = titles[section];
    }
});

// Load section from URL on page load
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const section = urlParams.get('section') || 'overview';
    
    if (section !== 'overview') {
        document.querySelectorAll('.menu-item').forEach(m => m.classList.remove('active'));
        document.querySelector(`[data-section="${section}"]`)?.classList.add('active');
        
        document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
        document.getElementById(section)?.classList.add('active');
        
        const titles = {
            'overview': 'Tổng quan',
            'users': 'Quản lý người dùng',
            'premium-history': 'Lịch sử Premium',
            'tracking': 'Thống kê Tracking',
            'downloads': 'Lịch sử tải xuống',
            'settings': 'Cài đặt hệ thống'
        };
        document.getElementById('pageTitle').textContent = titles[section];
        
        // Load data for section
        if (section === 'tracking') {
            loadTrackingData();
        } else if (section === 'users') {
            loadUsers();
        } else if (section === 'premium-history') {
            loadPremiumHistory();
        } else if (section === 'downloads') {
            loadDownloadsHistory();
        } else if (section === 'settings') {
            loadSettings();
        }
    }
});

// Logout function
function logout() {
    if (confirm('Bạn có chắc muốn đăng xuất?')) {
        fetch('/admin/logout', { method: 'POST' })
            .then(() => window.location.href = '/admin/login');
    }
}

// Load overview data
async function loadOverviewData() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        document.getElementById('totalDownloads').textContent = data.total_downloads.toLocaleString();
        
        // Load tracking stats for overview
        const trackResponse = await fetch('/api/stats/tracking');
        const trackData = await trackResponse.json();
        
        const totalUsers = trackData.devices.mobile + trackData.devices.pc + trackData.devices.tablet;
        document.getElementById('totalUsers').textContent = totalUsers.toLocaleString();
        document.getElementById('mobileUsers').textContent = trackData.devices.mobile.toLocaleString();
        document.getElementById('desktopUsers').textContent = trackData.devices.pc.toLocaleString();
        
    } catch (error) {
        console.error('Error loading overview:', error);
    }
}

// Load tracking data
async function loadTrackingData() {
    try {
        const response = await fetch('/api/stats/tracking');
        const data = await response.json();
        
        // Update device stats
        document.getElementById('trackMobile').textContent = data.devices.mobile.toLocaleString();
        document.getElementById('trackPC').textContent = data.devices.pc.toLocaleString();
        document.getElementById('trackTablet').textContent = data.devices.tablet.toLocaleString();
        
        // Update countries table
        const countriesTable = document.getElementById('countriesTable');
        countriesTable.innerHTML = data.top_countries.map(item => `
            <tr>
                <td><span style="font-size: 20px; margin-right: 8px;">${getFlag(item.code)}</span>${item.country}</td>
                <td>${item.code}</td>
                <td><strong>${item.count.toLocaleString()}</strong></td>
                <td style="color: #7f8c8d; font-size: 13px;">${new Date().toLocaleString('vi-VN')}</td>
            </tr>
        `).join('');
        
        // Update cities table
        const citiesTable = document.getElementById('citiesTable');
        citiesTable.innerHTML = data.top_cities.map(item => `
            <tr>
                <td>${item.city}</td>
                <td>${item.country}</td>
                <td><strong>${item.count.toLocaleString()}</strong></td>
            </tr>
        `).join('');
        
        // Update browsers table
        const browsersTable = document.getElementById('browsersTable');
        browsersTable.innerHTML = data.top_browsers.map(item => `
            <tr>
                <td>${item.browser}</td>
                <td><strong>${item.count.toLocaleString()}</strong></td>
            </tr>
        `).join('');
        
        // Update last update time
        document.getElementById('lastUpdate').textContent = new Date().toLocaleString('vi-VN');
        
    } catch (error) {
        console.error('Error loading tracking:', error);
    }
}

// Helper function to get platform color
function getPlatformColor(platform) {
    const colors = {
        'youtube': '#ff0000',
        'tiktok': '#000000',
        'instagram': '#e4405f',
        'facebook': '#1877f2'
    };
    return colors[platform?.toLowerCase()] || '#6c757d';
}

// Load downloads history
async function loadDownloadsHistory() {
    const limit = document.getElementById('limitSelect')?.value || 50;
    const container = document.getElementById('downloadsTable');
    container.innerHTML = '<div class="loading">Đang tải...</div>';
    
    try {
        const response = await fetch(`/api/admin/downloads/recent?limit=${limit}`);
        const data = await response.json();
        
        if (data.downloads && data.downloads.length > 0) {
            container.innerHTML = `
                <div style="margin-bottom: 15px; padding: 10px; background: #e8f5e8; border-radius: 6px; font-size: 14px;">
                    <i class="fas fa-info-circle" style="color: #28a745;"></i> 
                    Hiển thị ${data.downloads.length} lượt tải gần nhất | 
                    Cập nhật lúc: ${formatDateTime(data.timestamp)} |
                    <button onclick="loadDownloadsHistory()" style="margin-left: 10px; padding: 4px 8px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        <i class="fas fa-sync-alt"></i> Làm mới
                    </button>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Thời gian</th>
                            <th>Tài khoản</th>
                            <th>Platform</th>
                            <th>Format</th>
                            <th>Chất lượng</th>
                            <th>Thao tác</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.downloads.map(d => `
                            <tr>
                                <td style="white-space: nowrap; font-size: 12px;">${formatDateTime(d.download_time)}</td>
                                <td style="font-size: 12px;">
                                    <div style="display: flex; flex-direction: column; gap: 2px;">
                                        <span style="font-weight: 600; color: #2c3e50;">👤 ${d.username}</span>
                                        <span style="font-size: 10px; color: #7f8c8d;">${d.email || ''}</span>
                                    </div>
                                </td>
                                <td><span style="padding: 3px 6px; background: ${getPlatformColor(d.platform)}; color: white; border-radius: 3px; font-size: 10px; font-weight: bold;">${(d.platform || 'N/A').toUpperCase()}</span></td>
                                <td><span style="padding: 2px 6px; background: #6c757d; color: white; border-radius: 3px; font-size: 10px;">${d.format || 'N/A'}</span></td>
                                <td style="font-size: 12px;">${d.quality || 'N/A'}</td>
                                <td style="text-align: center;">
                                    <button onclick='showDownloadDetail(${JSON.stringify(d)})' style="padding: 6px 12px; background: #3498db; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.3s;">
                                        <i class="fas fa-eye"></i> Chi tiết
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } else {
            container.innerHTML = '<p style="text-align: center; padding: 40px; color: #7f8c8d;">Chưa có dữ liệu tải xuống</p>';
        }
        
    } catch (error) {
        console.error('Error loading downloads:', error);
        container.innerHTML = '<p style="text-align: center; padding: 40px; color: #e74c3c;">Lỗi tải dữ liệu: ' + error.message + '</p>';
    }
}

// Helper function to display country with flag
function getCountryDisplay(country) {
    if (!country || country === 'Unknown') return 'Unknown';
    
    // Common country mappings
    const countryFlags = {
        'Vietnam': '🇻🇳 Vietnam',
        'United States': '🇺🇸 United States', 
        'China': '🇨🇳 China',
        'Japan': '🇯🇵 Japan',
        'South Korea': '🇰🇷 South Korea',
        'Thailand': '🇹🇭 Thailand',
        'Singapore': '🇸🇬 Singapore',
        'Malaysia': '🇲🇾 Malaysia',
        'Philippines': '🇵🇭 Philippines',
        'Indonesia': '🇮🇩 Indonesia'
    };
    
    return countryFlags[country] || country;
}

// Helper functions
function getFlag(countryCode) {
    if (!countryCode || countryCode === 'XX') return '🏳️';
    const codePoints = countryCode
        .toUpperCase()
        .split('')
        .map(char => 127397 + char.charCodeAt());
    return String.fromCodePoint(...codePoints);
}

function getDeviceIcon(download) {
    if (download.is_mobile) return '📱';
    if (download.is_tablet) return '📲';
    if (download.is_pc) return '💻';
    return '❓';
}

function formatDateTime(dateStr) {
    if (!dateStr) return 'N/A';
    
    try {
        const date = new Date(dateStr);
        
        // Check if date is valid
        if (isNaN(date.getTime())) return 'Invalid Date';
        
        // Format with Vietnam timezone
        return date.toLocaleString('vi-VN', {
            timeZone: 'Asia/Ho_Chi_Minh',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    } catch (error) {
        console.error('Error formatting date:', error);
        return 'Error';
    }
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    
    try {
        const date = new Date(dateStr);
        
        // Check if date is valid
        if (isNaN(date.getTime())) return 'Invalid Date';
        
        return date.toLocaleDateString('vi-VN', {
            timeZone: 'Asia/Ho_Chi_Minh',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
    } catch (error) {
        console.error('Error formatting date:', error);
        return 'Error';
    }
}

// Show download detail modal
function showDownloadDetail(download) {
    const modal = document.getElementById('download-detail-modal');
    const content = document.getElementById('download-detail-content');
    
    content.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
                <h4 style="color: #2c3e50; margin-bottom: 15px; font-size: 16px; border-bottom: 2px solid #3498db; padding-bottom: 8px;">
                    <i class="fas fa-user"></i> Thông tin người dùng
                </h4>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <div>
                        <strong style="color: #7f8c8d; font-size: 12px;">Username:</strong>
                        <div style="color: #2c3e50; font-weight: 600;">${download.username || 'N/A'}</div>
                    </div>
                    <div>
                        <strong style="color: #7f8c8d; font-size: 12px;">Email:</strong>
                        <div style="color: #2c3e50;">${download.email || 'N/A'}</div>
                    </div>
                    <div>
                        <strong style="color: #7f8c8d; font-size: 12px;">User ID:</strong>
                        <div style="color: #2c3e50; font-family: monospace;">#${download.user_id || 'N/A'}</div>
                    </div>
                </div>
            </div>
            
            <div>
                <h4 style="color: #2c3e50; margin-bottom: 15px; font-size: 16px; border-bottom: 2px solid #e74c3c; padding-bottom: 8px;">
                    <i class="fas fa-download"></i> Thông tin tải xuống
                </h4>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <div>
                        <strong style="color: #7f8c8d; font-size: 12px;">Thời gian:</strong>
                        <div style="color: #2c3e50;">${formatDateTime(download.download_time)}</div>
                    </div>
                    <div>
                        <strong style="color: #7f8c8d; font-size: 12px;">Platform:</strong>
                        <div><span style="padding: 4px 8px; background: ${getPlatformColor(download.platform)}; color: white; border-radius: 4px; font-size: 11px; font-weight: bold;">${(download.platform || 'N/A').toUpperCase()}</span></div>
                    </div>
                    <div>
                        <strong style="color: #7f8c8d; font-size: 12px;">Format:</strong>
                        <div><span style="padding: 3px 8px; background: #6c757d; color: white; border-radius: 4px; font-size: 11px;">${download.format || 'N/A'}</span></div>
                    </div>
                    <div>
                        <strong style="color: #7f8c8d; font-size: 12px;">Chất lượng:</strong>
                        <div style="color: #2c3e50; font-weight: 600;">${download.quality || 'N/A'}</div>
                    </div>
                    <div>
                        <strong style="color: #7f8c8d; font-size: 12px;">Trạng thái:</strong>
                        <div>${download.success ? '<span style="color: #28a745; font-weight: 600;">✓ Thành công</span>' : '<span style="color: #dc3545; font-weight: 600;">✗ Thất bại</span>'}</div>
                    </div>
                </div>
            </div>
            
            <div>
                <h4 style="color: #2c3e50; margin-bottom: 15px; font-size: 16px; border-bottom: 2px solid #f39c12; padding-bottom: 8px;">
                    <i class="fas fa-map-marker-alt"></i> Vị trí
                </h4>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <div>
                        <strong style="color: #7f8c8d; font-size: 12px;">Quốc gia:</strong>
                        <div style="color: #2c3e50;">${getCountryDisplay(download.country)}</div>
                    </div>
                    <div>
                        <strong style="color: #7f8c8d; font-size: 12px;">Thành phố:</strong>
                        <div style="color: #2c3e50;">${download.city || 'Unknown'}</div>
                    </div>
                    <div>
                        <strong style="color: #7f8c8d; font-size: 12px;">IP Address:</strong>
                        <div style="color: #2c3e50; font-family: monospace; font-size: 13px;">${download.ip_address || 'N/A'}</div>
                    </div>
                </div>
            </div>
            
            <div>
                <h4 style="color: #2c3e50; margin-bottom: 15px; font-size: 16px; border-bottom: 2px solid #9b59b6; padding-bottom: 8px;">
                    <i class="fas fa-laptop"></i> Thiết bị
                </h4>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <div>
                        <strong style="color: #7f8c8d; font-size: 12px;">Loại thiết bị:</strong>
                        <div style="color: #2c3e50;">${getDeviceIcon(download)} ${download.device_type || 'Unknown'}</div>
                    </div>
                    <div>
                        <strong style="color: #7f8c8d; font-size: 12px;">Hệ điều hành:</strong>
                        <div style="color: #2c3e50;">${download.os || 'Unknown'}</div>
                    </div>
                    <div>
                        <strong style="color: #7f8c8d; font-size: 12px;">Trình duyệt:</strong>
                        <div style="color: #2c3e50;">${download.browser || 'Unknown'}</div>
                    </div>
                    <div>
                        <strong style="color: #7f8c8d; font-size: 12px;">Mobile:</strong>
                        <div style="color: #2c3e50;">${download.is_mobile ? '✓ Yes' : '✗ No'}</div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    modal.style.display = 'flex';
}

function closeDownloadDetailModal() {
    document.getElementById('download-detail-modal').style.display = 'none';
}

// Initialize
loadOverviewData();

// Auto refresh every 30 seconds
setInterval(() => {
    const activeSection = document.querySelector('.content-section.active').id;
    if (activeSection === 'overview') {
        loadOverviewData();
    } else if (activeSection === 'tracking') {
        loadTrackingData();
    } else if (activeSection === 'downloads') {
        loadDownloadsHistory(); // Add auto refresh for downloads
    }
}, 30000);


// Load settings page
async function loadSettings() {
    loadSystemInfo();
    loadEnvVars();
}

// Load system info
async function loadSystemInfo() {
    try {
        const response = await fetch('/api/debug/env');
        const data = await response.json();
        
        const systemInfo = document.getElementById('systemInfo');
        systemInfo.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                <div>
                    <strong>Python:</strong> ${data.python_version.split(' ')[0]}
                </div>
                <div>
                    <strong>yt-dlp:</strong> ${data.yt_dlp_version || 'N/A'}
                </div>
                <div>
                    <strong>FFmpeg:</strong> ${data.ffmpeg_installed ? '✓ Installed' : '✗ Not installed'}
                </div>
                <div>
                    <strong>Deno:</strong> ${data.deno_installed ? '✓ Installed' : '✗ Not installed'}
                </div>
                <div>
                    <strong>Node.js:</strong> ${data.node_installed ? '✓ Installed' : '✗ Not installed'}
                </div>
                <div>
                    <strong>bgutil Server:</strong> ${data.bgutil_server_running ? '✓ Running' : '✗ Not running'}
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading system info:', error);
        document.getElementById('systemInfo').innerHTML = '<p style="color: #e74c3c;">Lỗi tải thông tin hệ thống</p>';
    }
}

// Load environment variables
async function loadEnvVars() {
    try {
        const response = await fetch('/api/admin/env-vars');
        const data = await response.json();
        
        const envVars = document.getElementById('envVars');
        if (data.env_vars && data.env_vars.length > 0) {
            envVars.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                    ${data.env_vars.map(env => `
                        <div style="padding: 10px; background: #f8f9fa; border-radius: 6px; font-family: monospace; font-size: 13px;">
                            <i class="fas fa-check" style="color: #28a745;"></i> ${env}
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            envVars.innerHTML = '<p style="color: #7f8c8d;">Không có biến môi trường nào được cấu hình</p>';
        }
    } catch (error) {
        console.error('Error loading env vars:', error);
        document.getElementById('envVars').innerHTML = '<p style="color: #e74c3c;">Lỗi tải biến môi trường</p>';
    }
}

// Show database stats
async function showDatabaseStats() {
    const resultDiv = document.getElementById('dbStatsResult');
    resultDiv.innerHTML = '<p style="color: #17a2b8;">Đang tải...</p>';
    
    try {
        const response = await fetch('/api/admin/db-stats');
        const data = await response.json();
        
        resultDiv.innerHTML = `
            <div style="background: white; padding: 15px; border-radius: 6px; margin-top: 10px;">
                <h4 style="color: #2c3e50; margin-bottom: 10px;">Thống kê Database</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                    <div>
                        <strong>Tổng records:</strong> ${data.total_records?.toLocaleString() || 0}
                    </div>
                    <div>
                        <strong>Dung lượng:</strong> ${data.database_size || 'N/A'}
                    </div>
                    <div>
                        <strong>Record cũ nhất:</strong> ${data.oldest_record || 'N/A'}
                    </div>
                    <div>
                        <strong>Record mới nhất:</strong> ${data.newest_record || 'N/A'}
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading DB stats:', error);
        resultDiv.innerHTML = '<p style="color: #e74c3c;">Lỗi tải thống kê database</p>';
    }
}

// Export data
async function exportData() {
    if (!confirm('Bạn có muốn export toàn bộ dữ liệu tracking?')) return;
    
    try {
        const response = await fetch('/api/admin/export-data');
        const blob = await response.blob();
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `tracking_data_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        alert('Export thành công!');
    } catch (error) {
        console.error('Error exporting data:', error);
        alert('Lỗi export dữ liệu');
    }
}

// Clear old data
async function clearOldData() {
    const days = prompt('Xóa dữ liệu cũ hơn bao nhiêu ngày? (VD: 90)', '90');
    if (!days) return;
    
    if (!confirm(`Bạn có chắc muốn xóa dữ liệu cũ hơn ${days} ngày?`)) return;
    
    const resultDiv = document.getElementById('dbStatsResult');
    resultDiv.innerHTML = '<p style="color: #ffc107;">Đang xóa...</p>';
    
    try {
        const response = await fetch('/api/admin/clear-old-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ days: parseInt(days) })
        });
        const data = await response.json();
        
        if (data.success) {
            resultDiv.innerHTML = `<p style="color: #28a745;">✓ Đã xóa ${data.deleted_count} records</p>`;
        } else {
            resultDiv.innerHTML = `<p style="color: #e74c3c;">✗ ${data.error}</p>`;
        }
    } catch (error) {
        console.error('Error clearing old data:', error);
        resultDiv.innerHTML = '<p style="color: #e74c3c;">Lỗi xóa dữ liệu</p>';
    }
}

// Clear cache
async function clearCache(type) {
    if (!confirm(`Bạn có chắc muốn xóa ${type} cache?`)) return;
    
    const resultDiv = document.getElementById('cacheResult');
    resultDiv.innerHTML = '<p style="color: #6c757d;">Đang xóa...</p>';
    
    try {
        const response = await fetch('/api/admin/clear-cache', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type })
        });
        const data = await response.json();
        
        if (data.success) {
            resultDiv.innerHTML = `<p style="color: #28a745;">✓ ${data.message}</p>`;
        } else {
            resultDiv.innerHTML = `<p style="color: #e74c3c;">✗ ${data.error}</p>`;
        }
    } catch (error) {
        console.error('Error clearing cache:', error);
        resultDiv.innerHTML = '<p style="color: #e74c3c;">Lỗi xóa cache</p>';
    }
}

// Change password form handler
document.getElementById('changePasswordForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const resultDiv = document.getElementById('passwordChangeResult');
    
    if (newPassword !== confirmPassword) {
        resultDiv.innerHTML = '<p style="color: #e74c3c;">✗ Mật khẩu xác nhận không khớp</p>';
        return;
    }
    
    if (newPassword.length < 6) {
        resultDiv.innerHTML = '<p style="color: #e74c3c;">✗ Mật khẩu phải có ít nhất 6 ký tự</p>';
        return;
    }
    
    resultDiv.innerHTML = '<p style="color: #3498db;">Đang xử lý...</p>';
    
    try {
        const response = await fetch('/api/admin/change-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
        });
        const data = await response.json();
        
        if (data.success) {
            resultDiv.innerHTML = '<p style="color: #28a745;">✓ Đổi mật khẩu thành công! Vui lòng đăng nhập lại.</p>';
            setTimeout(() => {
                logout();
            }, 2000);
        } else {
            resultDiv.innerHTML = `<p style="color: #e74c3c;">✗ ${data.error}</p>`;
        }
    } catch (error) {
        console.error('Error changing password:', error);
        resultDiv.innerHTML = '<p style="color: #e74c3c;">Lỗi đổi mật khẩu</p>';
    }
});
