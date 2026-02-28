# Deploy Notes - Donation Promo System

## Thay đổi chính:

### ✅ Đã hoàn thành:
1. **Xóa hệ thống giới hạn tải xuống cũ**
   - Loại bỏ logic kiểm tra 2 lượt tải/tuần
   - Xóa download status badge
   - Xóa CSS styles cho download-status

2. **Thêm hệ thống donation promo mới**
   - Modal hiển thị ngay khi nhấn tải xuống
   - Người dùng phải bấm "Bỏ qua" để đóng
   - Có ô nhập tiền tự do (tối thiểu 5,000₫)
   - Các mức tiền có sẵn: 10k, 20k, 50k, 100k VND

3. **Cập nhật giao diện**
   - Thêm custom amount input với validation
   - Hỗ trợ đa ngôn ngữ (VI/EN/RU)
   - Responsive design

### 🔧 Sau khi deploy:
1. Chạy migration để xóa bảng cũ:
   ```bash
   python migrate_remove_premium.py
   ```

2. Kiểm tra các tính năng:
   - Nhấn tải YouTube/TikTok → Modal hiện ngay
   - Test ô nhập tiền tự do
   - Test các nút preset amount
   - Test nút "Bỏ qua" và "Ủng hộ"

### 📝 Commit Message:
```
feat: Replace download limit with donation promo system

- Remove 2 downloads/week limit system
- Add immediate donation promo modal on download
- Add custom amount input (min 5,000 VND)
- Support preset amounts: 10k, 20k, 50k, 100k VND
- Multi-language support (VI/EN/RU)
- User must manually close modal (no auto-close)
- Clean up old premium tables and CSS
```

### 🚀 Deploy Command:
```bash
git add .
git commit -m "feat: Replace download limit with donation promo system"
git push origin main
```

### ⚠️ Lưu ý:
- Modal sẽ hiện ngay khi nhấn tải, không phải sau khi tải xong
- Người dùng có thể bỏ qua hoặc ủng hộ
- Không còn giới hạn số lượt tải
- Database sẽ được dọn dẹp sau deploy