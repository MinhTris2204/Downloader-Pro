/**
 * Blog Viewer - Hiển thị bài viết trong modal overlay
 */

class BlogViewer {
    constructor() {
        this.modal = null;
        this.init();
    }

    init() {
        // Tạo modal HTML
        this.createModal();
        
        // Lắng nghe click vào các link blog
        this.attachEventListeners();
    }

    createModal() {
        const modalHTML = `
            <div id="blog-modal" class="blog-modal" style="display: none;">
                <div class="blog-modal-overlay"></div>
                <div class="blog-modal-content">
                    <button class="blog-modal-close" aria-label="Đóng">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                    <div class="blog-modal-header">
                        <button class="blog-modal-back" style="display: none;">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <line x1="19" y1="12" x2="5" y2="12"></line>
                                <polyline points="12 19 5 12 12 5"></polyline>
                            </svg>
                            Quay lại
                        </button>
                    </div>
                    <div class="blog-modal-body">
                        <div class="blog-loading">
                            <div class="spinner"></div>
                            <p>Đang tải bài viết...</p>
                        </div>
                        <div class="blog-content"></div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('blog-modal');
        
        // Thêm CSS
        this.addStyles();
        
        // Xử lý đóng modal
        this.modal.querySelector('.blog-modal-close').addEventListener('click', () => this.close());
        this.modal.querySelector('.blog-modal-overlay').addEventListener('click', () => this.close());
        this.modal.querySelector('.blog-modal-back').addEventListener('click', () => this.goBack());
        
        // Ngăn scroll body khi modal mở
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });
    }

    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .blog-modal {
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
            }
            
            .blog-modal-overlay {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                backdrop-filter: blur(5px);
            }
            
            .blog-modal-content {
                position: relative;
                width: 95%;
                max-width: 900px;
                height: 90vh;
                background: var(--card-bg, #fff);
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                display: flex;
                flex-direction: column;
                animation: slideUp 0.3s ease;
                overflow: hidden;
            }
            
            [data-theme="dark"] .blog-modal-content {
                background: #1a1a2e;
            }
            
            .blog-modal-close {
                position: absolute;
                top: 20px;
                right: 20px;
                width: 40px;
                height: 40px;
                border: none;
                background: rgba(0, 0, 0, 0.1);
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s;
                z-index: 10;
            }
            
            .blog-modal-close:hover {
                background: rgba(255, 0, 0, 0.1);
                transform: rotate(90deg);
            }
            
            .blog-modal-close svg {
                color: var(--text-color, #333);
            }
            
            .blog-modal-header {
                padding: 20px 30px;
                border-bottom: 1px solid rgba(99, 102, 241, 0.1);
            }
            
            .blog-modal-back {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 8px 16px;
                border: none;
                background: rgba(99, 102, 241, 0.1);
                color: #6366f1;
                border-radius: 8px;
                cursor: pointer;
                font-size: 0.95em;
                transition: all 0.3s;
            }
            
            .blog-modal-back:hover {
                background: rgba(99, 102, 241, 0.2);
            }
            
            .blog-modal-body {
                flex: 1;
                overflow-y: auto;
                padding: 30px;
            }
            
            .blog-loading {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 300px;
                gap: 20px;
            }
            
            .spinner {
                width: 50px;
                height: 50px;
                border: 4px solid rgba(99, 102, 241, 0.1);
                border-top-color: #6366f1;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            .blog-content {
                display: none;
            }
            
            .blog-content.loaded {
                display: block;
            }
            
            .blog-content article {
                max-width: 100%;
            }
            
            .blog-content img {
                max-width: 100%;
                height: auto;
                border-radius: 10px;
            }
            
            .blog-content a {
                color: #6366f1;
                text-decoration: none;
            }
            
            .blog-content a:hover {
                text-decoration: underline;
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
                .blog-modal-content {
                    width: 100%;
                    height: 100vh;
                    border-radius: 0;
                }
                
                .blog-modal-body {
                    padding: 20px;
                }
            }
        `;
        document.head.appendChild(style);
    }

    attachEventListeners() {
        // Lắng nghe click vào các link blog
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href^="/blog/"]');
            if (link && !link.hasAttribute('data-no-modal')) {
                e.preventDefault();
                const url = link.getAttribute('href');
                this.open(url);
            }
        });
        
        // Xử lý nút back/forward của browser
        window.addEventListener('popstate', (e) => {
            if (e.state && e.state.blogUrl) {
                this.open(e.state.blogUrl, false);
            } else if (this.modal.style.display !== 'none') {
                this.close(false);
            }
        });
    }

    async open(url, pushState = true) {
        // Hiển thị modal
        this.modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        // Hiển thị loading
        const loading = this.modal.querySelector('.blog-loading');
        const content = this.modal.querySelector('.blog-content');
        loading.style.display = 'flex';
        content.style.display = 'none';
        content.classList.remove('loaded');
        
        // Hiển thị nút back nếu không phải trang blog index
        const backBtn = this.modal.querySelector('.blog-modal-back');
        if (url !== '/blog') {
            backBtn.style.display = 'inline-flex';
        } else {
            backBtn.style.display = 'none';
        }
        
        // Push state vào history
        if (pushState) {
            history.pushState({ blogUrl: url }, '', url);
        }
        
        try {
            // Fetch nội dung bài viết
            const response = await fetch(url);
            if (!response.ok) throw new Error('Failed to load');
            
            const html = await response.text();
            
            // Parse HTML và lấy nội dung
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Lấy nội dung chính (container hoặc article)
            const mainContent = doc.querySelector('.container') || doc.querySelector('article') || doc.querySelector('main');
            
            if (mainContent) {
                // Ẩn loading, hiển thị content
                loading.style.display = 'none';
                content.innerHTML = mainContent.innerHTML;
                content.style.display = 'block';
                content.classList.add('loaded');
                
                // Scroll to top
                this.modal.querySelector('.blog-modal-body').scrollTop = 0;
                
                // Re-attach event listeners cho các link trong bài viết
                this.attachInternalLinks(content);
            } else {
                throw new Error('Content not found');
            }
        } catch (error) {
            console.error('Error loading blog:', error);
            loading.innerHTML = `
                <div style="text-align: center;">
                    <p style="color: #ef4444; margin-bottom: 15px;">❌ Không thể tải bài viết</p>
                    <button onclick="location.href='${url}'" class="download-btn">
                        Mở trong trang mới
                    </button>
                </div>
            `;
        }
    }

    attachInternalLinks(container) {
        // Các link blog trong modal cũng mở trong modal
        const links = container.querySelectorAll('a[href^="/blog/"]');
        links.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const url = link.getAttribute('href');
                this.open(url);
            });
        });
    }

    goBack() {
        // Quay lại trang blog index
        this.open('/blog');
    }

    close(updateHistory = true) {
        this.modal.style.display = 'none';
        document.body.style.overflow = '';
        
        // Update history khi đóng modal
        if (updateHistory && window.location.pathname.startsWith('/blog')) {
            history.pushState(null, '', '/');
        }
    }
}

// Khởi tạo khi DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new BlogViewer();
    });
} else {
    new BlogViewer();
}
