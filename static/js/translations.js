// Translation data
const translations = {
    vi: {
        nav_home: 'Trang chủ',
        nav_news: 'Tin tức',
        nav_blog: 'Blog',
        nav_mode: 'Chế độ',
        lang_name: 'Tiếng Việt',
        donate_header: 'Ủng hộ',
        donate_title: 'Ủng hộ duy trì website',
        donate_subtitle: 'Nếu bạn thấy website hữu ích, hãy ủng hộ chúng tôi một ly cà phê để duy trì và phát triển thêm nhiều tính năng mới!',
        donate_amount: 'Chọn số tiền:',
        donate_custom: 'Khác',
        donate_name: 'Tên của bạn (tùy chọn):',
        donate_email: 'Email (tùy chọn):',
        donate_message: 'Lời nhắn (tùy chọn):',
        donate_button: '💝 Ủng hộ ngay',
        donate_messages_title: '💬 Lời nhắn từ những người ủng hộ',
        donate_messages_subtitle: 'Cảm ơn sự hỗ trợ của các bạn!',
        footer_desc: 'Công cụ tải video YouTube, TikTok miễn phí tốt nhất Việt Nam. Hỗ trợ chuyển đổi MP4, MP3 chất lượng cao.',
        footer_contact: 'Liên hệ hỗ trợ',
        // Download limit messages
        limit_title: '⚠️ Đã hết lượt tải miễn phí',
        limit_message: 'Bạn đã sử dụng hết 2 lượt tải miễn phí trong tuần này.',
        limit_explanation: 'Để duy trì và phát triển website, chúng tôi cần chi phí cho server, băng thông và bảo trì. Mong bạn thông cảm!',
        limit_premium_title: '✨ Nâng cấp Premium',
        limit_premium_benefits: '• Tải xuống không giới hạn trong 30 ngày\n• Không quảng cáo\n• Ưu tiên hỗ trợ',
        limit_amount_label: 'Chọn hoặc nhập số tiền:',
        limit_amount_custom: 'Số tiền khác',
        limit_name_label: 'Tên của bạn (tùy chọn):',
        limit_button_pay: '💳 Thanh toán',
        limit_button_cancel: 'Để sau',
        premium_status: 'Premium đến',
        downloads_remaining: 'Còn {count} lượt tải'
    },
    en: {
        nav_home: 'Home',
        nav_news: 'News',
        nav_blog: 'Blog',
        nav_mode: 'Mode',
        lang_name: 'English',
        donate_header: 'Donate',
        donate_title: 'Support Our Website',
        donate_subtitle: 'If you find our website useful, please support us with a coffee to maintain and develop more new features!',
        donate_amount: 'Choose amount:',
        donate_custom: 'Custom',
        donate_name: 'Your name (optional):',
        donate_email: 'Email (optional):',
        donate_message: 'Message (optional):',
        donate_button: '💝 Donate Now',
        donate_messages_title: '💬 Messages from Supporters',
        donate_messages_subtitle: 'Thank you for your support!',
        footer_desc: 'Best free YouTube, TikTok video downloader in Vietnam. Support high quality MP4, MP3 conversion.',
        footer_contact: 'Contact Support',
        // Download limit messages
        limit_title: '⚠️ Free Downloads Limit Reached',
        limit_message: 'You have used all 2 free downloads this week.',
        limit_explanation: 'To maintain and develop the website, we need costs for servers, bandwidth and maintenance. Thank you for understanding!',
        limit_premium_title: '✨ Upgrade to Premium',
        limit_premium_benefits: '• Unlimited downloads for 30 days\n• No ads\n• Priority support',
        limit_amount_label: 'Choose or enter amount:',
        limit_amount_custom: 'Custom amount',
        limit_name_label: 'Your name (optional):',
        limit_button_pay: '💳 Pay Now',
        limit_button_cancel: 'Later',
        premium_status: 'Premium until',
        downloads_remaining: '{count} downloads left'
    },
    ru: {
        nav_home: 'Главная',
        nav_news: 'Новости',
        nav_blog: 'Блог',
        nav_mode: 'Режим',
        lang_name: 'Русский',
        donate_header: 'Поддержать',
        donate_title: 'Поддержите наш сайт',
        donate_subtitle: 'Если вы находите наш сайт полезным, поддержите нас чашкой кофе, чтобы поддерживать и разрабатывать новые функции!',
        donate_amount: 'Выберите сумму:',
        donate_custom: 'Другое',
        donate_name: 'Ваше имя (необязательно):',
        donate_email: 'Email (необязательно):',
        donate_message: 'Сообщение (необязательно):',
        donate_button: '💝 Поддержать сейчас',
        donate_messages_title: '💬 Сообщения от спонсоров',
        donate_messages_subtitle: 'Спасибо за вашу поддержку!',
        footer_desc: 'Лучший бесплатный загрузчик видео YouTube, TikTok во Вьетнаме. Поддержка высококачественного преобразования MP4, MP3.',
        footer_contact: 'Связаться с поддержкой',
        // Download limit messages
        limit_title: '⚠️ Лимит бесплатных загрузок исчерпан',
        limit_message: 'Вы использовали все 2 бесплатные загрузки на этой неделе.',
        limit_explanation: 'Для поддержания и развития сайта нам нужны средства на серверы, трафик и обслуживание. Спасибо за понимание!',
        limit_premium_title: '✨ Обновить до Premium',
        limit_premium_benefits: '• Неограниченные загрузки на 30 дней\n• Без рекламы\n• Приоритетная поддержка',
        limit_amount_label: 'Выберите или введите сумму:',
        limit_amount_custom: 'Другая сумма',
        limit_name_label: 'Ваше имя (необязательно):',
        limit_button_pay: '💳 Оплатить',
        limit_button_cancel: 'Позже',
        premium_status: 'Premium до',
        downloads_remaining: 'Осталось {count} загрузок'
    }
};

// Get current language from localStorage or default to 'vi'
function getCurrentLanguage() {
    return localStorage.getItem('language') || 'vi';
}

// Set language
function setLanguage(lang) {
    localStorage.setItem('language', lang);
    applyTranslations(lang);
    updateLanguageUI(lang);
}

// Apply translations to page
function applyTranslations(lang) {
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (translations[lang] && translations[lang][key]) {
            element.textContent = translations[lang][key];
        }
    });
}

// Update language UI
function updateLanguageUI(lang) {
    const langFlags = {
        vi: '🇻🇳',
        en: '🇺🇸',
        ru: '🇷🇺'
    };
    
    const langIcon = document.querySelector('.lang-icon');
    const langText = document.querySelector('.lang-text');
    
    if (langIcon) langIcon.textContent = langFlags[lang] || '🇻🇳';
    if (langText) langText.textContent = translations[lang].lang_name;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    const currentLang = getCurrentLanguage();
    applyTranslations(currentLang);
    updateLanguageUI(currentLang);
    
    // Language switcher
    const langOptions = document.querySelectorAll('.lang-option');
    langOptions.forEach(option => {
        option.addEventListener('click', function() {
            const lang = this.getAttribute('data-lang');
            setLanguage(lang);
            
            // Close dropdown
            const dropdown = document.getElementById('lang-dropdown');
            if (dropdown) dropdown.classList.remove('active');
        });
    });
});
