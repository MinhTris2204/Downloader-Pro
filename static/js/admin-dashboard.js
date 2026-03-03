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
            'tracking': 'Thống kê Tracking',
            'donations': 'Quản lý Ủng hộ',
            'downloads': 'Lịch sử tải xuống',
            'analytics': 'Phân tích chi tiết',
            'settings': 'Cài đặt hệ thống'
        };
        document.getElementById('pageTitle').textContent = titles[section];
        
        // Load data for section
        if (section === 'tracking') {
            loadTrackingData();
        } else if (section === 'donations') {
            loadDonations();
        } else if (section === 'downloads') {
            loadDownloadsHistory();
        } else if (section === 'analytics') {
            loadAnalytics();
        } else if (section === 'settings') {
            loadSettings();
        }
    });
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

// Load donations
async function loadDonations() {
    const statusFilter = document.getElementById('donationStatusFilter')?.value || 'all';
    const limit = document.getElementById('donationLimitSelect')?.value || 20;
    const container = document.getElementById('donationsTable');
    
    if (container) {
        container.innerHTML = '<div class="loading">Đang tải...</div>';
    }
    
    try {
        const response = await fetch(`/api/admin/donations?status=${statusFilter}&limit=${limit}&page=1`);
        const data = await response.json();
        
        if (!data.success) {
            if (container) {
                container.innerHTML = '<p style="text-align: center; padding: 40px; color: #e74c3c;">Lỗi tải dữ liệu</p>';
            }
            return;
        }
        
        // Update stats
        const stats = calculateDonationStats(data.donations);
        document.getElementById('donationSuccessCount').textContent = stats.successCount.toLocaleString();
        document.getElementById('donationTotalAmount').textContent = stats.totalAmount.toLocaleString() + 'đ';
        document.getElementById('donationPendingCount').textContent = stats.pendingCount.toLocaleString();
        document.getElementById('donationFailedCount').textContent = stats.failedCount.toLocaleString();
        
        // Display table
        if (data.donations && data.donations.length > 0) {
            container.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>Mã đơn</th>
                            <th>Số tiền</th>
                            <th>Người ủng hộ</th>
                            <th>Email</th>
                            <th>Trạng thái</th>
                            <th>Phương thức</th>
                            <th>Mã GD</th>
                            <th>Thời gian tạo</th>
                            <th>Thời gian thanh toán</th>
                            <th>IP</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.donations.map(d => `
                            <tr>
                                <td style="font-family: monospace; font-weight: bold;">${d.order_code}</td>
                                <td style="color: #e74c3c; font-weight: bold;">${d.amount.toLocaleString()}đ</td>
                                <td>${d.donor_name || 'Anonymous'}</td>
                                <td style="font-size: 12px;">${d.donor_email || '-'}</td>
                                <td>${getStatusBadge(d.payment_status)}</td>
                                <td style="font-size: 12px;">${d.payment_method || '-'}</td>
                                <td style="font-family: monospace; font-size: 11px;">${d.transaction_id || '-'}</td>
                                <td style="white-space: nowrap; font-size: 12px;">${formatDateTime(d.created_at)}</td>
                                <td style="white-space: nowrap; font-size: 12px;">${d.paid_at ? formatDateTime(d.paid_at) : '-'}</td>
                                <td style="font-family: monospace; font-size: 11px;">${d.ip_address || '-'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                <p style="margin-top: 15px; color: #7f8c8d; font-size: 13px;">
                    <i class="fas fa-info-circle"></i> Hiển thị ${data.donations.length} / ${data.total} donations
                </p>
            `;
        } else {
            container.innerHTML = '<p style="text-align: center; padding: 40px; color: #7f8c8d;">Chưa có dữ liệu</p>';
        }
        
    } catch (error) {
        console.error('Error loading donations:', error);
        if (container) {
            container.innerHTML = '<p style="text-align: center; padding: 40px; color: #e74c3c;">Lỗi tải dữ liệu</p>';
        }
    }
}

// Calculate donation statistics
function calculateDonationStats(donations) {
    let successCount = 0;
    let totalAmount = 0;
    let pendingCount = 0;
    let failedCount = 0;
    
    donations.forEach(d => {
        if (d.payment_status === 'success') {
            successCount++;
            totalAmount += d.amount;
        } else if (d.payment_status === 'pending') {
            pendingCount++;
        } else if (d.payment_status === 'failed' || d.payment_status === 'cancelled') {
            failedCount++;
        }
    });
    
    return { successCount, totalAmount, pendingCount, failedCount };
}

// Get status badge HTML
function getStatusBadge(status) {
    const badges = {
        'success': '<span style="padding: 4px 10px; background: #4caf50; color: white; border-radius: 4px; font-size: 11px; font-weight: 600;">✓ Thành công</span>',
        'pending': '<span style="padding: 4px 10px; background: #ff9800; color: white; border-radius: 4px; font-size: 11px; font-weight: 600;">⏳ Đang chờ</span>',
        'failed': '<span style="padding: 4px 10px; background: #f44336; color: white; border-radius: 4px; font-size: 11px; font-weight: 600;">✗ Thất bại</span>',
        'cancelled': '<span style="padding: 4px 10px; background: #9e9e9e; color: white; border-radius: 4px; font-size: 11px; font-weight: 600;">⊘ Đã hủy</span>'
    };
    return badges[status] || status;
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
                            <th>Platform</th>
                            <th>Format</th>
                            <th>Chất lượng</th>
                            <th>Quốc gia</th>
                            <th>Thành phố</th>
                            <th>Thiết bị</th>
                            <th>OS</th>
                            <th>Trình duyệt</th>
                            <th>IP</th>
                            <th>Trạng thái</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.downloads.map(d => `
                            <tr>
                                <td style="white-space: nowrap; font-size: 12px;">${formatDateTime(d.download_time)}</td>
                                <td><span style="padding: 3px 6px; background: ${getPlatformColor(d.platform)}; color: white; border-radius: 3px; font-size: 10px; font-weight: bold;">${(d.platform || 'N/A').toUpperCase()}</span></td>
                                <td><span style="padding: 2px 6px; background: #6c757d; color: white; border-radius: 3px; font-size: 10px;">${d.format || 'N/A'}</span></td>
                                <td style="font-size: 12px;">${d.quality || 'N/A'}</td>
                                <td style="font-size: 12px;">${getCountryDisplay(d.country)}</td>
                                <td style="font-size: 12px;">${d.city || 'Unknown'}</td>
                                <td style="font-size: 12px;">${getDeviceIcon(d)} ${d.device_type || 'Unknown'}</td>
                                <td style="font-size: 11px;">${d.os || 'Unknown'}</td>
                                <td style="font-size: 11px;">${d.browser || 'Unknown'}</td>
                                <td style="font-family: monospace; font-size: 11px; color: #6c757d;">${d.ip_address || 'N/A'}</td>
                                <td style="text-align: center;">${d.success ? '<span style="color: #28a745; font-size: 16px;">✓</span>' : '<span style="color: #dc3545; font-size: 16px;">✗</span>'}</td>
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

// Load analytics
async function loadAnalytics() {
    document.getElementById('analyticsLoading').style.display = 'block';
    
    try {
        const response = await fetch('/api/admin/analytics/daily');
        const data = await response.json();
        
        // Platform distribution
        const platformsTable = document.getElementById('platformsTable');
        const totalPlatform = data.platforms.reduce((sum, p) => sum + p.count, 0);
        platformsTable.innerHTML = data.platforms.map(p => `
            <tr>
                <td><strong>${p.platform}</strong></td>
                <td>${p.count.toLocaleString()}</td>
                <td>${((p.count / totalPlatform) * 100).toFixed(1)}%</td>
            </tr>
        `).join('');
        
        // Format distribution
        const formatsTable = document.getElementById('formatsTable');
        const totalFormat = data.formats.reduce((sum, f) => sum + f.count, 0);
        formatsTable.innerHTML = data.formats.map(f => `
            <tr>
                <td><strong>${f.format}</strong></td>
                <td>${f.count.toLocaleString()}</td>
                <td>${((f.count / totalFormat) * 100).toFixed(1)}%</td>
            </tr>
        `).join('');
        
        // Simple daily chart (text-based)
        const dailyChart = document.getElementById('dailyChart');
        dailyChart.innerHTML = `
            <table style="width: 100%;">
                <thead>
                    <tr>
                        <th>Ngày</th>
                        <th>Tổng</th>
                        <th>YouTube</th>
                        <th>TikTok</th>
                        <th>Mobile</th>
                        <th>Desktop</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.daily_stats.map(d => `
                        <tr>
                            <td>${formatDate(d.date)}</td>
                            <td><strong>${d.total}</strong></td>
                            <td>${d.youtube}</td>
                            <td>${d.tiktok}</td>
                            <td>${d.mobile}</td>
                            <td>${d.desktop}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        document.getElementById('analyticsLoading').style.display = 'none';
        
    } catch (error) {
        console.error('Error loading analytics:', error);
        document.getElementById('analyticsLoading').style.display = 'none';
    }
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
    const date = new Date(dateStr);
    return date.toLocaleDateString('vi-VN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
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
