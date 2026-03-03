// Donation Promotion Modal (Always Show on Download)

// Get current language (fallback function)
function getCurrentLanguage() {
    return localStorage.getItem('language') || 'vi';
}

// Show donation promotion modal (non-blocking)
function showDonationPromo() {
    const lang = getCurrentLanguage();
    const t = translations[lang];
    
    console.log('🌍 Current language:', lang);
    console.log('📝 Translations loaded:', !!t);
    console.log('🔑 Available keys:', t ? Object.keys(t).length : 0);
    
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
        // Convert to string and remove any existing formatting (including VNĐ)
        const numStr = num.toString().replace(/[^\d]/g, '');
        
        // If empty, return empty
        if (!numStr) return '';
        
        // Add thousand separator
        const formatted = numStr.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
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
    let formatTimeout;
    
    customAmountInput.addEventListener('input', function() {
        // Clear previous timeout
        if (formatTimeout) {
            clearTimeout(formatTimeout);
        }
        
        // Delay formatting to allow backspace/delete to work
        formatTimeout = setTimeout(() => {
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
        }, 100);
    });
    
    // Allow all keys for better user experience
    customAmountInput.addEventListener('keydown', function(e) {
        // Allow all control keys and navigation keys
        const allowedKeys = [
            8,  // Backspace
            9,  // Tab
            13, // Enter
            27, // Escape
            35, // End
            36, // Home
            37, // Left Arrow
            38, // Up Arrow
            39, // Right Arrow
            40, // Down Arrow
            46  // Delete
        ];
        
        // Allow Ctrl combinations
        if (e.ctrlKey || e.metaKey) {
            return true;
        }
        
        // Allow allowed keys
        if (allowedKeys.includes(e.keyCode)) {
            return true;
        }
        
        // Allow numbers (0-9) from both main keyboard and numpad
        if ((e.keyCode >= 48 && e.keyCode <= 57) || (e.keyCode >= 96 && e.keyCode <= 105)) {
            return true;
        }
        
        // Block everything else
        e.preventDefault();
        return false;
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
        console.log('🎯 Donate button clicked');
        
        // Get amount from custom input or selected button
        const customAmountValue = document.getElementById('customAmountInput').value;
        let amount;
        
        if (customAmountValue && customAmountValue.trim() !== '') {
            amount = parseFormattedNumber(customAmountValue);
        } else {
            amount = selectedAmount;
        }
        
        // Get donor name and message with fallbacks
        const donorNameInput = document.getElementById('donorName');
        const messageInput = document.getElementById('donationMessage');
        
        const donorName = (donorNameInput ? donorNameInput.value.trim() : '') || 
                         (t && t.anonymous_user) || 'Người dùng ẩn danh';
        const message = (messageInput ? messageInput.value.trim() : '') || 
                       (t && t.default_message) || 'Cảm ơn bạn đã ủng hộ!';
        
        console.log(`💰 Final amount: ${amount} (from custom: "${customAmountValue}", selected: ${selectedAmount})`);
        console.log(`👤 Donor: "${donorName}", Message: "${message}"`);
        
        if (!amount || amount < 5000) {
            const errorMsg = 'Số tiền tối thiểu là 5,000 VNĐ';
            console.error('❌ Amount validation failed:', errorMsg);
            
            // Try showToast, fallback to alert
            if (typeof showToast === 'function') {
                showToast(errorMsg, 'error');
            } else {
                alert(errorMsg);
            }
            return;
        }
        
        // Disable button
        this.disabled = true;
        const originalText = this.innerHTML;
        this.innerHTML = '<span class="spinner"></span> Đang xử lý...';
        
        try {
            console.log(`🚀 Sending to API: amount=${amount}, name="${donorName}"`);
            
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
            
            console.log('📡 API Response status:', response.status);
            
            if (!response.ok) {
                // Try to get error message from response
                let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    if (errorData.error) {
                        errorMessage = errorData.error;
                    }
                } catch (e) {
                    // If can't parse JSON, use default message
                }
                throw new Error(errorMessage);
            }
            
            const data = await response.json();
            console.log('📦 API Response data:', data);
            
            if (data.success && data.checkoutUrl) {
                console.log('✅ Payment link created, redirecting to:', data.checkoutUrl);
                // Close modal and redirect to PayOS payment
                closeDonationPromo();
                window.open(data.checkoutUrl, '_blank');
            } else {
                const errorMsg = data.error || 'Lỗi tạo thanh toán';
                console.error('❌ API Error:', errorMsg);
                
                if (typeof showToast === 'function') {
                    showToast(errorMsg, 'error');
                } else {
                    alert(errorMsg);
                }
                
                this.disabled = false;
                this.innerHTML = (t && t.promo_donate) || '💝 Ủng hộ';
            }
        } catch (err) {
            console.error('💥 Donation error:', err);
            const errorMsg = 'Lỗi kết nối server: ' + err.message;
            
            if (typeof showToast === 'function') {
                showToast(errorMsg, 'error');
            } else {
                alert(errorMsg);
            }
            
            this.disabled = false;
            this.innerHTML = (t && t.promo_donate) || '💝 Ủng hộ';
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