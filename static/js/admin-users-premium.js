// Admin Users and Premium Management JavaScript

// Update menu titles
const menuTitles = {
    'overview': 'Tổng quan',
    'users': 'Quản lý người dùng',
    'premium': 'Quản lý Premium',
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
        } else if (section === 'premium') {
            loadPremiumSubscriptions();
        }
    });
});

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
                        <th>Loại</th>
                        <th>Premium</th>
                        <th>Ngày tạo</th>
                        <th>Thao tác</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.users.map(user => `
                        <tr>
                            <td>${user.id}</td>
                            <td>
                                <strong>${user.username}</strong>
                                ${user.has_google ? '<span style="color: #4285f4; margin-left: 5px;" title="Đăng nhập Google">🔗</span>' : ''}
                            </td>
                            <td>${user.email}</td>
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
                    `).join('')}
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

// ==================== PREMIUM MANAGEMENT ====================

async function loadPremiumSubscriptions() {
    const statusFilter = document.getElementById('premiumStatusFilter').value;
    
    const premiumTable = document.getElementById('premiumTable');
    premiumTable.innerHTML = '<div class="loading">Đang tải...</div>';
    
    try {
        const response = await fetch(`/api/admin/premium?status=${statusFilter}`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Không thể tải dữ liệu');
        }
        
        // Update stats
        document.getElementById('premiumActive').textContent = data.stats.active.toLocaleString();
        document.getElementById('premiumRevenue').textContent = data.stats.revenue.toLocaleString() + ' VNĐ';
        document.getElementById('premiumExpiring').textContent = data.stats.expiring.toLocaleString();
        document.getElementById('premiumExpired').textContent = data.stats.expired.toLocaleString();
        
        // Build table
        if (data.subscriptions.length === 0) {
            premiumTable.innerHTML = '<p style="text-align: center; padding: 40px; color: #7f8c8d;">Không có gói Premium nào</p>';
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
                        <th>Bắt đầu</th>
                        <th>Hết hạn</th>
                        <th>Trạng thái</th>
                        <th>Thao tác</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.subscriptions.map(sub => {
                        const isActive = sub.status === 'active';
                        const daysLeft = isActive ? Math.ceil((new Date(sub.expires_at) - new Date()) / (1000 * 60 * 60 * 24)) : 0;
                        const isExpiring = daysLeft > 0 && daysLeft <= 7;
                        
                        return `
                        <tr>
                            <td>${sub.id}</td>
                            <td><strong>${sub.username}</strong></td>
                            <td style="font-size: 13px; color: #64748b;">${sub.email}</td>
                            <td style="font-size: 12px; font-family: monospace;">${sub.order_code || '-'}</td>
                            <td><strong>${sub.amount.toLocaleString()} VNĐ</strong></td>
                            <td style="font-size: 13px; color: #64748b;">${new Date(sub.starts_at).toLocaleDateString('vi-VN')}</td>
                            <td style="font-size: 13px; color: #64748b;">${new Date(sub.expires_at).toLocaleDateString('vi-VN')}</td>
                            <td>
                                ${isActive ? 
                                    (isExpiring ? 
                                        `<span style="background: #fef3c7; color: #92400e; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">⚠️ Còn ${daysLeft} ngày</span>` :
                                        `<span style="background: #d1fae5; color: #065f46; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">✓ Hoạt động</span>`
                                    ) :
                                    '<span style="background: #fee2e2; color: #991b1b; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">✗ Hết hạn</span>'
                                }
                            </td>
                            <td>
                                <button onclick="extendPremium(${sub.id}, '${sub.username}')" 
                                    style="padding: 6px 12px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; margin-right: 5px; font-size: 12px;">
                                    <i class="fas fa-plus"></i> Gia hạn
                                </button>
                                <button onclick="deletePremium(${sub.id}, '${sub.username}')" 
                                    style="padding: 6px 12px; background: #ef4444; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 12px;">
                                    <i class="fas fa-trash"></i> Xóa
                                </button>
                            </td>
                        </tr>
                    `}).join('')}
                </tbody>
            </table>
        `;
        
        premiumTable.innerHTML = tableHTML;
        
    } catch (error) {
        console.error('Error loading premium:', error);
        premiumTable.innerHTML = `<p style="text-align: center; padding: 40px; color: #ef4444;">Lỗi: ${error.message}</p>`;
    }
}

// Extend premium subscription
async function extendPremium(subscriptionId, username) {
    const days = prompt(`Gia hạn thêm bao nhiêu ngày cho ${username}?`, '30');
    if (!days || isNaN(days) || days <= 0) return;
    
    try {
        const response = await fetch(`/api/admin/premium/${subscriptionId}/extend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ days: parseInt(days) })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message);
            loadPremiumSubscriptions();
        } else {
            alert('Lỗi: ' + (data.error || 'Không thể gia hạn'));
        }
    } catch (error) {
        alert('Lỗi: ' + error.message);
    }
}

// Delete premium subscription
async function deletePremium(subscriptionId, username) {
    if (!confirm(`Bạn có chắc muốn xóa gói Premium của "${username}"?\n\nThao tác này không thể hoàn tác!`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/premium/${subscriptionId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message);
            loadPremiumSubscriptions();
        } else {
            alert('Lỗi: ' + (data.error || 'Không thể xóa'));
        }
    } catch (error) {
        alert('Lỗi: ' + error.message);
    }
}

// Show add premium modal (placeholder)
function showAddPremiumModal() {
    alert('Tính năng này sẽ được thêm sau. Hiện tại bạn có thể thêm Premium cho người dùng từ trang "Người dùng".');
}
