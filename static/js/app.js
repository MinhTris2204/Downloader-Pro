// ======// State for TikTok gallery
let currentTiktokImages = [];
let selectedImageIndices = new Set();
let isSelectAll = true;

// ====== Tab Switching ======
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;

        // Update buttons
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Update content
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(`${tab}-tab`).classList.add('active');
    });
});

// Event Listeners for Format Switching
document.querySelectorAll('input[name="youtube-format"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        const isVideo = e.target.value === 'mp4';
        document.getElementById('youtube-video-quality-selector').style.display = isVideo ? 'block' : 'none';
        document.getElementById('youtube-audio-quality-selector').style.display = isVideo ? 'none' : 'block';
    });
});

document.querySelectorAll('input[name="tiktok-format"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        const isVideo = e.target.value === 'mp4';
        document.getElementById('tiktok-video-quality').style.display = isVideo ? 'block' : 'none';
        document.getElementById('tiktok-audio-quality').style.display = isVideo ? 'none' : 'block';
    });
});

// ====== Paste URL and Show Preview ======
async function pasteUrl(inputId) {
    try {
        const text = await navigator.clipboard.readText();
        const input = document.getElementById(inputId);
        input.value = text;

        showToast('Đã dán link thành công!', 'success');

        // Auto fetch preview
        if (inputId === 'youtube-url') {
            fetchYoutubeInfo(text);
        } else if (inputId === 'tiktok-url') {
            fetchTiktokInfo(text);
        }
    } catch (err) {
        showToast('Không thể dán từ clipboard. Hãy dán thủ công.', 'error');
    }
}

// Helper to validate URLs
function isValidYouTubeUrl(url) {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)\/(watch\?v=|embed\/|v\/|.+\?v=)?([^&=%\?]{11})/;
    return youtubeRegex.test(url);
}

function isValidTikTokUrl(url) {
    const tiktokRegex = /^(https?:\/\/)?(www\.|vm\.|vt\.)?tiktok\.com\/.*$/;
    return tiktokRegex.test(url);
}

// ====== Fetch Video Info and Show Preview ======
async function fetchYoutubeInfo(url) {
    if (!url) return;

    if (url.length > 5 && !isValidYouTubeUrl(url)) {
        showToast('Link YouTube không đúng định dạng!', 'error');
        return;
    }

    if (url.length < 10) return;

    const downloadBtn = document.getElementById('youtube-download-btn');
    const preview = document.getElementById('youtube-preview');

    // Extract video ID
    const videoId = extractYoutubeId(url);
    if (!videoId) return;

    // Show preview with thumbnail immediately
    preview.style.display = 'flex';
    document.getElementById('youtube-thumbnail').src = `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`;
    document.getElementById('youtube-title').textContent = 'Đang tải thông tin...';
    document.getElementById('youtube-author').textContent = '';

    // Enable download button
    downloadBtn.disabled = false;
    downloadBtn.innerHTML = 'Tải Xuống';

    // Try to get title from oEmbed API (no auth needed)
    try {
        const response = await fetch(`https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=${videoId}&format=json`);
        if (response.ok) {
            const data = await response.json();
            document.getElementById('youtube-title').textContent = data.title || 'Video YouTube';
            document.getElementById('youtube-author').textContent = data.author_name || '';
        } else {
            document.getElementById('youtube-title').textContent = 'Video YouTube';
            document.getElementById('youtube-author').textContent = 'Sẵn sàng tải xuống';
        }
    } catch (err) {
        document.getElementById('youtube-title').textContent = 'Video YouTube';
        document.getElementById('youtube-author').textContent = 'Sẵn sàng tải xuống';
    }
}

function extractYoutubeId(url) {
    const regex = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/;
    const match = url.match(regex);
    return match ? match[1] : '';
}

async function fetchTiktokInfo(url) {
    console.log('fetchTiktokInfo called with URL:', url);
    
    if (!url) return;

    if (url.length > 5 && !isValidTikTokUrl(url)) {
        showToast('Link TikTok không đúng định dạng!', 'error');
        return;
    }

    if (!url || url.length < 10) return;

    // Disable download button while loading
    const downloadBtn = document.getElementById('tiktok-download-btn');
    downloadBtn.disabled = true;
    downloadBtn.innerHTML = 'Đang tải thông tin...';

    // Hide gallery and video options
    document.getElementById('tiktok-gallery').style.display = 'none';
    document.getElementById('tiktok-video-options').style.display = 'none';
    document.getElementById('tiktok-quality-selector').style.display = 'none';
    currentTiktokImages = [];
    selectedImageIndices.clear();

    // Show loading state
    const preview = document.getElementById('tiktok-preview');
    preview.style.display = 'flex';
    document.getElementById('tiktok-title').textContent = 'Đang tải thông tin...';
    document.getElementById('tiktok-author').textContent = '';
    document.getElementById('tiktok-thumbnail').src = '';

    try {
        const response = await fetch('/api/tiktok/info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        if (!response.ok) {
            document.getElementById('tiktok-title').textContent = 'Sẵn sàng tải xuống';
            document.getElementById('tiktok-author').textContent = 'Nhấn nút Tải Xuống để bắt đầu';
            downloadBtn.disabled = false;
            downloadBtn.innerHTML = 'Tải Xuống';
            return;
        }

        const data = await response.json();
        console.log('API Response:', data);

        if (data.success) {
            document.getElementById('tiktok-thumbnail').src = data.thumbnail || '';
            document.getElementById('tiktok-title').textContent = data.title || 'Video TikTok';
            document.getElementById('tiktok-author').textContent = data.author || '';

            // Handle Photo vs Video UI
            const videoOptions = document.getElementById('tiktok-video-options');
            const gallery = document.getElementById('tiktok-gallery');

            console.log('Is photo:', data.is_photo);
            console.log('Images count:', data.images ? data.images.length : 0);

            if (data.is_photo) {
                // PHOTO MODE - always show gallery for photo URLs
                console.log('Entering PHOTO MODE');
                console.log('Images received:', data.images);
                videoOptions.style.display = 'none';
                gallery.style.display = 'block';

                if (data.images && data.images.length > 0) {
                    currentTiktokImages = data.images;
                    console.log('Setting currentTiktokImages:', currentTiktokImages);
                    console.log('About to call renderGallery...');
                    renderGallery();
                    console.log('renderGallery completed');
                    showToast(`Tìm thấy ${data.images.length} ảnh! Chọn ảnh để tải.`, 'success');
                } else {
                    // Show empty gallery with loading message
                    currentTiktokImages = [];
                    const grid = document.getElementById('gallery-grid');
                    if (grid) {
                        grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 20px; color: #666;">Đang tải ảnh...</div>';
                    }
                    updateDownloadButtonText();
                    showToast('Đang tải album ảnh...', 'info');
                    
                    // Try to reload images after a short delay
                    setTimeout(() => {
                        fetchTiktokInfo(url);
                    }, 2000);
                }
            } else {
                // VIDEO MODE
                videoOptions.style.display = 'block';
                document.getElementById('tiktok-quality-selector').style.display = 'block';

                // Initialize display state based on current radio
                const isMp4 = document.querySelector('input[name="tiktok-format"]:checked').value === 'mp4';
                document.getElementById('tiktok-video-quality').style.display = isMp4 ? 'block' : 'none';
                document.getElementById('tiktok-audio-quality').style.display = isMp4 ? 'none' : 'block';

                gallery.style.display = 'none';
                downloadBtn.innerHTML = 'Tải Xuống';
            }

            downloadBtn.disabled = false;
        } else {
            document.getElementById('tiktok-title').textContent = 'Sẵn sàng tải xuống';
            document.getElementById('tiktok-author').textContent = 'Nhấn nút Tải Xuống để bắt đầu';
        }
    } catch (err) {
        document.getElementById('tiktok-title').textContent = 'Sẵn sàng tải xuống';
        document.getElementById('tiktok-author').textContent = 'Nhấn nút Tải Xuống để bắt đầu';
    }

    // Re-enable download button (if not photo logic return)
    downloadBtn.disabled = false;
    downloadBtn.innerHTML = 'Tải Xuống';
}

// ====== YouTube Download ======
async function downloadYoutube() {
    const url = document.getElementById('youtube-url').value.trim();
    const format = document.querySelector('input[name="youtube-format"]:checked').value;
    let quality;
    if (format === 'mp4') {
        quality = document.getElementById('youtube-quality').value;
    } else {
        quality = document.getElementById('youtube-audio-quality').value;
    }

    if (!url) {
        showToast('Vui lòng nhập link YouTube', 'error');
        return;
    }

    if (!isValidYouTubeUrl(url)) {
        showToast('Link YouTube không đúng định dạng!', 'error');
        return;
    }

    // Track conversion event
    if (typeof gtag_report_conversion === 'function') {
        gtag_report_conversion();
    }

    const btn = document.getElementById('youtube-download-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Đang xử lý...';

    // Hide previous complete state
    document.getElementById('youtube-complete').style.display = 'none';

    try {
        const response = await fetch('/api/youtube/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, format, quality })
        });

        const data = await response.json();

        if (data.success) {
            showProgress('youtube', data.download_id);
            
            // Show donation promo after starting download
            if (typeof showDonationPromoOnDownload === 'function') {
                showDonationPromoOnDownload();
            }
        } else {
            // Check if it's a rate limit error (429)
            if (response.status === 429 && data.error) {
                // Extract wait time from error message
                const match = data.error.match(/đợi (\d+) giây/);
                if (match) {
                    const waitTime = parseInt(match[1]);
                    startCooldownTimer('youtube', waitTime);
                } else {
                    showToast(data.error, 'error');
                    resetButton('youtube');
                }
            } else {
                showToast(data.error || 'Có lỗi xảy ra', 'error');
                resetButton('youtube');
            }
        }
    } catch (err) {
        showToast('Lỗi kết nối server', 'error');
        resetButton('youtube');
    }
}

// ====== TikTok Gallery Helpers ======
function renderGallery() {
    const grid = document.getElementById('gallery-grid');
    const gallery = document.getElementById('tiktok-gallery');
    
    // Debug logging for mobile
    console.log('renderGallery called, images:', currentTiktokImages.length);
    console.log('Gallery element:', gallery);
    console.log('Grid element:', grid);
    console.log('User Agent:', navigator.userAgent);
    console.log('Is iOS Safari:', /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream);
    
    if (!grid) {
        console.error('Gallery grid not found!');
        return;
    }
    
    grid.innerHTML = '';
    selectedImageIndices.clear();

    // Detect iOS Safari
    const isIOSSafari = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    const isMobile = window.innerWidth <= 768;

    // Force gallery to be visible - especially important on mobile
    if (gallery) {
        gallery.style.display = 'block';
        gallery.style.visibility = 'visible';
        gallery.style.opacity = '1';
        gallery.style.width = '100%';
        gallery.style.boxSizing = 'border-box';
        
        // Mobile specific fixes
        if (isMobile) {
            gallery.style.background = 'rgba(0, 0, 0, 0.2)';
            gallery.style.border = '1px solid rgba(255, 255, 255, 0.1)';
            gallery.style.borderRadius = '8px';
            gallery.style.padding = '12px';
            gallery.style.margin = '15px 0';
            
            // iOS Safari specific fixes
            if (isIOS) {
                gallery.style.webkitTransform = 'translateZ(0)';
                gallery.style.transform = 'translateZ(0)';
                gallery.style.webkitBackfaceVisibility = 'hidden';
                gallery.style.backfaceVisibility = 'hidden';
            }
        }
    }
    
    // Force grid visibility with iOS Safari fallback
    if (grid) {
        grid.style.visibility = 'visible';
        grid.style.opacity = '1';
        grid.style.width = '100%';
        
        // iOS (all browsers): Use flexbox instead of grid
        if (isIOS && isMobile) {
            grid.style.display = 'flex';
            grid.style.flexWrap = 'wrap';
            grid.style.justifyContent = 'space-between';
            grid.style.webkitFlexWrap = 'wrap';
            grid.style.webkitJustifyContent = 'space-between';
        } else {
            // Regular browsers: use grid
            grid.style.display = 'grid';
            
            if (isMobile) {
                if (window.innerWidth <= 480) {
                    grid.style.gridTemplateColumns = 'repeat(3, 1fr)';
                    grid.style.gap = '6px';
                } else {
                    grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(90px, 1fr))';
                    grid.style.gap = '8px';
                }
                grid.style.maxHeight = '280px';
                grid.style.overflowY = 'auto';
            }
        }
    }

    currentTiktokImages.forEach((url, index) => {
        console.log(`Creating gallery item ${index + 1}/${currentTiktokImages.length}:`, url);
        
        // Default select all
        selectedImageIndices.add(index);

        const item = document.createElement('div');
        item.className = 'gallery-item selected';
        item.onclick = () => toggleImageSelection(index, item);
        
        // Force item visibility
        item.style.display = 'block';
        item.style.visibility = 'visible';
        item.style.opacity = '1';
        item.style.position = 'relative';
        item.style.cursor = 'pointer';
        item.style.borderRadius = '8px';
        item.style.overflow = 'hidden';
        item.style.border = '2px solid var(--primary)';
        
        // iOS specific item styling
        if (isIOS && isMobile) {
            item.style.width = 'calc(33.333% - 4px)';
            item.style.height = '0';
            item.style.paddingBottom = 'calc(33.333% - 4px)';
            item.style.marginBottom = '6px';
            item.style.flex = '0 0 calc(33.333% - 4px)';
            item.style.webkitFlex = '0 0 calc(33.333% - 4px)';
        } else {
            item.style.aspectRatio = '1';
        }

        const img = document.createElement('img');
        // Try direct URL first for better compatibility
        img.src = url;
        img.loading = 'lazy';
        img.crossOrigin = 'anonymous';
        
        // Force image visibility
        img.style.display = 'block';
        img.style.visibility = 'visible';
        img.style.opacity = '1';
        img.style.objectFit = 'cover';
        img.style.webkitObjectFit = 'cover';
        
        // iOS specific image styling
        if (isIOS && isMobile) {
            img.style.position = 'absolute';
            img.style.top = '0';
            img.style.left = '0';
            img.style.width = '100%';
            img.style.height = '100%';
        } else {
            img.style.width = '100%';
            img.style.height = '100%';
        }
        
        img.onload = () => {
            console.log(`Image ${index + 1} loaded successfully:`, url);
        };
        
        img.onerror = () => {
            console.log(`Image ${index + 1} failed to load, trying proxy:`, url);
            // Fallback to proxy URL
            const proxyUrl = `/proxy/image?url=${encodeURIComponent(url)}`;
            img.src = proxyUrl;
            img.onerror = () => {
                console.log(`Proxy also failed for image ${index + 1}:`, url);
                img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iIzMzMyIvPjx0ZXh0IHg9IjUwIiB5PSI1NSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSIjZmZmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5JbWFnZTwvdGV4dD48L3N2Zz4=';
            };
        };

        const overlay = document.createElement('div');
        overlay.className = 'gallery-overlay';
        overlay.innerHTML = '<span class="check-icon">✓</span>';
        
        // Force overlay visibility
        overlay.style.display = 'flex';
        overlay.style.visibility = 'visible';
        overlay.style.opacity = '1';
        overlay.style.position = 'absolute';
        overlay.style.top = '5px';
        overlay.style.right = '5px';
        overlay.style.width = '20px';
        overlay.style.height = '20px';
        overlay.style.background = 'var(--primary)';
        overlay.style.borderRadius = '50%';
        overlay.style.alignItems = 'center';
        overlay.style.justifyContent = 'center';
        overlay.style.border = '2px solid var(--primary)';
        overlay.style.zIndex = '10';
        
        // iOS flexbox prefixes
        if (isIOS) {
            overlay.style.webkitAlignItems = 'center';
            overlay.style.webkitJustifyContent = 'center';
        }

        item.appendChild(img);
        item.appendChild(overlay);
        grid.appendChild(item);
        
        console.log(`Gallery item ${index + 1} added to grid`);
    });

    isSelectAll = true;
    updateSelectAllButton();
    updateDownloadButtonText();
    
    // Force a reflow to ensure visibility on mobile
    setTimeout(() => {
        if (gallery && isMobile) {
            gallery.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            
            // Double check visibility
            console.log('Gallery final styles:', {
                display: gallery.style.display,
                visibility: gallery.style.visibility,
                opacity: gallery.style.opacity,
                isIOS: isIOS
            });
        }
    }, 100);
}

function toggleImageSelection(index, element) {
    if (selectedImageIndices.has(index)) {
        selectedImageIndices.delete(index);
        element.classList.remove('selected');
    } else {
        selectedImageIndices.add(index);
        element.classList.add('selected');
    }

    updateSelectAllButton();
    updateDownloadButtonText();
}

function toggleSelectAll() {
    isSelectAll = !isSelectAll;
    const items = document.querySelectorAll('.gallery-item');

    if (isSelectAll) {
        currentTiktokImages.forEach((_, i) => selectedImageIndices.add(i));
        items.forEach(item => item.classList.add('selected'));
    } else {
        selectedImageIndices.clear();
        items.forEach(item => item.classList.remove('selected'));
    }

    updateSelectAllButton();
    updateDownloadButtonText();
}

function updateSelectAllButton() {
    const btn = document.querySelector('.select-all-btn');
    if (btn) { // Check if button exists
        if (selectedImageIndices.size === currentTiktokImages.length && currentTiktokImages.length > 0) {
            isSelectAll = true;
            btn.textContent = 'Bỏ chọn tất cả';
        } else {
            isSelectAll = false;
            btn.textContent = 'Chọn tất cả';
        }
    }
}

function updateContent() {
    const langIcon = document.getElementById('lang-icon');
    const langText = document.getElementById('lang-text');

    if (currentLang === 'vi') {
        if (langIcon) langIcon.textContent = '🇻🇳';
        if (langText) langText.textContent = 'Tiếng Việt';
    } else {
        if (langIcon) langIcon.textContent = '🇺🇸';
        if (langText) langText.textContent = 'English';
    }
}

// Make accessible globally
window.updateContent = updateContent;

function updateDownloadButtonText() {
    const btn = document.getElementById('tiktok-download-btn');
    const count = selectedImageIndices.size;
    if (count > 0) {
        btn.innerHTML = `📷 Tải ${count} Ảnh`;
        btn.disabled = false;
    } else {
        btn.innerHTML = 'Chọn ảnh để tải';
        btn.disabled = true;
    }
}

// ====== TikTok Download ======
async function downloadTiktok() {
    const url = document.getElementById('tiktok-url').value.trim();
    if (!url) {
        showToast('Vui lòng nhập link TikTok', 'error');
        return;
    }

    if (!isValidTikTokUrl(url)) {
        showToast('Link TikTok không đúng định dạng!', 'error');
        return;
    }

    // Track conversion event
    if (typeof gtag_report_conversion === 'function') {
        gtag_report_conversion();
    }

    // Get format & quality
    const formatEl = document.querySelector('input[name="tiktok-format"]:checked');
    const format = formatEl ? formatEl.value : 'mp4';

    let quality = 'best';
    if (format === 'mp4') {
        quality = document.getElementById('tiktok-video-quality').value;
    } else {
        quality = document.getElementById('tiktok-audio-quality').value;
    }

    // UI Loading
    const btn = document.getElementById('tiktok-download-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Đang xử lý...';

    // Hide previous complete state
    document.getElementById('tiktok-complete').style.display = 'none';

    // Payload
    const payload = { url, format, quality };

    // If photos, add selection
    if (currentTiktokImages.length > 0 && document.getElementById('tiktok-gallery').style.display !== 'none') {
        const selected = Array.from(selectedImageIndices);
        if (selected.length === 0) {
            showToast('Vui lòng chọn ít nhất 1 ảnh!', 'error');
            resetButton('tiktok');
            return;
        }
        payload.selected_images = selected;
    }

    try {
        const response = await fetch('/api/tiktok/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (data.success) {
            showProgress('tiktok', data.download_id);
            
            // Show donation promo after starting download
            if (typeof showDonationPromoOnDownload === 'function') {
                showDonationPromoOnDownload();
            }
        } else {
            showToast(data.error || 'Có lỗi xảy ra', 'error');
            resetButton('tiktok');
        }
    } catch (err) {
        showToast('Lỗi kết nối server', 'error');
        resetButton('tiktok');
    }
}

// ====== Progress Tracking with Auto Download ======
function showProgress(platform, downloadId) {
    document.getElementById(`${platform}-progress`).style.display = 'block';
    document.getElementById(`${platform}-complete`).style.display = 'none';

    const statusEl = document.getElementById(`${platform}-progress-status`);
    const percentEl = document.getElementById(`${platform}-progress-percent`);
    const fillEl = document.getElementById(`${platform}-progress-fill`);

    const progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/progress/${downloadId}`);
            const data = await response.json();

            const progress = Math.round(data.progress || 0);
            fillEl.style.width = `${progress}%`;
            percentEl.textContent = `${progress}%`;

            if (data.status === 'preparing') {
                statusEl.textContent = progress > 0 ? `Đang chuẩn bị... ${progress}%` : 'Đang chuẩn bị...';
            } else if (data.status === 'downloading') {
                let statusText = `Đang tải: ${progress}%`;
                if (data.speed) {
                    statusText = `Tải: ${progress}% | ${data.speed}`;
                }
                if (data.eta && data.eta !== 'Unknown') {
                    statusText += ` | Còn ${data.eta}`;
                }
                statusEl.textContent = statusText;
            } else if (data.status === 'processing') {
                statusEl.textContent = `Đang xử lý file... ${progress}%`;
            } else if (data.status === 'completed') {
                clearInterval(progressInterval);
                fillEl.style.width = '100%';
                percentEl.textContent = '100%';
                statusEl.textContent = 'Hoàn tất!';

                // Update preview with actual title if available
                if (data.title && platform === 'youtube') {
                    document.getElementById('youtube-title').textContent = data.title;
                }

                setTimeout(() => {
                    triggerDownload(downloadId);

                    document.getElementById(`${platform}-progress`).style.display = 'none';
                    document.getElementById(`${platform}-complete`).style.display = 'block';

                    document.getElementById(`${platform}-save-btn`).onclick = () => {
                        triggerDownload(downloadId);
                    };

                    resetButton(platform);
                    showToast('Tải xuống hoàn tất!', 'success');
                }, 300);
            } else if (data.status === 'error') {
                clearInterval(progressInterval);
                showToast(data.error || 'Có lỗi xảy ra khi tải', 'error');
                document.getElementById(`${platform}-progress`).style.display = 'none';
                resetButton(platform);
            }
        } catch (err) {
            console.error('Progress error:', err);
        }
    }, 500);
}


// ====== Universal Download Trigger - Works on All Devices ======
function triggerDownload(downloadId) {
    const downloadUrl = `/api/download/${downloadId}`;

    // Use hidden iframe method - most reliable and doesn't open new tabs
    let iframe = document.getElementById('download-iframe');
    if (!iframe) {
        iframe = document.createElement('iframe');
        iframe.id = 'download-iframe';
        iframe.style.display = 'none';
        document.body.appendChild(iframe);
    }

    // Set src to trigger download
    iframe.src = downloadUrl;
}


// ====== Reset Button ======
function resetButton(platform) {
    const btn = document.getElementById(`${platform}-download-btn`);
    btn.disabled = false;
    btn.innerHTML = 'Tải Xuống';
}

// ====== Cooldown Timer ======
function startCooldownTimer(platform, seconds) {
    const btn = document.getElementById(`${platform}-download-btn`);
    btn.disabled = true;

    let remaining = seconds;

    const updateButton = () => {
        if (remaining > 0) {
            btn.innerHTML = `⏳ Đợi ${remaining}s...`;
            remaining--;
            setTimeout(updateButton, 1000);
        } else {
            resetButton(platform);
            showToast('Bạn có thể tải video tiếp theo rồi! 😊', 'success');
        }
    };

    updateButton();
}

// ====== Toast Notifications ======
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ====== URL Input Events - Auto Fetch Preview ======
let youtubeDebounce = null;
let tiktokDebounce = null;

// Check if elements exist before adding event listeners
const youtubeUrlInput = document.getElementById('youtube-url');
const tiktokUrlInput = document.getElementById('tiktok-url');

if (youtubeUrlInput) {
    youtubeUrlInput.addEventListener('input', (e) => {
        const url = e.target.value.trim();

        // Debounce to avoid too many requests
        clearTimeout(youtubeDebounce);
        youtubeDebounce = setTimeout(() => {
            fetchYoutubeInfo(url);
        }, 500);
    });

    // ====== Also trigger on paste event ======
    youtubeUrlInput.addEventListener('paste', (e) => {
        setTimeout(() => {
            const url = e.target.value.trim();
            fetchYoutubeInfo(url);
        }, 100);
    });
}

if (tiktokUrlInput) {
    tiktokUrlInput.addEventListener('input', (e) => {
        const url = e.target.value.trim();

        // Debounce to avoid too many requests
        clearTimeout(tiktokDebounce);
        tiktokDebounce = setTimeout(() => {
            fetchTiktokInfo(url);
        }, 500);
    });

    tiktokUrlInput.addEventListener('paste', (e) => {
        setTimeout(() => {
            const url = e.target.value.trim();
            fetchTiktokInfo(url);
        }, 100);
    });
}

// ====== Keyboard Shortcuts ======
document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab.id === 'youtube-tab') {
            downloadYoutube();
        } else if (activeTab.id === 'tiktok-tab') {
            downloadTiktok();
        }
    }
});

// ====== Initialize ======
let lastDownloadCount = 0;

// Animated counter effect
function animateCounter(element, target, duration = 1500) {
    const start = lastDownloadCount;
    const increment = (target - start) / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= target) || (increment < 0 && current <= target)) {
            current = target;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current).toLocaleString('vi-VN');
    }, 16);

    lastDownloadCount = target;
}

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        if (data.total_downloads !== undefined) {
            const element = document.getElementById('total-downloads');
            const badge = document.getElementById('stats-badge');

            // Animate the counter
            animateCounter(element, data.total_downloads);
            badge.style.opacity = '1';

            // Add "rising" effect when count increases
            if (data.total_downloads > lastDownloadCount && lastDownloadCount > 0) {
                badge.style.animation = 'none';
                badge.offsetHeight; // Trigger reflow
                badge.style.animation = 'stats-pulse 0.5s ease-in-out 3';
            }
        }
    } catch (err) {
        console.error('Failed to fetch stats');
    }
}

console.log('Downloader Pro - Ready!');
fetchStats();

// Auto refresh stats every 30 seconds
setInterval(fetchStats, 30000);



// ====== Theme Toggle ======
const themeToggleBtn = document.getElementById('theme-toggle');
const sunIcon = document.querySelector('.sun-icon');
const moonIcon = document.querySelector('.moon-icon');

if (themeToggleBtn) {
    // Check saved theme, default to light
    const savedTheme = localStorage.getItem('theme') || 'light';

    if (savedTheme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
        if (sunIcon) sunIcon.style.display = 'none';
        if (moonIcon) moonIcon.style.display = 'block';
    } else {
        document.documentElement.removeAttribute('data-theme');
        if (sunIcon) sunIcon.style.display = 'block';
        if (moonIcon) moonIcon.style.display = 'none';
    }

    themeToggleBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');

        if (currentTheme === 'light') {
            // Switch to Dark
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('theme', 'dark');
            if (sunIcon) sunIcon.style.display = 'block';
            if (moonIcon) moonIcon.style.display = 'none';
        } else {
            // Switch to Light
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
            if (sunIcon) sunIcon.style.display = 'none';
            if (moonIcon) moonIcon.style.display = 'block';
        }
    });
}


// ====== Dropdown Language Switcher ======
const langDropdown = document.getElementById('lang-dropdown');
const langToggleBtn = document.getElementById('lang-toggle-btn');
const langMenu = document.querySelector('.lang-menu');
const langOverlay = document.getElementById('lang-overlay');
const langOptions = document.querySelectorAll('.lang-option');

// Default to Vietnamese
let currentLang = localStorage.getItem('language') || 'vi';

// SVG Flags
// SVG Flags with explicit dimensions to ensure rendering
// SVG Flags with standard 3:2 aspect ratio (900x600 coordinate system) for consistent rendering
const flagsSVGs = {
    'vi': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 600" width="100%" height="100%"><rect fill="#DA251D" width="900" height="600"/><polygon fill="#FFCD00" points="450,120 554.8,442.5 288.2,248.8 611.8,248.8 345.2,442.5"/></svg>',
    'en': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1235 650" width="100%" height="100%"><g fill-rule="evenodd"><path fill="#b22234" d="M0 0h1235v650H0z"/><path fill="#fff" d="M0 50h1235v50H0zm0 100h1235v50H0zm0 100h1235v50H0zm0 100h1235v50H0zm0 100h1235v50H0zm0 100h1235v50H0z"/><path fill="#3c3b6e" d="M0 0h494v350H0z"/><g fill="#fff"><path d="M24 18l11 35H0l11-35L0 53h35z" transform="translate(18 18) scale(0.35)"/></g></g></svg>',
    'ru': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 600" width="100%" height="100%"><rect fill="#fff" width="900" height="200"/><rect fill="#0039a6" y="200" width="900" height="200"/><rect fill="#d52b1e" y="400" width="900" height="200"/></svg>'
};

function updateContent() {
    if (typeof translations === 'undefined') return;

    const t = translations[currentLang];
    if (!t) return;

    // Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (t[key]) {
            if (el.tagName === 'INPUT' && el.getAttribute('placeholder')) {
                el.placeholder = t[key];
            } else {
                el.textContent = t[key];
            }
        }
    });

    // Update specific dynamic placeholders if needed
    const youtubeInput = document.getElementById('youtube-url');
    const tiktokInput = document.getElementById('tiktok-url');
    if (youtubeInput && t['input_placeholder_youtube']) youtubeInput.placeholder = t['input_placeholder_youtube'];
    if (tiktokInput && t['input_placeholder_tiktok']) tiktokInput.placeholder = t['input_placeholder_tiktok'];

    // Update toggle button appearance (text and flag)
    const langIcon = document.querySelector('.lang-toggle .lang-icon');
    const langText = document.querySelector('.lang-toggle .lang-text');

    if (langIcon) langIcon.innerHTML = flagsSVGs[currentLang];

    if (currentLang === 'vi') {
        if (langText) langText.textContent = 'Tiếng Việt';
    } else if (currentLang === 'en') {
        if (langText) langText.textContent = 'English';
    } else if (currentLang === 'ru') {
        if (langText) langText.textContent = 'Русский';
    }

    // Update active state in dropdown
    langOptions.forEach(opt => {
        // Update flags in dropdown as well if they are empty or text
        const optLang = opt.getAttribute('data-lang');
        const flagSpan = opt.querySelector('.lang-flag');
        if (flagSpan && !flagSpan.querySelector('svg')) {
            flagSpan.innerHTML = flagsSVGs[optLang];
        }

        if (optLang === currentLang) {
            opt.classList.add('active');
        } else {
            opt.classList.remove('active');
        }
    });
}

// Make accessible globally
window.updateContent = updateContent;

// Dropdown Logic
function toggleLangMenu() {
    langDropdown.classList.toggle('active');
    langMenu.classList.toggle('show');
    if (langOverlay) langOverlay.classList.toggle('show');

    // Accessibility
    const isExpanded = langToggleBtn.getAttribute('aria-expanded') === 'true';
    langToggleBtn.setAttribute('aria-expanded', !isExpanded);
}

function closeLangMenu() {
    langDropdown.classList.remove('active');
    langMenu.classList.remove('show');
    if (langOverlay) langOverlay.classList.remove('show');
    langToggleBtn.setAttribute('aria-expanded', 'false');
}

if (langToggleBtn) {
    langToggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleLangMenu();
    });
}

if (langOverlay) {
    langOverlay.addEventListener('click', closeLangMenu);
}

// Close when clicking outside
document.addEventListener('click', (e) => {
    if (langDropdown && !langDropdown.contains(e.target)) {
        closeLangMenu();
    }
});

// Option click handling
langOptions.forEach(option => {
    option.addEventListener('click', () => {
        const selectedLang = option.getAttribute('data-lang');
        currentLang = selectedLang;
        localStorage.setItem('language', currentLang);
        updateContent();
        closeLangMenu();
    });
});

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    updateContent();
});



// ====== Mobile Menu ======
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileSidebar = document.getElementById('mobileSidebar');
    const mobileSidebarOverlay = document.getElementById('mobileSidebarOverlay');
    const mobileThemeToggle = document.getElementById('mobileThemeToggle');
    const mobileLangBtns = document.querySelectorAll('.mobile-lang-btn');
    
    // Toggle mobile menu
    function toggleMobileMenu() {
        mobileMenuBtn.classList.toggle('active');
        mobileSidebar.classList.toggle('active');
        mobileSidebarOverlay.classList.toggle('active');
        document.body.style.overflow = mobileSidebar.classList.contains('active') ? 'hidden' : '';
        
        // Update active language when opening sidebar
        if (mobileSidebar.classList.contains('active')) {
            updateActiveMobileLang();
        }
    }
    
    // Close mobile menu
    function closeMobileMenu() {
        mobileMenuBtn.classList.remove('active');
        mobileSidebar.classList.remove('active');
        mobileSidebarOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }
    
    // Event listeners
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', toggleMobileMenu);
    }
    
    if (mobileSidebarOverlay) {
        mobileSidebarOverlay.addEventListener('click', closeMobileMenu);
    }
    
    // Close menu when clicking nav links
    document.querySelectorAll('.mobile-nav-link').forEach(link => {
        link.addEventListener('click', closeMobileMenu);
    });
    
    // Mobile theme toggle
    if (mobileThemeToggle) {
        mobileThemeToggle.addEventListener('click', function() {
            const themeToggle = document.getElementById('theme-toggle');
            if (themeToggle) {
                themeToggle.click();
            }
            
            // Update mobile theme button icons
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const sunIcon = mobileThemeToggle.querySelector('.sun-icon');
            const moonIcon = mobileThemeToggle.querySelector('.moon-icon');
            
            if (currentTheme === 'light') {
                sunIcon.style.display = 'none';
                moonIcon.style.display = 'block';
            } else {
                sunIcon.style.display = 'block';
                moonIcon.style.display = 'none';
            }
        });
    }
    
    // Mobile language buttons
    mobileLangBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const lang = this.dataset.lang;
            const langOptions = document.querySelectorAll('.lang-option');
            
            // Find and click the corresponding desktop lang option
            langOptions.forEach(option => {
                if (option.dataset.lang === lang) {
                    option.click();
                }
            });
            
            // Update active state
            updateActiveMobileLang();
            
            closeMobileMenu();
        });
    });
    
    // Function to update active mobile language button
    function updateActiveMobileLang() {
        const currentLang = localStorage.getItem('language') || 'vi';
        
        mobileLangBtns.forEach(btn => {
            if (btn.dataset.lang === currentLang) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }
    
    // Update mobile theme icons on page load
    const currentTheme = document.documentElement.getAttribute('data-theme');
    if (mobileThemeToggle) {
        const sunIcon = mobileThemeToggle.querySelector('.sun-icon');
        const moonIcon = mobileThemeToggle.querySelector('.moon-icon');
        
        if (currentTheme === 'light') {
            sunIcon.style.display = 'none';
            moonIcon.style.display = 'block';
        } else {
            sunIcon.style.display = 'block';
            moonIcon.style.display = 'none';
        }
    }
    
    // Initialize active language on page load
    updateActiveMobileLang();
});
