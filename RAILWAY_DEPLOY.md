# Deploy lên Railway

## Cấu Hình Tự Động

Project đã được cấu hình để tự động cài đặt Deno khi deploy lên Railway.

### Files Cấu Hình:

1. **nixpacks.toml** - Cấu hình Nixpacks để cài Python, FFmpeg, Deno
2. **railway.json** - Cấu hình Railway
3. **Procfile** - Lệnh khởi động với script cài Deno
4. **install_deno.sh** - Script cài đặt Deno tự động

## Cách Deploy

### Option 1: Deploy từ GitHub (Khuyến nghị)

1. Push code lên GitHub:
```bash
git add .
git commit -m "Add Railway config with Deno"
git push origin main
```

2. Vào Railway Dashboard:
   - New Project → Deploy from GitHub
   - Chọn repository: `Downloader-Pro`
   - Railway sẽ tự động detect và build

3. Đợi build xong (2-3 phút)

4. Kiểm tra logs để đảm bảo Deno đã được cài:
```
Deno installed successfully!
deno 2.x.x
```

### Option 2: Deploy từ Railway CLI

```bash
# Cài Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link project
railway link

# Deploy
railway up
```

## Biến Môi Trường

Trong Railway Dashboard, thêm các biến môi trường:

```
DATABASE_URL=postgresql://...
PORT=8080
PYTHON_VERSION=3.11
```

## Kiểm Tra Sau Deploy

1. Truy cập: `https://your-app.railway.app/debug`
2. Kiểm tra xem Deno đã được cài chưa
3. Nếu thấy ✅ Deno → Thành công!
4. Test tải YouTube

## Troubleshooting

### Nếu Deno vẫn chưa được cài:

1. **Kiểm tra logs**:
   - Vào Railway Dashboard
   - Click vào Deployment
   - Xem Build Logs

2. **Thử cách khác - Dùng Aptfile**:
   
   Tạo file `Aptfile`:
   ```
   ffmpeg
   ```
   
   Và thêm vào `requirements.txt`:
   ```
   yt-dlp>=2024.12.0
   ```

3. **Hoặc dùng Docker**:
   
   Tạo `Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       ffmpeg \
       curl \
       && rm -rf /var/lib/apt/lists/*
   
   # Install Deno
   RUN curl -fsSL https://deno.land/install.sh | sh
   ENV DENO_INSTALL="/root/.deno"
   ENV PATH="$DENO_INSTALL/bin:$PATH"
   
   # Set working directory
   WORKDIR /app
   
   # Copy requirements
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Copy app
   COPY . .
   
   # Expose port
   EXPOSE 8080
   
   # Run app
   CMD ["python", "app.py"]
   ```

## Verify Installation

Sau khi deploy, chạy lệnh trong Railway Shell:

```bash
# Mở Railway Shell
railway shell

# Kiểm tra Deno
deno --version

# Kiểm tra FFmpeg
ffmpeg -version

# Kiểm tra yt-dlp
yt-dlp --version
```

## Performance Tips

1. **Tăng RAM**: Railway free tier có 512MB, nên upgrade lên 1GB
2. **Enable Persistent Storage**: Để cache downloads
3. **Add Redis**: Để cache video info (optional)

## Cost Estimate

- **Free Tier**: $5 credit/month (đủ cho traffic nhỏ)
- **Hobby Plan**: $5/month (unlimited usage)
- **Pro Plan**: $20/month (priority support)

## Support

Nếu gặp vấn đề:
1. Check Railway logs
2. Visit `/debug` endpoint
3. Contact Railway support: https://railway.app/help
