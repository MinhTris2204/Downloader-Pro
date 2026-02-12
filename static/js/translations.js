// Translation data
const translations = {
    vi: {
        nav_home: 'Trang chủ',
        nav_news: 'Tin tức',
        nav_blog: 'Blog',
        nav_donate: '☕ Ủng hộ',
        nav_mode: 'Chế độ',
        lang_name: 'Tiếng Việt',
        footer_desc: 'Công cụ tải video YouTube, TikTok miễn phí tốt nhất Việt Nam. Hỗ trợ chuyển đổi MP4, MP3 chất lượng cao.',
        footer_contact: 'Liên hệ hỗ trợ'
    },
    en: {
        nav_home: 'Home',
        nav_news: 'News',
        nav_blog: 'Blog',
        nav_donate: '☕ Donate',
        nav_mode: 'Mode',
        lang_name: 'English',
        footer_desc: 'Best free YouTube, TikTok video downloader in Vietnam. Support high quality MP4, MP3 conversion.',
        footer_contact: 'Contact Support'
    },
    ru: {
        nav_home: 'Главная',
        nav_news: 'Новости',
        nav_blog: 'Блог',
        nav_donate: '☕ Поддержать',
        nav_mode: 'Режим',
        lang_name: 'Русский',
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
