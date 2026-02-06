/**
 * News Viewer - Hiển thị bài báo trong modal iframe
 */

class NewsViewer {
    constructor() {
        this.modal = null;
        this.init();
    }

    init() {
        // Tạo modal HTML
        this.createModal();

        // Lắng nghe click vào các link tin tức
        this.attachEventListeners();

        // Xử lý nút Back của trình duyệt
        window.addEventListener('popstate', (event) => {
            if (this.modal.style.display === 'flex') {
                this.close(true); // true = from history event
            }
        });
    }

    createModal() {
        const modalHTML = `
            <div id="news-viewer-modal" class="news-viewer-modal" style="display: none;">
                <div class="news-viewer-overlay"></div>
                <div class="news-viewer-content">
                    <div class="news-viewer-header">
                        <button class="news-viewer-back">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <line x1="19" y1="12" x2="5" y2="12"></line>
                                <polyline points="12 19 5 12 12 5"></polyline>
                            </svg>
                            Quay lại
                        </button>
                        <div class="news-viewer-title"></div>
                        <button class="news-viewer-close" aria-label="Đóng">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>
                    </div>
                    <div class="news-viewer-body">
                        <div class="news-loading">
                            <div class="spinner"></div>
                            <p>Đang tải bài viết...</p>
                        </div>
                        <iframe class="news-iframe"></iframe>
                    </div>
                    <div class="news-viewer-footer">
                        <a href="#" target="_blank" rel="noopener noreferrer" class="news-original-link">
                            🔗 Mở bài gốc trên ${''} 
                        </a>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('news-viewer-modal');

        // Thêm CSS
        this.addStyles();

        // Xử lý đóng modal
        this.modal.querySelector('.news-viewer-close').addEventListener('click', () => this.close());
        this.modal.querySelector('.news-viewer-back').addEventListener('click', () => this.close());
        this.modal.querySelector('.news-viewer-overlay').addEventListener('click', () => this.close());
    }

    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .news-viewer-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 9999;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: fadeIn 0.3s ease;
                overscroll-behavior: none; /* Prevent pull-to-refresh */
            }
            
            .news-viewer-overlay {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                backdrop-filter: blur(5px);
                overscroll-behavior: none;
            }
            
            .news-viewer-content {
                position: relative;
                width: 95%;
                max-width: 1200px;
                height: 90vh;
                background: #fff;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                display: flex;
                flex-direction: column;
                animation: slideUp 0.3s ease;
                overflow: hidden;
                overscroll-behavior: contain;
            }
            
            [data-theme="dark"] .news-viewer-content {
                background: #1a1a2e;
            }
            
            .news-viewer-header {
                display: flex;
                align-items: center;
                gap: 15px;
                padding: 15px 20px;
                border-bottom: 1px solid rgba(99, 102, 241, 0.1);
                background: var(--card-bg);
                flex-shrink: 0; /* Header doesn't shrink */
            }
            
            .news-viewer-back,
            .news-viewer-close {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 8px 12px;
                border: none;
                background: rgba(99, 102, 241, 0.1);
                color: #6366f1;
                border-radius: 8px;
                cursor: pointer;
                font-size: 0.95em;
                transition: all 0.3s;
                flex-shrink: 0;
            }
            
            .news-viewer-back:hover,
            .news-viewer-close:hover {
                background: rgba(99, 102, 241, 0.2);
            }
            
            .news-viewer-title {
                flex: 1;
                font-weight: 600;
                font-size: 0.95em;
                opacity: 0.8;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            
            .news-viewer-body {
                flex: 1;
                position: relative;
                overflow-y: auto; /* Scroll inside body */
                -webkit-overflow-scrolling: touch;
                overscroll-behavior: contain;
            }
            
            .news-loading {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 20px;
                background: var(--card-bg);
                z-index: 10;
            }
            
            .news-loading.hidden {
                display: none;
            }
            
            .spinner {
                width: 50px;
                height: 50px;
                border: 4px solid rgba(99, 102, 241, 0.1);
                border-top-color: #6366f1;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            .news-iframe {
                width: 100%;
                height: 100%;
                border: none;
                background: #fff;
                display: block; /* Remove inline-block spacing */
            }
            
            .news-viewer-footer {
                padding: 12px 20px;
                border-top: 1px solid rgba(99, 102, 241, 0.1);
                background: var(--card-bg);
                text-align: center;
                flex-shrink: 0;
            }
            
            .news-original-link {
                color: #6366f1;
                text-decoration: none;
                font-size: 0.9em;
                display: inline-flex;
                align-items: center;
                gap: 5px;
                transition: opacity 0.3s;
            }
            
            .news-original-link:hover {
                opacity: 0.7;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes slideUp {
                from {
                    opacity: 0;
                    transform: translateY(50px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            @media (max-width: 768px) {
                .news-viewer-content {
                    width: 100%;
                    height: 100%; /* Fallback */
                    height: 100dvh; /* Dynamic viewport height */
                    max-width: none;
                    border-radius: 0;
                    margin: 0;
                }
                
                .news-viewer-title {
                    display: none;
                }

                .news-viewer-header {
                    padding: 10px 15px;
                }
                
                iframe {
                    width: 100vw; /* Ensure full viewport width */
                }
            }
        `;
        document.head.appendChild(style);
    }

    attachEventListeners() {
        // Lắng nghe click vào các card tin tức
        document.addEventListener('click', (e) => {
            const newsCard = e.target.closest('.news-card');
            if (newsCard) {
                e.preventDefault();
                const url = newsCard.getAttribute('href');
                const title = newsCard.querySelector('.news-title')?.textContent || 'Tin tức';
                this.open(url, title);
            }
        });
    }

    open(url, title) {
        if (!url) return;

        // Hiển thị modal
        this.modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        // Push history state để intercept nút Back
        history.pushState({ modalOpen: true }, '', window.location.href);

        // Cập nhật title
        this.modal.querySelector('.news-viewer-title').textContent = title;

        // Cập nhật link gốc
        const originalLink = this.modal.querySelector('.news-original-link');
        originalLink.href = url;

        // Lấy tên nguồn từ URL
        let sourceName = 'trang gốc';
        if (url.includes('vnexpress')) sourceName = 'VnExpress';
        else if (url.includes('zing')) sourceName = 'Zing News';
        else if (url.includes('genk')) sourceName = 'Genk';
        originalLink.innerHTML = `🔗 Mở bài gốc trên ${sourceName}`;

        // Hiển thị loading
        const loading = this.modal.querySelector('.news-loading');
        const iframe = this.modal.querySelector('.news-iframe');

        loading.classList.remove('hidden');
        iframe.style.display = 'none';

        // Load qua proxy để tránh CSP
        const proxyUrl = `/api/news/proxy?url=${encodeURIComponent(url)}`;
        iframe.src = proxyUrl;

        // Ẩn loading khi iframe load xong
        iframe.onload = () => {
            loading.classList.add('hidden');
            iframe.style.display = 'block';
        };

        // Nếu load lâu quá (10s), vẫn hiển thị iframe
        setTimeout(() => {
            if (!loading.classList.contains('hidden')) {
                loading.classList.add('hidden');
                iframe.style.display = 'block';
            }
        }, 10000);

        // Nếu lỗi, hiển thị thông báo
        iframe.onerror = () => {
            loading.innerHTML = `
                <div style="text-align: center; padding: 20px;">
                    <p style="color: #ef4444; margin-bottom: 15px;">❌ Không thể tải bài viết</p>
                    <p style="opacity: 0.7; margin-bottom: 20px;">Trang báo có thể đang bảo trì hoặc chặn truy cập</p>
                    <a href="${url}" target="_blank" rel="noopener noreferrer" class="download-btn" style="display: inline-block; text-decoration: none;">
                        Mở bài gốc trên ${sourceName}
                    </a>
                </div>
            `;
        };
    }

    close(fromHistory = false) {
        this.modal.style.display = 'none';
        document.body.style.overflow = '';

        // Clear iframe
        const iframe = this.modal.querySelector('.news-iframe');
        iframe.src = 'about:blank';

        // Nếu đóng bằng nút X (không phải nút Back), ta cần back history để xóa state
        if (!fromHistory) {
            history.back();
        }
    }
}

// Khởi tạo khi DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new NewsViewer();
    });
} else {
    new NewsViewer();
}
