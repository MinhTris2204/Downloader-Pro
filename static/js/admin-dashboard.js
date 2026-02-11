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
            'downloads': 'Lịch sử tải xuống',
            'analytics': 'Phân tích chi tiết',
            'settings': 'Cài đặt hệ thống'
        };
        document.getElementById('pageTitle').textContent = titles[section];
        
        // Load data for section
        if (section === 'tracking') {
            loadTrackingData();
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
        
    } catch (error) {
        console.error('Error loading tracking:', error);
    }
}

// Get country flag emoji
function getFlag(countryCode) {
    if (!countryCode || countryCode === 'XX') return '🏳️';
    const codePoints = countryCode
        .toUpperCase()
        .split('')
        .map(char => 127397 + char.charCodeAt());
    return String.fromCodePoint(...codePoints);
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
    }
}, 30000);
