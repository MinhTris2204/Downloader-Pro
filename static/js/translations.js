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
        footer_contact: 'Liên hệ hỗ trợ'
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
        footer_contact: 'Contact Support'
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
        footer_contact: 'Связаться с поддержкой'
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
