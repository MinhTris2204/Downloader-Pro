# Test Donation Messages Feature

## Checklist

### ✅ Database
- [ ] Table `donation_messages` được tạo thành công
- [ ] Columns đúng: id, order_code, donor_name, message, created_at, is_approved
- [ ] order_code có constraint UNIQUE
- [ ] Default values hoạt động (donor_name='Anonymous', is_approved=TRUE)

### ✅ Backend API
- [ ] POST /api/donate/message hoạt động
- [ ] GET /api/donate/messages hoạt động
- [ ] Session validation hoạt động
- [ ] Duplicate prevention hoạt động
- [ ] Input validation hoạt động (1-500 chars)

### ✅ Frontend - Form (donate_result.html)
- [ ] Form hiển thị sau khi donate thành công
- [ ] Character counter hoạt động (0/500)
- [ ] Submit button có loading state
- [ ] Success message hiển thị sau khi gửi
- [ ] Form ẩn đi sau khi gửi thành công
- [ ] Error handling hoạt động

### ✅ Frontend - Widget (index.html)
- [ ] Widget hiển thị trên trang chủ
- [ ] Loading spinner hiển thị khi đang tải
- [ ] Messages hiển thị đúng format
- [ ] Relative time hiển thị đúng ("5 phút trước")
- [ ] Scroll hoạt động nếu nhiều messages
- [ ] "Chưa có lời nhắn" hiển thị nếu empty
- [ ] XSS protection (HTML escaped)

### ✅ UI/UX
- [ ] Gradient background đẹp
- [ ] Glass effect hoạt động
- [ ] Hover effect trên cards
- [ ] Responsive trên mobile
- [ ] Font sizes phù hợp
- [ ] Colors contrast tốt

### ✅ Security
- [ ] Session-based validation
- [ ] Order code unique constraint
- [ ] Input sanitization
- [ ] SQL injection prevention
- [ ] XSS prevention

## Test Cases

### Test Case 1: Happy Path
**Steps:**
1. Donate 10,000đ
2. Thanh toán thành công
3. Nhập tên: "Test User"
4. Nhập message: "Great tool!"
5. Click "Gửi lời nhắn"

**Expected:**
- ✅ Success message hiển thị
- ✅ Message lưu vào DB
- ✅ Message hiển thị trên trang chủ

### Test Case 2: Anonymous Donor
**Steps:**
1. Donate thành công
2. Để trống tên
3. Nhập message: "Thanks!"
4. Submit

**Expected:**
- ✅ Donor name = "Anonymous"
- ✅ Message lưu thành công

### Test Case 3: Duplicate Prevention
**Steps:**
1. Donate thành công (order_code: 123)
2. Gửi message lần 1 → Success
3. Refresh page
4. Thử gửi message lần 2 với cùng order_code

**Expected:**
- ❌ Error: "Bạn đã gửi lời nhắn cho đơn hàng này rồi"

### Test Case 4: Validation - Empty Message
**Steps:**
1. Donate thành công
2. Để trống message
3. Click submit

**Expected:**
- ❌ Alert: "Vui lòng nhập lời nhắn"

### Test Case 5: Validation - Too Long
**Steps:**
1. Donate thành công
2. Nhập message > 500 chars
3. Click submit

**Expected:**
- ❌ Alert: "Lời nhắn không được quá 500 ký tự"
- Character counter màu đỏ

### Test Case 6: Session Expired
**Steps:**
1. Donate thành công
2. Clear session/cookies
3. Thử gửi message

**Expected:**
- ❌ Error: "Phiên làm việc không hợp lệ"

### Test Case 7: Widget Empty State
**Steps:**
1. Database không có messages
2. Truy cập trang chủ

**Expected:**
- 💬 Icon + "Chưa có lời nhắn nào"

### Test Case 8: Widget with Messages
**Steps:**
1. Database có 5 messages
2. Truy cập trang chủ

**Expected:**
- ✅ 5 cards hiển thị
- ✅ Donor names đúng
- ✅ Messages đúng
- ✅ Relative time đúng

### Test Case 9: XSS Prevention
**Steps:**
1. Donate thành công
2. Nhập message: `<script>alert('xss')</script>`
3. Submit

**Expected:**
- ✅ Message lưu vào DB
- ✅ Hiển thị trên trang chủ as plain text (escaped)
- ❌ Script KHÔNG chạy

### Test Case 10: Mobile Responsive
**Steps:**
1. Mở trang chủ trên mobile
2. Scroll đến widget

**Expected:**
- ✅ Widget responsive
- ✅ Cards stack vertically
- ✅ Font sizes phù hợp
- ✅ Touch-friendly

## Performance Tests

### Load Test
- [ ] Widget load < 1s với 10 messages
- [ ] Widget load < 2s với 50 messages
- [ ] API response < 500ms

### Database
- [ ] Index trên order_code (UNIQUE constraint)
- [ ] Index trên created_at (ORDER BY)
- [ ] Query optimization

## Browser Compatibility

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

## Deployment Checklist

### Before Deploy:
- [ ] Code reviewed
- [ ] Tests passed
- [ ] No console errors
- [ ] No console warnings
- [ ] Database migration ready

### After Deploy:
- [ ] Check logs for errors
- [ ] Test donate flow end-to-end
- [ ] Verify messages display on homepage
- [ ] Monitor database size
- [ ] Check performance metrics

## Monitoring

### Metrics to track:
- Messages per day
- Average message length
- Donation conversion rate (donate → message)
- Widget load time
- API response time
- Database size growth

### Alerts:
- Database connection errors
- API errors > 5%
- Widget load time > 3s
- Spam messages detected

## Rollback Plan

If issues occur:
1. Disable widget: Comment out include in index.html
2. Disable API: Comment out routes in donate_controller.py
3. Keep table: Don't drop, just disable features
4. Fix issues
5. Re-enable gradually

---

**Ready for production! 🚀**
