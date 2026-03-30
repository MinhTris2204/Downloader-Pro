/* ===== AUTH JS ===== */

// ===== Utility Functions =====
function showError(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = message;
        el.style.display = 'block';
        el.className = 'auth-error';
    }
}

function showSuccess(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = message;
        el.style.display = 'block';
        el.className = 'auth-success';
    }
}

function hideError(elementId) {
    const el = document.getElementById(elementId);
    if (el) el.style.display = 'none';
}

function setLoading(btn, loading) {
    if (!btn) return;
    const textEl = btn.querySelector('.btn-text');
    const loadingEl = btn.querySelector('.btn-loading');
    if (textEl) textEl.style.display = loading ? 'none' : '';
    if (loadingEl) loadingEl.style.display = loading ? 'flex' : 'none';
    btn.disabled = loading;
}

function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const wrapper = input.closest('.password-wrapper');
    const eyeOpen = wrapper.querySelector('.eye-open');
    const eyeClosed = wrapper.querySelector('.eye-closed');
    
    if (input.type === 'password') {
        input.type = 'text';
        eyeOpen.style.display = 'none';
        eyeClosed.style.display = 'block';
    } else {
        input.type = 'password';
        eyeOpen.style.display = 'block';
        eyeClosed.style.display = 'none';
    }
}

// ===== OTP Countdown =====
let resendTimer = null;

function startResendCountdown() {
    const countdown = document.getElementById('resendCountdown');
    const btn = document.getElementById('resendBtn');
    let seconds = 60;
    
    if (btn) btn.disabled = true;
    
    if (resendTimer) clearInterval(resendTimer);
    
    resendTimer = setInterval(() => {
        seconds--;
        if (countdown) countdown.textContent = seconds;
        
        if (seconds <= 0) {
            clearInterval(resendTimer);
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Gửi lại mã OTP';
            }
        }
    }, 1000);
}

// ===== Login =====
async function handleLogin() {
    const btn = document.getElementById('loginBtn') || document.querySelector('.auth-btn');
    const loginId = document.getElementById('login_id').value.trim();
    const password = document.getElementById('password').value;
    
    hideError('loginError');
    
    if (!loginId || !password) {
        showError('loginError', 'Vui lòng nhập đầy đủ thông tin');
        return;
    }
    
    setLoading(btn, true);
    
    try {
        const resp = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',  // Ensure cookies are sent
            body: JSON.stringify({ login_id: loginId, password: password })
        });
        
        const data = await resp.json();
        
        if (data.success) {
            window.location.href = data.redirect || '/';
        } else if (data.need_otp) {
            // Show OTP form
            document.getElementById('loginForm').style.display = 'none';
            document.getElementById('otpForm').style.display = 'flex';
            document.getElementById('otpEmail').textContent = loginId;
            startResendCountdown();
            window._otpPurpose = data.purpose || 'verify';
        } else {
            showError('loginError', data.error || 'Đăng nhập thất bại');
        }
    } catch (err) {
        showError('loginError', 'Lỗi kết nối. Vui lòng thử lại.');
    }
    
    setLoading(btn, false);
}

// ===== Register =====
async function handleRegister() {
    const btn = document.querySelector('#registerForm .auth-btn');
    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    
    hideError('registerError');
    
    if (!username || !email || !password || !confirmPassword) {
        showError('registerError', 'Vui lòng điền đầy đủ thông tin');
        return;
    }
    
    if (password !== confirmPassword) {
        showError('registerError', 'Mật khẩu xác nhận không khớp');
        return;
    }
    
    setLoading(btn, true);
    
    try {
        const resp = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password, confirm_password: confirmPassword })
        });
        
        const data = await resp.json();
        
        if (data.success && data.need_otp) {
            // Show OTP form
            document.getElementById('registerForm').style.display = 'none';
            document.getElementById('otpForm').style.display = 'flex';
            document.getElementById('otpEmail').textContent = email;
            window._otpPurpose = 'verify';
            startResendCountdown();
        } else if (!data.success) {
            showError('registerError', data.error || 'Đăng ký thất bại');
        }
    } catch (err) {
        showError('registerError', 'Lỗi kết nối. Vui lòng thử lại.');
    }
    
    setLoading(btn, false);
}

// ===== Verify OTP =====
async function handleVerifyOTP() {
    const btn = document.querySelector('#otpForm .auth-btn');
    const otp = document.getElementById('otp_code').value.trim();
    
    hideError('otpError');
    
    if (!otp || otp.length !== 6) {
        showError('otpError', 'Vui lòng nhập đúng 6 chữ số');
        return;
    }
    
    setLoading(btn, true);
    
    try {
        const resp = await fetch('/api/auth/verify-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ otp, purpose: window._otpPurpose || 'verify' })
        });
        
        const data = await resp.json();
        
        if (data.success) {
            if (data.redirect) {
                window.location.href = data.redirect;
            }
        } else {
            showError('otpError', data.error || 'Mã OTP không đúng');
        }
    } catch (err) {
        showError('otpError', 'Lỗi kết nối. Vui lòng thử lại.');
    }
    
    setLoading(btn, false);
}

// ===== Resend OTP =====
async function handleResendOTP() {
    try {
        const resp = await fetch('/api/auth/resend-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ purpose: window._otpPurpose || 'verify' })
        });
        
        const data = await resp.json();
        
        if (data.success) {
            startResendCountdown();
            showSuccess('otpError', 'Đã gửi lại mã OTP!');
        } else {
            showError('otpError', data.error || 'Không thể gửi lại OTP');
        }
    } catch (err) {
        showError('otpError', 'Lỗi kết nối.');
    }
}

// ===== Forgot Password =====
async function handleForgotPassword() {
    const btn = document.querySelector('#forgotForm .auth-btn');
    const email = document.getElementById('email').value.trim();
    
    hideError('forgotError');
    
    if (!email) {
        showError('forgotError', 'Vui lòng nhập email');
        return;
    }
    
    setLoading(btn, true);
    
    try {
        const resp = await fetch('/api/auth/forgot-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        
        const data = await resp.json();
        
        if (data.success && data.need_otp) {
            document.getElementById('forgotForm').style.display = 'none';
            document.getElementById('otpForm').style.display = 'flex';
            document.getElementById('otpEmail').textContent = email;
            window._otpPurpose = 'reset';
            startResendCountdown();
        } else {
            showError('forgotError', data.error || 'Không tìm thấy email');
        }
    } catch (err) {
        showError('forgotError', 'Lỗi kết nối.');
    }
    
    setLoading(btn, false);
}

// ===== Verify Reset OTP =====
async function handleVerifyResetOTP() {
    const btn = document.querySelector('#otpForm .auth-btn');
    const otp = document.getElementById('otp_code').value.trim();
    
    hideError('otpError');
    
    if (!otp || otp.length !== 6) {
        showError('otpError', 'Vui lòng nhập đúng 6 chữ số');
        return;
    }
    
    setLoading(btn, true);
    
    try {
        const resp = await fetch('/api/auth/verify-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ otp, purpose: 'reset' })
        });
        
        const data = await resp.json();
        
        if (data.success && data.can_reset) {
            document.getElementById('otpForm').style.display = 'none';
            document.getElementById('resetForm').style.display = 'flex';
        } else {
            showError('otpError', data.error || 'Mã OTP không đúng');
        }
    } catch (err) {
        showError('otpError', 'Lỗi kết nối.');
    }
    
    setLoading(btn, false);
}

// ===== Resend Reset OTP =====
async function handleResendResetOTP() {
    try {
        const resp = await fetch('/api/auth/resend-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ purpose: 'reset' })
        });
        
        const data = await resp.json();
        
        if (data.success) {
            startResendCountdown();
            showSuccess('otpError', 'Đã gửi lại mã OTP!');
        } else {
            showError('otpError', data.error);
        }
    } catch (err) {
        showError('otpError', 'Lỗi kết nối.');
    }
}

// ===== Reset Password =====
async function handleResetPassword() {
    const btn = document.querySelector('#resetForm .auth-btn');
    const newPassword = document.getElementById('new_password').value;
    const confirmPassword = document.getElementById('confirm_new_password').value;
    
    hideError('resetError');
    
    if (!newPassword || !confirmPassword) {
        showError('resetError', 'Vui lòng nhập mật khẩu mới');
        return;
    }
    
    if (newPassword.length < 6) {
        showError('resetError', 'Mật khẩu phải có ít nhất 6 ký tự');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        showError('resetError', 'Mật khẩu xác nhận không khớp');
        return;
    }
    
    setLoading(btn, true);
    
    try {
        const resp = await fetch('/api/auth/reset-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_password: newPassword, confirm_password: confirmPassword })
        });
        
        const data = await resp.json();
        
        if (data.success) {
            window.location.href = data.redirect || '/login';
        } else {
            showError('resetError', data.error || 'Lỗi đổi mật khẩu');
        }
    } catch (err) {
        showError('resetError', 'Lỗi kết nối.');
    }
    
    setLoading(btn, false);
}

// ===== Google Login =====
async function handleGoogleLogin(response) {
    try {
        const resp = await fetch('/api/auth/google', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ credential: response.credential })
        });
        
        const data = await resp.json();
        
        if (data.success) {
            window.location.href = data.redirect || '/';
        } else {
            showError('loginError', data.error || 'Đăng nhập Google thất bại');
        }
    } catch (err) {
        showError('loginError', 'Lỗi kết nối Google.');
    }
}

// ===== Logout =====
async function handleLogout() {
    try {
        const resp = await fetch('/api/auth/logout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await resp.json();
        window.location.href = data.redirect || '/';
    } catch (err) {
        window.location.href = '/';
    }
}

// ===== Premium Purchase =====
let selectedAmount = 0;

function showPremiumPurchase() {
    const section = document.getElementById('premiumPurchaseSection');
    if (section) {
        section.style.display = section.style.display === 'none' ? 'block' : 'none';
        if (section.style.display === 'block') {
            section.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
}

function selectAmount(amount) {
    selectedAmount = amount;
    document.getElementById('customAmount').value = amount;
    
    // Update button styles
    document.querySelectorAll('.amount-btn').forEach(btn => btn.classList.remove('selected'));
    event.target.closest('.amount-btn').classList.add('selected');
}

async function handlePremiumPurchase() {
    const btn = document.getElementById('premiumPayBtn');
    const customAmount = document.getElementById('customAmount').value;
    const amount = parseInt(customAmount) || selectedAmount;
    
    hideError('premiumError');
    
    if (!amount || amount < 1000) {
        showError('premiumError', 'Vui lòng chọn hoặc nhập số tiền (tối thiểu 1,000đ)');
        return;
    }
    
    setLoading(btn, true);
    
    try {
        const resp = await fetch('/api/premium/purchase', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount })
        });
        
        const data = await resp.json();
        
        if (data.success && data.checkoutUrl) {
            window.location.href = data.checkoutUrl;
        } else {
            showError('premiumError', data.error || 'Lỗi tạo link thanh toán');
        }
    } catch (err) {
        showError('premiumError', 'Lỗi kết nối. Vui lòng thử lại.');
    }
    
    setLoading(btn, false);
}

// ===== Download Limit Check (used from index.html) =====
async function checkDownloadPermission() {
    try {
        const resp = await fetch('/api/auth/check-download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await resp.json();
        
        if (!data.can_download) {
            showDownloadLimitModal(data);
            return false;
        }
        
        return true;
    } catch (err) {
        console.error('Check download error:', err);
        return true; // Allow if check fails
    }
}

function showDownloadLimitModal(data) {
    // Remove existing modal
    const existing = document.getElementById('downloadLimitOverlay');
    if (existing) existing.remove();
    
    const overlay = document.createElement('div');
    overlay.id = 'downloadLimitOverlay';
    overlay.className = 'download-limit-overlay';
    
    const isLoggedIn = data.logged_in;
    const lang = getCurrentLanguage();
    const t = translations[lang];
    
    // Check if user needs to login first
    if (!isLoggedIn && data.reason === 'require_login') {
        overlay.innerHTML = `
            <div class="download-limit-modal">
                <div class="limit-icon">🔐</div>
                <h3>${t.require_login_title}</h3>
                <p>${t.require_login_message}</p>
                <div class="limit-actions">
                    <a href="/login" class="premium-action-btn">${t.require_login_btn}</a>
                    <a href="/register" class="premium-action-btn">${t.require_register_btn}</a>
                    <button class="close-limit-btn" onclick="this.closest('.download-limit-overlay').remove()">${t.close_btn}</button>
                </div>
            </div>
        `;
    } else {
        // Show limit reached modal
        overlay.innerHTML = `
            <div class="download-limit-modal">
                <div class="limit-icon">🚫</div>
                <h3>${t.limit_reached_title}</h3>
                <p>${data.message || t.limit_reached_message}</p>
                <div class="limit-actions">
                    ${isLoggedIn ? 
                        `<a href="/premium" class="premium-action-btn">${t.upgrade_premium_btn}</a>` :
                        `<a href="/register" class="premium-action-btn">${t.register_premium_btn}</a>
                         <a href="/login" class="premium-action-btn">${t.require_login_btn}</a>`
                    }
                    <button class="close-limit-btn" onclick="this.closest('.download-limit-overlay').remove()">${t.close_btn}</button>
                </div>
            </div>
        `;
    }
    
    document.body.appendChild(overlay);
    
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) overlay.remove();
    });
}

async function recordDownload(platform) {
    try {
        await fetch('/api/auth/record-download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform })
        });
    } catch (err) {
        console.error('Record download error:', err);
    }
}

// ===== Load User Status for Header =====
async function loadUserStatus() {
    try {
        const resp = await fetch('/api/auth/me');
        const data = await resp.json();
        
        if (data.logged_in) {
            updateHeaderForUser(data.user, data.premium);
        } else {
            updateHeaderForGuest();
        }
    } catch (err) {
        console.error('Load user status error:', err);
    }
}

function updateHeaderForUser(user, premium) {
    // Don't create user-status-bar anymore, just update mobile menu
    updateMobileMenuForUser(user, premium);
    
    // Hide donation promo if premium
    const isPremium = premium && premium.is_premium;
    if (isPremium) {
        hideDonationPromo();
        hideAds();
    } else {
        // Show free download counter for free users
        showDownloadCounter(premium);
    }
}

function updateHeaderForGuest() {
    // Don't create auth button in header anymore
    // Guest users will see the login link in the nav menu
}

function updateMobileMenuForUser(user, premium) {
    const sidebar = document.querySelector('.mobile-sidebar-content');
    if (!sidebar || document.getElementById('mobileAuthSection')) return;
    
    const isPremium = premium && premium.is_premium;
    
    const section = document.createElement('div');
    section.id = 'mobileAuthSection';
    
    section.innerHTML = `
        <div class="mobile-sidebar-divider"></div>
        <a href="/account" class="mobile-nav-link">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <span>${user.username} ${isPremium ? '👑' : ''}</span>
        </a>
    `;
    
    sidebar.appendChild(section);
}

function showDownloadCounter(premium) {
    if (!premium) return;
    const left = premium.free_downloads_left !== undefined ? premium.free_downloads_left : 2;
    const max = premium.max_free_downloads || 2;
    
    // Remove existing counter
    const existing = document.getElementById('downloadCounterBar');
    if (existing) existing.remove();
    
    const bar = document.createElement('div');
    bar.id = 'downloadCounterBar';
    bar.style.cssText = 'position:fixed;bottom:20px;right:20px;background:rgba(30,30,50,0.92);color:#fff;padding:10px 16px;border-radius:12px;font-size:0.85em;z-index:9000;box-shadow:0 4px 15px rgba(0,0,0,0.3);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,0.1);';
    bar.innerHTML = left > 0
        ? `📥 Còn <strong style="color:#6ee7b7">${left}/${max}</strong> lượt tải miễn phí tháng này · <a href="/premium" style="color:#a78bfa;text-decoration:none;">Nâng cấp Premium</a>`
        : `🚫 Hết lượt tải miễn phí · <a href="/premium" style="color:#f87171;text-decoration:none;">Nâng cấp Premium</a>`;
    document.body.appendChild(bar);
    
    // Auto hide after 8 seconds
    setTimeout(() => { if (bar.parentNode) bar.remove(); }, 8000);
}

function hideDonationPromo() {
    // Hide donation/support prompts for premium users
    const donationBanner = document.querySelector('.donation-promo-banner');
    if (donationBanner) donationBanner.style.display = 'none';
    
    const supportBanner = document.querySelector('.support-banner');
    if (supportBanner) supportBanner.style.display = 'none';
    
    // Mark premium so donation-promo.js won't show modal
    window._isPremiumUser = true;
}

function hideAds() {
    // Hide Google Ads and click ads for premium users
    document.querySelectorAll('.adsbygoogle, ins.adsbygoogle').forEach(ad => {
        ad.style.display = 'none';
    });
    // Disable click-based ad script by marking premium
    window._isPremiumUser = true;
}

// ===== Password Strength =====
function checkPasswordStrength() {
    const password = document.getElementById('password');
    const strengthEl = document.getElementById('passwordStrength');
    
    if (!password || !strengthEl) return;
    
    password.addEventListener('input', () => {
        const val = password.value;
        let strength = 0;
        
        if (val.length >= 6) strength++;
        if (val.length >= 10) strength++;
        if (/[A-Z]/.test(val)) strength++;
        if (/[0-9]/.test(val)) strength++;
        if (/[^A-Za-z0-9]/.test(val)) strength++;
        
        const colors = ['#ef4444', '#f59e0b', '#eab308', '#22c55e', '#10b981'];
        const widths = ['20%', '40%', '60%', '80%', '100%'];
        
        if (val.length > 0) {
            strengthEl.innerHTML = `<div class="strength-bar" style="width: ${widths[strength - 1] || '0%'}; background: ${colors[strength - 1] || '#ef4444'};"></div>`;
        } else {
            strengthEl.innerHTML = '';
        }
    });
}

// ===== Init =====
document.addEventListener('DOMContentLoaded', () => {
    checkPasswordStrength();
    
    // Auto-detect theme
    const saved = localStorage.getItem('theme');
    if (saved) {
        document.documentElement.setAttribute('data-theme', saved);
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
    
    // Load user status on all pages (for premium ad hiding and download counter)
    loadUserStatus();
    
    // Enter key support for forms
    document.querySelectorAll('.auth-form input').forEach(input => {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const form = input.closest('.auth-form');
                const btn = form.querySelector('.auth-btn');
                if (btn) btn.click();
            }
        });
    });
});
