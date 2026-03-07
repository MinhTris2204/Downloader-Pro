# Hướng dẫn cấu hình Facebook Login

## Bước 1: Tạo Facebook App

1. Truy cập https://developers.facebook.com/apps/
2. Nhấn "Create App" (Tạo ứng dụng)
3. Chọn "Consumer" hoặc "None" làm use case
4. Điền thông tin:
   - App Name: Tên ứng dụng của bạn (vd: Downloader Pro)
   - App Contact Email: Email liên hệ
5. Nhấn "Create App"

## Bước 2: Thêm Facebook Login

1. Trong Dashboard của App, tìm "Add Products"
2. Tìm "Facebook Login" và nhấn "Set Up"
3. Chọn "Web" platform
4. Nhập URL website của bạn (vd: https://downloaderpro.io.vn)

### Cấu hình Facebook Login Settings

1. Vào **Facebook Login** > **Settings** trong menu bên trái
2. Bật các tùy chọn sau:
   - ✅ **Client OAuth Login**: Yes
   - ✅ **Web OAuth Login**: Yes
   - ✅ **Use Strict Mode for Redirect URIs**: Yes (khuyến nghị)

3. Trong **Valid OAuth Redirect URIs**, thêm các URL sau (mỗi URL một dòng):
   ```
   https://downloaderpro.io.vn/
   https://downloaderpro.io.vn/login
   https://downloaderpro.io.vn/register
   ```

4. Trong **Allowed Domains for the JavaScript SDK**, thêm:
   ```
   downloaderpro.io.vn
   ```
   
   **Lưu ý:** Chỉ nhập domain, không có `https://` hay `www.`

5. Nhấn **Save Changes**

## Bước 3: Cấu hình OAuth Redirect URIs

1. Vào "Facebook Login" > "Settings" trong menu bên trái
2. Trong phần "Cài đặt" (Settings), tìm mục:

### Công cụ xác thực URI chuyển hướng (Valid OAuth Redirect URIs)

Điền các URL sau (thay `your-domain.com` bằng domain thực của bạn):

```
https://downloaderpro.io.vn/
https://downloaderpro.io.vn/login
https://downloaderpro.io.vn/register
```

**Lưu ý quan trọng:**
- Phải có `https://` ở đầu (không dùng http://)
- Mỗi URL một dòng
- Không có dấu cách thừa
- Phải match chính xác với domain website của bạn

### Kiểm tra URI (Deauthorize Callback URL) - Tùy chọn

Nếu muốn xử lý khi user hủy quyền truy cập:
```
https://downloaderpro.io.vn/api/auth/facebook-deauth
```

### Xóa dữ liệu (Data Deletion Request URL) - Bắt buộc cho Live Mode

Để app được chuyển sang Live, cần có URL xử lý yêu cầu xóa dữ liệu:
```
https://downloaderpro.io.vn/api/auth/facebook-delete-data
```

3. Nhấn "Save Changes" (Lưu thay đổi)

## Bước 4: Cấu hình URL chuyển hướng OAuth hợp lệ

Trong ảnh của bạn, điền vào ô "Chuyển hướng URI xác kiểm tra":

```
https://downloaderpro.io.vn/login
```

Sau đó nhấn "Kiểm tra URI" để Facebook kiểm tra URL có hoạt động không.

## Bước 5: Lấy App ID và App Secret

1. Vào "Settings" > "Basic" trong menu bên trái
2. Copy "App ID" (Mã ứng dụng)
3. Nhấn "Show" để hiện "App Secret" (Khóa bí mật ứng dụng) và copy
4. Thêm vào file `.env`:
   ```
   FACEBOOK_APP_ID=1234567890123456
   FACEBOOK_APP_SECRET=abcdef1234567890abcdef1234567890
   ```

## Bước 6: Cấu hình Domain

1. Vào "Settings" > "Basic"
2. Kéo xuống phần "App Domains" (Miền ứng dụng)
3. Thêm domain của bạn (không có https://):
   ```
   downloaderpro.io.vn
   ```

## Bước 7: Chạy Migration

Chạy script để thêm cột `facebook_id` vào database:

```bash
python add_facebook_column.py
```

## Bước 8: Chuyển App sang Live Mode

1. Vào "Settings" > "Basic"
2. Kéo xuống "App Mode"
3. Chuyển từ "Development" sang "Live"
4. Điền đầy đủ thông tin yêu cầu:
   - **Privacy Policy URL**: https://downloaderpro.io.vn/privacy (cần tạo trang này)
   - **Terms of Service URL**: https://downloaderpro.io.vn/terms (cần tạo trang này)
   - **App Icon**: Upload logo 1024x1024px
   - **Category**: Chọn "Entertainment" hoặc "Utilities"
   - **Data Deletion Instructions URL**: https://downloaderpro.io.vn/api/auth/facebook-delete-data

## Bước 9: Yêu cầu Permissions (nếu cần)

App mặc định có quyền `public_profile`. Để lấy email:

1. Vào "App Review" > "Permissions and Features"
2. Tìm "email" permission
3. Nếu chưa có, nhấn "Request" và làm theo hướng dẫn
4. Cung cấp video demo và giải thích use case

**Lưu ý:** Permission `email` thường được approve tự động cho các app web.

## Cấu hình trong Code

### 1. File .env

```env
FACEBOOK_APP_ID=your_app_id_here
FACEBOOK_APP_SECRET=your_app_secret_here
```

### 2. Kiểm tra template login.html

Đảm bảo có đoạn code này:

```html
{% if facebook_app_id %}
<button type="button" class="btn-facebook" onclick="handleFacebookLogin()">
    <svg>...</svg>
    <span data-i18n="auth_facebook_login">Đăng nhập với Facebook</span>
</button>
{% endif %}
```

## Test

1. Mở trang login: https://downloaderpro.io.vn/login
2. Nhấn nút "Đăng nhập với Facebook"
3. Cho phép ứng dụng truy cập thông tin
4. Kiểm tra đăng nhập thành công

## Troubleshooting

### Lỗi "URL Blocked: This redirect failed"
**Nguyên nhân:** URL chuyển hướng không khớp với Valid OAuth Redirect URIs

**Giải pháp:**
- Kiểm tra URL trong Valid OAuth Redirect URIs có chính xác không
- Đảm bảo có `https://` và không có dấu `/` thừa ở cuối
- URL phải match 100% với domain thực tế

### Lỗi "App Not Setup"
**Nguyên nhân:** App ID trong .env không đúng hoặc app chưa được cấu hình

**Giải pháp:**
- Kiểm tra App ID trong .env có đúng không
- Kiểm tra đã thêm Facebook Login product chưa
- Kiểm tra domain đã được thêm vào App Domains

### Lỗi "Invalid Scope: email"
**Nguyên nhân:** App chưa được approve permission `email`

**Giải pháp:**
- Vào App Review > Permissions and Features
- Request permission `email`
- Hoặc tạm thời chỉ dùng `public_profile` (bỏ `email` trong scope)

### User không có email
**Nguyên nhân:** User từ chối cấp quyền email hoặc Facebook account không có email

**Giải pháp:**
- Code đã xử lý trường hợp này
- Sẽ tạo username từ Facebook name hoặc ID
- User vẫn đăng nhập được bình thường

### Lỗi "Can't Load URL: The domain of this URL isn't included in the app's domains"
**Nguyên nhân:** Domain chưa được thêm vào App Domains

**Giải pháp:**
1. Vào Settings > Basic
2. Thêm domain vào "App Domains"
3. Lưu thay đổi

## Checklist hoàn thành

- [ ] Tạo Facebook App
- [ ] Thêm Facebook Login product
- [ ] Cấu hình Valid OAuth Redirect URIs
- [ ] Lấy App ID và App Secret
- [ ] Thêm vào file .env
- [ ] Chạy migration script
- [ ] Thêm App Domains
- [ ] Tạo Privacy Policy và Terms of Service
- [ ] Chuyển app sang Live Mode (nếu cần)
- [ ] Test đăng nhập thành công

## Tài liệu tham khảo

- Facebook Login Documentation: https://developers.facebook.com/docs/facebook-login/web
- Graph API Reference: https://developers.facebook.com/docs/graph-api
- App Review: https://developers.facebook.com/docs/app-review
