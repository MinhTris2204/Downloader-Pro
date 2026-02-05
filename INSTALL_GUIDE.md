# Hướng Dẫn Cài Đặt Server

## Yêu Cầu Hệ Thống

### 1. Python 3.8+
```bash
python3 --version
```

### 2. FFmpeg (Bắt buộc cho chuyển đổi video/audio)
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg

# macOS
brew install ffmpeg

# Kiểm tra
ffmpeg -version
```

### 3. JavaScript Runtime (Khuyến nghị cho YouTube)
Cài đặt một trong các runtime sau:

#### Option A: Deno (Khuyến nghị)
```bash
# Linux/macOS
curl -fsSL https://deno.land/install.sh | sh

# Thêm vào PATH
echo 'export PATH="$HOME/.deno/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Kiểm tra
deno --version
```

#### Option B: Node.js
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Kiểm tra
node --version
```

### 4. yt-dlp (Phiên bản mới nhất)
```bash
pip install -U yt-dlp

# Hoặc cài từ GitHub (nightly build)
pip install --upgrade https://github.com/yt-dlp/yt-dlp/archive/master.tar.gz

# Kiểm tra
yt-dlp --version
```

## Cài Đặt Dependencies

```bash
# Clone repository
git clone https://github.com/MinhTris2204/Downloader-Pro.git
cd Downloader-Pro

# Cài đặt Python packages
pip install -r requirements.txt

# Hoặc với virtual environment (khuyến nghị)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# hoặc: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Chạy Server

### Development
```bash
python app.py
```

### Production (với Waitress)
```bash
# Đã được cấu hình trong app.py
python app.py
```

### Production (với Gunicorn - Linux only)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

## Kiểm Tra Cài Đặt

Chạy script test:
```bash
python test_youtube.py
```

Kết quả mong đợi:
```
✅ SUCCESS!
Title: [Video title]
Duration: [seconds]
Available formats: [number]
```

## Xử Lý Lỗi Thường Gặp

### 1. "Failed to extract any player response"
**Nguyên nhân**: Thiếu JavaScript runtime hoặc yt-dlp cũ

**Giải pháp**:
```bash
# Cài Deno
curl -fsSL https://deno.land/install.sh | sh

# Cập nhật yt-dlp
pip install -U yt-dlp

# Khởi động lại server
```

### 2. "ffmpeg not found"
**Nguyên nhân**: Chưa cài FFmpeg

**Giải pháp**:
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# Kiểm tra
ffmpeg -version
```

### 3. "No supported JavaScript runtime"
**Nguyên nhân**: Không có deno/node

**Giải pháp**:
```bash
# Cài Deno (khuyến nghị)
curl -fsSL https://deno.land/install.sh | sh

# Hoặc Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 4. Port đã được sử dụng
**Giải pháp**:
```bash
# Tìm process đang dùng port 8080
lsof -i :8080

# Kill process
kill -9 [PID]

# Hoặc đổi port trong app.py
```

## Cấu Hình Server Production

### 1. Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name downloaderpro.io.vn;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Tăng timeout cho download lớn
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
```

### 2. Systemd Service
Tạo file `/etc/systemd/system/downloaderpro.service`:
```ini
[Unit]
Description=DownloaderPro Web Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/Downloader-Pro
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Kích hoạt:
```bash
sudo systemctl daemon-reload
sudo systemctl enable downloaderpro
sudo systemctl start downloaderpro
sudo systemctl status downloaderpro
```

## Cập Nhật

```bash
# Pull code mới
git pull origin main

# Cập nhật dependencies
pip install -r requirements.txt

# Cập nhật yt-dlp
pip install -U yt-dlp

# Khởi động lại service
sudo systemctl restart downloaderpro
```

## Monitoring

### Xem logs
```bash
# Systemd logs
sudo journalctl -u downloaderpro -f

# Hoặc nếu chạy trực tiếp
tail -f app.log
```

### Kiểm tra health
```bash
curl http://localhost:8080/
```

## Bảo Mật

1. **Firewall**: Chỉ mở port 80/443
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

2. **SSL/TLS**: Sử dụng Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d downloaderpro.io.vn
```

3. **Rate Limiting**: Cấu hình trong Nginx
```nginx
limit_req_zone $binary_remote_addr zone=download:10m rate=10r/m;

location / {
    limit_req zone=download burst=5;
    # ...
}
```

## Hiệu Năng

### 1. Tăng số workers
```python
# app.py
serve(app, host='0.0.0.0', port=8080, threads=8)
```

### 2. Cache
Cài đặt Redis cho caching (tùy chọn)

### 3. CDN
Sử dụng Cloudflare cho static files

## Hỗ Trợ

- GitHub Issues: https://github.com/MinhTris2204/Downloader-Pro/issues
- Email: support@downloaderpro.io.vn
