// Admin Users and Premium Management JavaScript

// Update menu titles
const menuTitles = {
    'overview': 'Tổng quan',
    'users': 'Quản lý người dùng',
    'premium-history': 'Lịch sử thanh toán Premium',
    'tracking': 'Thống kê Tracking',
    'donations': 'Quản lý Ủng hộ',
    'downloads': 'Lịch sử tải xuống',
    'analytics': 'Phân tích chi tiết',
    'settings': 'Cài đặt hệ thống'
};

// Override menu click handler to include new sections
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
        document.getElementById('pageTitle').textContent = menuTitles[section] || section;
        
        // Load data for section
        if (section === 'users') {
            loadUsers();
        } else if (section === 'premium-history') {
            loadPremiumHistory();
        }
    });
});

// Track online users via Socket.IO
let onlineUserIds = new Set();

if (typeof io !== 'undefined') {
    const socket = io();
    
    socket.on('user_status', function(data) {
        if (data.user_id) {
            if (data.status === 'online') {
                onlineUserIds.add(data.user_id);
            } else {
                onlineUserIds.delete(data.user_id);
            }
            // Update online count in stats
            document.getElementById('usersOnline').textContent = onlineUserIds.size;
        }
    });
}

// ==================== USERS MANAGEMENT ====================

async function loadUsers() {
    const userType = document.getElementById('userTypeFilter').value;
    const search = document.getElementById('userSearchInput').value;
    
    const usersTable = document.getElementById('usersTable');
    usersTable.innerHTML = '<div class="loading">Đang tải...</div>';
    
    try {
        const response = await fetch(`/api/admin/users?type=${userType}&search=${encodeURIComponent(search)}`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Không thể tải dữ liệu');
        }
        
        // Update stats
        document.getElementById('usersTotal').textContent = data.stats.total.toLocaleString();
        document.getElementById('usersOnline').textContent = data.stats.online.toLocaleString();
        document.getElementById('usersPremium').textContent = data.stats.premium.toLocaleString();
        document.getElementById('usersToday').textContent = data.stats.today.toLocaleString();
        
        // Build table
        if (data.users.length === 0) {
            usersTable.innerHTML = '<p style="text-align: center; padding: 40px; color: #7f8c8d;">Không có người dùng nào</p>';
            return;
        }
        
        const tableHTML = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Email</th>
                        <th>Online</th>
                        <th>Loại</th>
                        <th>Premium</th>
                        <th>Ngày tạo</th>
                        <th>Thao tác</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.users.map(user => {
                        const isOnline = onlineUserIds.has(user.id);
                        return `
                        <tr>
                            <td>${user.id}</td>
                            <td>
                                <strong>${user.username}</strong>
                                ${user.has_google ? '<span style="color: #4285f4; margin-left: 5px;" title="Đăng nhập Google">🔗</span>' : ''}
                            </td>
                            <td>${user.email}</td>
                            <td>
                                ${isOnline ? 
                                    '<span style="background: #d1fae5; color: #065f46; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">🟢 Online</span>' : 
                                    '<span style="background: #f1f5f9; color: #64748b; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">⚫ Offline</span>'
                                }
                            </td>
                            <td>
                                ${user.is_premium ? 
                                    '<span style="background: linear-gradient(135deg, #fef3c7, #fed7aa); color: #92400e; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">👑 Premium</span>' : 
                                    '<span style="background: #f1f5f9; color: #475569; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">Miễn phí</span>'
                                }
                            </td>
                            <td>
                                ${user.is_premium && user.premium_expires ? 
                                    `<span style="color: #10b981; font-size: 13px;">Đến ${new Date(user.premium_expires).toLocaleDateString('vi-VN')}</span>` : 
                                    '<span style="color: #94a3b8;">-</span>'
                                }
                            </td>
                            <td style="color: #64748b; font-size: 13px;">${new Date(user.created_at).toLocaleDateString('vi-VN')}</td>
                            <td>
                                <button onclick="addPremiumToUser(${user.id}, '${user.username}')" 
                                    style="padding: 6px 12px; background: #f59e0b; color: white; border: none; border-radius: 6px; cursor: pointer; margin-right: 5px; font-size: 12px;">
                                    <i class="fas fa-crown"></i> Premium
                                </button>
                                <button onclick="deleteUser(${user.id}, '${user.username}')" 
                                    style="padding: 6px 12px; background: #ef4444; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 12px;">
                                    <i class="fas fa-trash"></i> Xóa
                                </button>
                            </td>
                        </tr>
                    `}).join('')}
                </tbody>
            </table>
        `;
        
        usersTable.innerHTML = tableHTML;
        
    } catch (error) {
        console.error('Error loading users:', error);
        usersTable.innerHTML = `<p style="text-align: center; padding: 40px; color: #ef4444;">Lỗi: ${error.message}</p>`;
    }
}

// Add premium to user
async function addPremiumToUser(userId, username) {
    const days = prompt(`Thêm bao nhiêu ngày Premium cho ${username}?`, '30');
    if (!days || isNaN(days) || days <= 0) return;
    
    try {
        const response = await fetch(`/api/admin/users/${userId}/add-premium`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ days: parseInt(days) })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message);
            loadUsers();
        } else {
            alert('Lỗi: ' + (data.error || 'Không thể thêm Premium'));
        }
    } catch (error) {
        alert('Lỗi: ' + error.message);
    }
}

// Delete user
async function deleteUser(userId, username) {
    if (!confirm(`Bạn có chắc muốn xóa người dùng "${username}"?\n\nThao tác này không thể hoàn tác!`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/users/${userId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message);
            loadUsers();
        } else {
            alert('Lỗi: ' + (data.error || 'Không thể xóa người dùng'));
        }
    } catch (error) {
        alert('Lỗi: ' + error.message);
    }
}

// Search users on Enter key
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('userSearchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                loadUsers();
            }
        });
    }
});

// ==================== PREMIUM HISTORY ====================

async function loadPremiumHistory() {
    const statusFilter = document.getElementById('premiumHistoryStatusFilter').value;
    const search = document.getElementById('premiumHistorySearch').value;
    
    const premiumHistoryTable = document.getElementById('premiumHistoryTable');
    premiumHistoryTable.innerHTML = '<div class="loading">Đang tải...</div>';
    
    try {
        const response = await fetch(`/api/admin/premium-history?status=${statusFilter}&search=${encodeURIComponent(search)}`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Không thể tải dữ liệu');
        }
        
        // Update stats
        document.getElementById('premiumHistorySuccess').textContent = data.stats.success.toLocaleString();
        document.getElementById('premiumHistoryRevenue').textContent = data.stats.revenue.toLocaleString() + ' VNĐ';
        document.getElementById('premiumHistoryUsers').textContent = data.stats.premium_users.toLocaleString();
        document.getElementById('premiumHistoryToday').textContent = data.stats.today.toLocaleString();
        
        // Build table
        if (data.payments.length === 0) {
            premiumHistoryTable.innerHTML = '<p style="text-align: center; padding: 40px; color: #7f8c8d;">Không có giao dịch nào</p>';
            return;
        }
        
        const tableHTML = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Người dùng</th>
                        <th>Email</th>
                        <th>Mã đơn</th>
                        <th>Số tiền</th>
                        <th>Trạng thái</th>
                        <th>Ngày tạo</th>
                        <th>Ngày cập nhật</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.payments.map(payment => {
                        let statusBadge = '';
                        if (payment.status === 'PAID') {
                            statusBadge = '<span style="background: #d1fae5; color: #065f46; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">✓ Thành công</span>';
                        } else if (payment.status === 'PENDING') {
                            statusBadge = '<span style="background: #fef3c7; color: #92400e; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">⏳ Đang chờ</span>';
                        } else if (payment.status === 'CANCELLED') {
                            statusBadge = '<span style="background: #fee2e2; color: #991b1b; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">✗ Đã hủy</span>';
                        } else {
                            statusBadge = `<span style="background: #f1f5f9; color: #64748b; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">${payment.status}</span>`;
                        }
                        
                        return `
                        <tr>
                            <td>${payment.id}</td>
                            <td><strong>${payment.username || '-'}</strong></td>
                            <td style="font-size: 13px; color: #64748b;">${payment.email || '-'}</td>
                            <td style="font-size: 12px; font-family: monospace;">${payment.order_code}</td>
                            <td><strong>${payment.amount.toLocaleString()} VNĐ</strong></td>
                            <td>${statusBadge}</td>
                            <td style="font-size: 13px; color: #64748b;">${new Date(payment.created_at).toLocaleString('vi-VN')}</td>
                            <td style="font-size: 13px; color: #64748b;">${payment.updated_at ? new Date(payment.updated_at).toLocaleString('vi-VN') : '-'}</td>
                        </tr>
                    `}).join('')}
                </tbody>
            </table>
        `;
        
        premiumHistoryTable.innerHTML = tableHTML;
        
    } catch (error) {
        console.error('Error loading premium history:', error);
        premiumHistoryTable.innerHTML = `<p style="text-align: center; padding: 40px; color: #ef4444;">Lỗi: ${error.message}</p>`;
    }
}

// Search premium history on Enter key
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('premiumHistorySearch');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                loadPremiumHistory();
            }
        });
    }
});
