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
                    <div class="promo-left">
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
                    </div>
                    
                    <div class="promo-right">
                        <div class="name-section">
                            <label for="donorName" class="name-label">${t.promo_name_label || 'Tên của bạn (tùy chọn):'}</label>
                            <input type="text" id="donorName" class="name-input" 
                                   placeholder="${t.promo_name_placeholder || 'Để trống sẽ hiển thị "Người dùng ẩn danh"'}" 
                                   maxlength="50">
                        </div>
                        
                        <div class="promo-amounts">
                            <button class="amount-btn-promo" data-amount="10000">10,000 VNĐ</button>
                            <button class="amount-btn-promo" data-amount="20000">20,000 VNĐ</button>
                            <button class="amount-btn-promo" data-amount="50000">50,000 VNĐ</button>
                            <button class="amount-btn-promo" data-amount="100000">100,000 VNĐ</button>
                        </div>
                        
                        <div class="custom-amount-section">
                            <label for="customAmountInput" class="custom-amount-label">${t.promo_custom_amount || 'Hoặc nhập số tiền khác:'}</label>
                            <input type="text" id="customAmountInput" class="custom-amount-input" 
                                   placeholder="${t.promo_amount_placeholder || 'Nhập số tiền (VND)'}" 
                                   inputmode="numeric">
                        </div>
                        
                        <div class="message-section">
                            <label for="donationMessage" class="message-label">${t.promo_message_label || 'Lời nhắn (tùy chọn):'}</label>
                            <textarea id="donationMessage" class="message-input" 
                                      placeholder="${t.promo_message_placeholder || 'Viết lời nhắn để hiển thị trong phần ủng hộ...'}" 
                                      maxlength="200"></textarea>
                        </div>
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
    
    // Ensure modal is visible and centered
    const modal = document.getElementById('donationPromoOverlay');
    if (modal) {
        // Prevent body scroll when modal is open
        document.body.style.overflow = 'hidden';
        
        // Force modal to be visible
        modal.style.display = 'flex';
        modal.style.position = 'fixed';
        modal.style.top = '0';
        modal.style.left = '0';
        modal.style.width = '100%';
        modal.style.height = '100%';
        modal.style.zIndex = '10001';
        
        // Scroll modal content to top if needed
        const modalContent = modal.querySelector('.donation-promo-modal');
        if (modalContent) {
            modalContent.scrollTop = 0;
        }
    }
    
    // Add event listeners
    let selectedAmount = 20000; // Default
    
    // Format number with commas (VD: 50000 -> 50,000 VNĐ)
    function formatCurrency(num) {
        const formatted = num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        return formatted + ' VNĐ';
    }
    
    // Parse formatted number back to integer (VD: 50,000 VNĐ -> 50000)
    function parseFormattedNumber(str) {
        if (!str) return 0;
        // Remove all non-digits (commas, VNĐ, spaces, etc.) and parse
        const cleanStr = str.toString().replace(/[^\d]/g, '');
        const result = parseInt(cleanStr) || 0;
        console.log(`Parsing: "${str}" -> "${cleanStr}" -> ${result}`);
        return result;
    }
    
    // Handle preset amount buttons
    document.querySelectorAll('.amount-btn-promo').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.amount-btn-promo').forEach(b => b.classList.remove('selected'));
            this.classList.add('selected');
            selectedAmount = parseInt(this.dataset.amount);
            document.getElementById('customAmountInput').value = ''; // Clear custom input
        });
    });
    
    // Handle custom amount input with formatting
    const customAmountInput = document.getElementById('customAmountInput');
    customAmountInput.addEventListener('input', function() {
        // Remove all non-digits (including k, K, etc.)
        let value = this.value.replace(/[^\d]/g, '');
        
        // Format with dots
        if (value) {
            this.value = formatCurrency(value);
            const numValue = parseInt(value);
            if (numValue >= 5000) {
                selectedAmount = numValue;
                // Deselect preset buttons
                document.querySelectorAll('.amount-btn-promo').forEach(b => b.classList.remove('selected'));
            }
        } else {
            this.value = '';
            selectedAmount = 20000; // Reset to default
        }
    });
    
    // Prevent non-numeric input completely
    customAmountInput.addEventListener('keypress', function(e) {
        // Only allow numbers and control keys
        const allowedKeys = ['0','1','2','3','4','5','6','7','8','9','Backspace','Delete','ArrowLeft','ArrowRight','Tab'];
        if (!allowedKeys.includes(e.key)) {
            e.preventDefault();
        }
    });
    
    // Prevent paste of non-numeric content
    customAmountInput.addEventListener('paste', function(e) {
        e.preventDefault();
        const paste = (e.clipboardData || window.clipboardData).getData('text');
        const numericOnly = paste.replace(/[^\d]/g, '');
        if (numericOnly) {
            this.value = formatCurrency(numericOnly);
            const numValue = parseInt(numericOnly);
            if (numValue >= 5000) {
                selectedAmount = numValue;
                document.querySelectorAll('.amount-btn-promo').forEach(b => b.classList.remove('selected'));
            }
        }
    });
    
    // Select default amount
    document.querySelector('.amount-btn-promo[data-amount="20000"]').classList.add('selected');
    
    // Close handlers - only X button and Skip button
    document.getElementById('promoCloseBtn').addEventListener('click', closeDonationPromo);
    document.getElementById('promoSkipBtn').addEventListener('click', closeDonationPromo);
    
    // Remove click outside to close - user must use X or Skip button
    // document.getElementById('donationPromoOverlay').addEventListener('click', function(e) {
    //     if (e.target === this) closeDonationPromo();
    // });
    
    // Block ESC key to close modal
    const handleKeyDown = function(e) {
        if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            // Optional: highlight the close button to show user how to close
            const closeBtn = document.getElementById('promoCloseBtn');
            if (closeBtn) {
                closeBtn.style.animation = 'pulse 0.5s ease-in-out 2';
            }
        }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    
    // Store the handler to remove it later
    window.donationModalKeyHandler = handleKeyDown;
    
    // Donate handler - create payment directly
    document.getElementById('promoDonateBtn').addEventListener('click', async function() {
        // Get amount from custom input or selected button
        const customAmountValue = document.getElementById('customAmountInput').value;
        let amount;
        
        if (customAmountValue && customAmountValue.trim() !== '') {
            amount = parseFormattedNumber(customAmountValue);
        } else {
            amount = selectedAmount;
        }
        
        // Get donor name and message
        const donorName = document.getElementById('donorName').value.trim() || t.anonymous_user || 'Người dùng ẩn danh';
        const message = document.getElementById('donationMessage').value.trim() || t.default_message || 'Cảm ơn bạn đã ủng hộ!';
        
        console.log(`Final amount: ${amount} (from custom: "${customAmountValue}", selected: ${selectedAmount})`);
        console.log(`Donor: "${donorName}", Message: "${message}"`);
        
        if (!amount || amount < 5000) {
            showToast('Số tiền tối thiểu là 5.000₫', 'error');
            return;
        }
        
        // Disable button
        this.disabled = true;
        this.innerHTML = '<span class="spinner"></span> Đang xử lý...';
        
        try {
            console.log(`Sending to API: amount=${amount}, name="${donorName}"`);
            
            // Create payment directly via API
            const response = await fetch('/api/donate/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    amount: amount,
                    name: donorName,
                    email: '',
                    message: message,
                    is_premium: false
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.checkoutUrl) {
                // Close modal and redirect to PayOS payment
                closeDonationPromo();
                window.open(data.checkoutUrl, '_blank');
            } else {
                showToast(data.error || 'Lỗi tạo thanh toán', 'error');
                this.disabled = false;
                this.innerHTML = t.promo_donate;
            }
        } catch (err) {
            console.error('Donation error:', err);
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
        setTimeout(() => {
            modal.remove();
            // Restore body scroll
            document.body.style.overflow = '';
        }, 300);
    }
    
    // Remove keyboard event listener
    if (window.donationModalKeyHandler) {
        document.removeEventListener('keydown', window.donationModalKeyHandler);
        window.donationModalKeyHandler = null;
    }
}

// Show promo immediately when download starts (not random)
function showDonationPromoOnDownload() {
    showDonationPromo();
}

// Export for use in app.js
window.showDonationPromoOnDownload = showDonationPromoOnDownload;
window.showDonationPromo = showDonationPromo;