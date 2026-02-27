// Download Limit & Premium Modal Handler

let userStatus = {
    can_download: true,
    remaining_downloads: 2,
    is_premium: false,
    premium_expires: null
};

// Fetch user status on page load
async function fetchUserStatus() {
    try {
        const response = await fetch('/api/user/status');
        const data = await response.json();
        userStatus = data;
        updateDownloadStatusUI();
    } catch (err) {
        console.error('Failed to fetch user status:', err);
    }
}

// Update UI to show download status
function updateDownloadStatusUI() {
    const statusEl = document.getElementById('download-status');
    if (!statusEl) return;
    
    const lang = getCurrentLanguage();
    const t = translations[lang];
    
    if (userStatus.is_premium) {
        const expiresDate = new Date(userStatus.premium_expires);
        const daysLeft = Math.ceil((expiresDate - new Date()) / (1000 * 60 * 60 * 24));
        statusEl.innerHTML = `✨ ${t.premium_status} ${expiresDate.toLocaleDateString()} (${daysLeft} ngày)`;
        statusEl.className = 'download-status premium';
    } else if (userStatus.remaining_downloads >= 0) {
        statusEl.innerHTML = t.downloads_remaining.replace('{count}', userStatus.remaining_downloads);
        statusEl.className = 'download-status free';
    }
}

// Show limit exceeded modal
function showLimitModal() {
    const lang = getCurrentLanguage();
    const t = translations[lang];
    
    // Create modal HTML
    const modalHTML = `
        <div class="limit-modal-overlay" id="limitModalOverlay">
            <div class="limit-modal">
                <div class="limit-modal-header">
                    <h2>${t.limit_title}</h2>
                </div>
                <div class="limit-modal-body">
                    <p class="limit-message">${t.limit_message}</p>
                    <p class="limit-explanation">${t.limit_explanation}</p>
                    
                    <div class="premium-section">
                        <h3>${t.limit_premium_title}</h3>
                        <pre class="premium-benefits">${t.limit_premium_benefits}</pre>
                    </div>
                    
                    <div class="payment-form">
                        <label>${t.limit_amount_label}</label>
                        <div class="amount-options">
                            <button class="amount-btn" data-amount="10000">10,000₫</button>
                            <button class="amount-btn" data-amount="20000">20,000₫</button>
                            <button class="amount-btn" data-amount="50000">50,000₫</button>
                            <button class="amount-btn" data-amount="100000">100,000₫</button>
                        </div>
                        <input type="number" id="customAmount" class="custom-amount-input" 
                               placeholder="${t.limit_amount_custom}" min="10000" step="1000">
                        
                        <label>${t.limit_name_label}</label>
                        <input type="text" id="donorName" class="donor-name-input" 
                               placeholder="${t.limit_name_label}" maxlength="100">
                    </div>
                </div>
                <div class="limit-modal-footer">
                    <button class="btn-cancel" id="limitCancelBtn">${t.limit_button_cancel}</button>
                    <button class="btn-pay" id="limitPayBtn">${t.limit_button_pay}</button>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existing = document.getElementById('limitModalOverlay');
    if (existing) existing.remove();
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Add event listeners
    let selectedAmount = 20000; // Default
    
    document.querySelectorAll('.amount-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.amount-btn').forEach(b => b.classList.remove('selected'));
            this.classList.add('selected');
            selectedAmount = parseInt(this.dataset.amount);
            document.getElementById('customAmount').value = '';
        });
    });
    
    // Select default amount
    document.querySelector('.amount-btn[data-amount="20000"]').classList.add('selected');
    
    document.getElementById('customAmount').addEventListener('input', function() {
        document.querySelectorAll('.amount-btn').forEach(b => b.classList.remove('selected'));
        selectedAmount = parseInt(this.value) || 10000;
    });
    
    document.getElementById('limitCancelBtn').addEventListener('click', closeLimitModal);
    document.getElementById('limitModalOverlay').addEventListener('click', function(e) {
        if (e.target === this) closeLimitModal();
    });
    
    document.getElementById('limitPayBtn').addEventListener('click', async function() {
        const amount = selectedAmount;
        const name = document.getElementById('donorName').value.trim() || 'Anonymous';
        
        if (amount < 10000) {
            showToast('Số tiền tối thiểu là 10,000₫', 'error');
            return;
        }
        
        // Disable button
        this.disabled = true;
        this.innerHTML = '<span class="spinner"></span> Đang xử lý...';
        
        try {
            // Get user identifier from cookie/session
            const response = await fetch('/api/user/status');
            const userData = await response.json();
            
            // Create payment
            const paymentResponse = await fetch('/api/donate/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    amount: amount,
                    name: name,
                    email: '',
                    message: '',
                    is_premium: true,
                    user_id: 'auto' // Server will get from request
                })
            });
            
            const paymentData = await paymentResponse.json();
            
            if (paymentData.success && paymentData.checkoutUrl) {
                // Redirect to payment page
                window.location.href = paymentData.checkoutUrl;
            } else {
                showToast(paymentData.error || 'Lỗi tạo thanh toán', 'error');
                this.disabled = false;
                this.innerHTML = t.limit_button_pay;
            }
        } catch (err) {
            showToast('Lỗi kết nối server', 'error');
            this.disabled = false;
            this.innerHTML = t.limit_button_pay;
        }
    });
}

function closeLimitModal() {
    const modal = document.getElementById('limitModalOverlay');
    if (modal) modal.remove();
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    fetchUserStatus();
    
    // Refresh status every 30 seconds
    setInterval(fetchUserStatus, 30000);
});

// Export for use in app.js
window.showLimitModal = showLimitModal;
window.fetchUserStatus = fetchUserStatus;
