// Donation Promotion Modal (Always Show on Download)

// Get current language (fallback function)
function getCurrentLanguage() {
    return localStorage.getItem('language') || 'vi';
}

// Show donation promotion modal (non-blocking)
function showDonationPromo() {
    const lang = getCurrentLanguage();
    const t = translations[lang];
    
    // Create modal HTML
    const modalHTML = `
        <div class="donation-promo-overlay" id="donationPromoOverlay">
            <div class="donation-promo-modal">
                <div class="donation-promo-header">
                    <h2>💚 ${t.promo_title}</h2>
                    <button class="close-btn" id="promoCloseBtn">×</button>
                </div>
                <div class="donation-promo-body">
                    <div class="promo-icon">☕</div>
                    <p class="promo-message">${t.promo_message}</p>
                    <p class="promo-explanation">${t.promo_explanation}</p>
                    
                    <div class="promo-benefits">
                        <h4>${t.promo_benefits_title}</h4>
                        <ul>
                            <li>💰 ${t.promo_benefit_1}</li>
                            <li>🚀 ${t.promo_benefit_2}</li>
                            <li>❤️ ${t.promo_benefit_3}</li>
                        </ul>
                    </div>
                    
                    <div class="promo-amounts">
                        <button class="amount-btn-promo" data-amount="10000">10,000₫</button>
                        <button class="amount-btn-promo" data-amount="20000">20,000₫</button>
                        <button class="amount-btn-promo" data-amount="50000">50,000₫</button>
                        <button class="amount-btn-promo" data-amount="100000">100,000₫</button>
                    </div>
                    
                    <div class="custom-amount-section">
                        <label for="customAmountInput" class="custom-amount-label">${t.promo_custom_amount || 'Hoặc nhập số tiền khác:'}</label>
                        <input type="number" id="customAmountInput" class="custom-amount-input" 
                               placeholder="${t.promo_amount_placeholder || 'Nhập số tiền (VND)'}" 
                               min="5000" step="1000">
                    </div>
                </div>
                <div class="donation-promo-footer">
                    <button class="btn-skip" id="promoSkipBtn">${t.promo_skip}</button>
                    <button class="btn-donate-promo" id="promoDonateBtn">${t.promo_donate}</button>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existing = document.getElementById('donationPromoOverlay');
    if (existing) existing.remove();
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Add event listeners
    let selectedAmount = 20000; // Default
    
    // Handle preset amount buttons
    document.querySelectorAll('.amount-btn-promo').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.amount-btn-promo').forEach(b => b.classList.remove('selected'));
            this.classList.add('selected');
            selectedAmount = parseInt(this.dataset.amount);
            document.getElementById('customAmountInput').value = ''; // Clear custom input
        });
    });
    
    // Handle custom amount input
    document.getElementById('customAmountInput').addEventListener('input', function() {
        document.querySelectorAll('.amount-btn-promo').forEach(b => b.classList.remove('selected'));
        const customValue = parseInt(this.value);
        if (customValue >= 5000) {
            selectedAmount = customValue;
        }
    });
    
    // Select default amount
    document.querySelector('.amount-btn-promo[data-amount="20000"]').classList.add('selected');
    
    // Close handlers
    document.getElementById('promoCloseBtn').addEventListener('click', closeDonationPromo);
    document.getElementById('promoSkipBtn').addEventListener('click', closeDonationPromo);
    document.getElementById('donationPromoOverlay').addEventListener('click', function(e) {
        if (e.target === this) closeDonationPromo();
    });
    
    // Donate handler - create payment directly
    document.getElementById('promoDonateBtn').addEventListener('click', async function() {
        // Get amount from custom input or selected button
        const customAmount = document.getElementById('customAmountInput').value;
        const amount = customAmount ? parseInt(customAmount) : selectedAmount;
        
        if (amount < 5000) {
            showToast('Số tiền tối thiểu là 5,000₫', 'error');
            return;
        }
        
        // Disable button
        this.disabled = true;
        this.innerHTML = '<span class="spinner"></span> Đang xử lý...';
        
        try {
            // Create payment directly via API
            const response = await fetch('/api/donate/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    amount: amount,
                    name: 'Người dùng ủng hộ',
                    email: '',
                    message: 'Ủng hộ từ modal tải xuống',
                    is_premium: false
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.checkoutUrl) {
                // Close modal and redirect to payment
                closeDonationPromo();
                window.open(data.checkoutUrl, '_blank');
            } else {
                showToast(data.error || 'Lỗi tạo thanh toán', 'error');
                this.disabled = false;
                this.innerHTML = t.promo_donate;
            }
        } catch (err) {
            showToast('Lỗi kết nối server', 'error');
            this.disabled = false;
            this.innerHTML = t.promo_donate;
        }
    });
}

function closeDonationPromo() {
    const modal = document.getElementById('donationPromoOverlay');
    if (modal) {
        modal.style.opacity = '0';
        setTimeout(() => modal.remove(), 300);
    }
}

// Show promo immediately when download starts (not random)
function showDonationPromoOnDownload() {
    showDonationPromo();
}

// Export for use in app.js
window.showDonationPromoOnDownload = showDonationPromoOnDownload;
window.showDonationPromo = showDonationPromo;