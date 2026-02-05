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

        if (data.success) {
            document.getElementById('tiktok-thumbnail').src = data.thumbnail || '';
            document.getElementById('tiktok-title').textContent = data.title || 'Video TikTok';
            document.getElementById('tiktok-author').textContent = data.author || '';

            // Handle Photo vs Video UI
            const videoOptions = document.getElementById('tiktok-video-options');
            const gallery = document.getElementById('tiktok-gallery');

            if (data.is_photo && data.images && data.images.length > 0) {
                // PHOTO MODE
                videoOptions.style.display = 'none';
                gallery.style.display = 'block';

                currentTiktokImages = data.images;
                renderGallery(); // This will auto-update button text
                showToast(`Tìm thấy ${data.images.length} ảnh!`, 'success');
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
    grid.innerHTML = '';

    selectedImageIndices.clear();

    currentTiktokImages.forEach((url, index) => {
        // Default select all
        selectedImageIndices.add(index);

        const item = document.createElement('div');
        item.className = 'gallery-item selected';
        item.onclick = () => toggleImageSelection(index, item);

        const img = document.createElement('img');
        img.src = url;
        img.loading = 'lazy';

        const overlay = document.createElement('div');
        overlay.className = 'gallery-overlay';
        overlay.innerHTML = '<span class="check-icon">✓</span>';

        item.appendChild(img);
        item.appendChild(overlay);
        grid.appendChild(item);
    });

    isSelectAll = true;
    updateSelectAllButton();
    updateDownloadButtonText();
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
                statusEl.textContent = 'Đang chuẩn bị...';
            } else if (data.status === 'downloading') {
                let statusText = 'Đang tải xuống...';
                if (data.speed) {
                    statusText = `Tải: ${data.speed}`;
                }
                if (data.eta && data.eta !== 'Unknown') {
                    statusText += ` | Còn ${data.eta}`;
                }
                statusEl.textContent = statusText;
            } else if (data.status === 'processing') {
                statusEl.textContent = 'Đang xử lý file...';
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
async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        if (data.total_downloads) {
            const displayCount = data.total_downloads.toLocaleString();
            document.getElementById('total-downloads').textContent = `${displayCount}+`;
            document.getElementById('stats-badge').style.opacity = '1';
        }
    } catch (err) {
        console.error('Failed to fetch stats');
    }
}

console.log('Downloader Pro - Ready!');
fetchStats();


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

