# 💰 Bảng Donations - Lưu thông tin thanh toán

## Schema

### Table: `donations`
Lưu trữ tất cả thông tin thanh toán donate

```sql
CREATE TABLE donations (
    id SERIAL PRIMARY KEY,
    order_code VARCHAR(50) UNIQUE NOT NULL,
    amount INTEGER NOT NULL,
    donor_name VARCHAR(100) DEFAULT 'Anonymous',
    donor_email VARCHAR(100),
    message TEXT,
    payment_status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(50),
    transaction_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);
```

### Columns:

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key, auto-increment |
| order_code | VARCHAR(50) | Mã đơn hàng (unique, timestamp-based) |
| amount | INTEGER | Số tiền donate (VNĐ) |
| donor_name | VARCHAR(100) | Tên người donate (default: 'Anonymous') |
| donor_email | VARCHAR(100) | Email người donate (optional) |
| message | TEXT | Lời nhắn khi tạo donation (optional) |
| payment_status | VARCHAR(20) | Trạng thái: pending, success, cancelled, failed |
| payment_method | VARCHAR(50) | Phương thức thanh toán (từ webhook) |
| transaction_id | VARCHAR(100) | Mã giao dịch từ PayOS |
| created_at | TIMESTAMP | Thời gian tạo donation |
| paid_at | TIMESTAMP | Thời gian thanh toán thành công |
| ip_address | VARCHAR(45) | IP người donate |
| user_agent | TEXT | User agent browser |

### Indexes:
```sql
CREATE INDEX idx_donations_status ON donations(payment_status);
CREATE INDEX idx_donations_created ON donations(created_at DESC);
CREATE INDEX idx_donations_paid ON donations(paid_at DESC);
```

## Payment Status Flow

```
pending → success   (thanh toán thành công)
pending → cancelled (người dùng hủy)
pending → failed    (lỗi tạo payment link)
```

### Status Details:

1. **pending**: Donation được tạo, đang chờ thanh toán
   - Tạo khi user click "Ủng hộ ngay"
   - Chưa thanh toán

2. **success**: Thanh toán thành công
   - Update khi user quay về `/payos/return`
   - Hoặc từ webhook PayOS
   - `paid_at` được set

3. **cancelled**: User hủy thanh toán
   - Update khi user quay về `/payos/cancel`

4. **failed**: Lỗi tạo payment link
   - Update khi PayOS API trả về lỗi

## Relationship

```
donations (1) ←→ (0..1) donation_messages
```

- Mỗi donation có thể có 0 hoặc 1 message
- Foreign key: `donation_messages.order_code` → `donations.order_code`
- ON DELETE CASCADE: Xóa donation → xóa message

## API Endpoints

### Public:
- `POST /api/donate/create` - Tạo donation (status: pending)
- `GET /api/donate/stats` - Thống kê donations

### Admin:
- `GET /api/admin/donations?page=1&limit=20&status=all` - Danh sách donations

### Webhooks:
- `POST /payos/webhook` - Update status từ PayOS
- `GET /payos/return` - Update status = success
- `GET /payos/cancel` - Update status = cancelled

## Usage Examples

### 1. Tạo donation mới:
```python
cursor.execute("""
    INSERT INTO donations 
    (order_code, amount, donor_name, donor_email, message, 
     payment_status, ip_address, user_agent)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
""", (order_code, amount, name, email, message, 
      'pending', ip_address, user_agent))
```

### 2. Update status thành công:
```python
cursor.execute("""
    UPDATE donations 
    SET payment_status = 'success',
        paid_at = CURRENT_TIMESTAMP
    WHERE order_code = %s
""", (order_code,))
```

### 3. Update từ webhook:
```python
cursor.execute("""
    UPDATE donations 
    SET payment_status = 'success',
        paid_at = CURRENT_TIMESTAMP,
        transaction_id = %s,
        payment_method = %s
    WHERE order_code = %s
""", (transaction_id, payment_method, order_code))
```

### 4. Thống kê:
```sql
SELECT 
    COUNT(*) as total_count,
    SUM(amount) as total_amount,
    COUNT(CASE WHEN payment_status = 'success' THEN 1 END) as success_count,
    SUM(CASE WHEN payment_status = 'success' THEN amount ELSE 0 END) as success_amount
FROM donations;
```

### 5. Top donors:
```sql
SELECT donor_name, SUM(amount) as total_donated, COUNT(*) as donation_count
FROM donations
WHERE payment_status = 'success'
GROUP BY donor_name
ORDER BY total_donated DESC
LIMIT 10;
```

## Migration

### Nếu app đã deploy:
```bash
python migrate_donations_table.py
```

### Nếu app mới:
- Table tự động tạo khi app khởi động (trong `init_db()`)

## Admin Dashboard Integration

Có thể thêm vào admin dashboard:
- Tổng số donations
- Tổng số tiền
- Conversion rate (pending → success)
- Chart donations theo ngày
- Danh sách donors
- Export CSV

## Security

### Data Protection:
- Email không hiển thị public
- IP address chỉ admin xem được
- User agent chỉ admin xem được

### Privacy:
- Donor name có thể là "Anonymous"
- Email là optional
- Message là optional

## Analytics Queries

### Donations per day (last 30 days):
```sql
SELECT 
    DATE(created_at) as date,
    COUNT(*) as count,
    SUM(amount) as total
FROM donations
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
  AND payment_status = 'success'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Success rate:
```sql
SELECT 
    payment_status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM donations
GROUP BY payment_status;
```

### Average donation:
```sql
SELECT 
    AVG(amount) as avg_amount,
    MIN(amount) as min_amount,
    MAX(amount) as max_amount
FROM donations
WHERE payment_status = 'success';
```

## Maintenance

### Clean old pending donations (>7 days):
```sql
DELETE FROM donations
WHERE payment_status = 'pending'
  AND created_at < CURRENT_DATE - INTERVAL '7 days';
```

### Archive old donations (>1 year):
```sql
-- Create archive table first
CREATE TABLE donations_archive AS 
SELECT * FROM donations WHERE FALSE;

-- Move old records
INSERT INTO donations_archive
SELECT * FROM donations
WHERE created_at < CURRENT_DATE - INTERVAL '1 year';

DELETE FROM donations
WHERE created_at < CURRENT_DATE - INTERVAL '1 year';
```

## Monitoring

### Metrics to track:
- Total donations per day
- Success rate
- Average donation amount
- Failed payment rate
- Pending → success conversion time

### Alerts:
- Success rate < 80%
- Failed payments > 10%
- No donations in 24h (if expected)

---

**Database schema hoàn chỉnh! 🎉**
