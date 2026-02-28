"""Donate Controller - Xử lý donation qua PayOS"""
from flask import Blueprint, render_template, request, jsonify, redirect, session
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.payos_config import (
    PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY,
    PAYOS_RETURN_URL, PAYOS_CANCEL_URL
)
from utils.payos_helper import PayOS

donate_bp = Blueprint('donate', __name__)

# Initialize PayOS
payos = PayOS(PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY)

@donate_bp.route('/donate')
def donate_page():
    """Trang donate"""
    return render_template('donate.html')

@donate_bp.route('/api/donate/create', methods=['POST'])
def create_donation():
    """Tạo link thanh toán donate"""
    try:
        from app import db_pool
        
        data = request.get_json()
        amount = int(data.get('amount', 0))
        name = data.get('name', 'Anonymous')
        email = data.get('email', '')
        message = data.get('message', '')
        is_premium = data.get('is_premium', False)  # Flag for premium purchase
        user_id = data.get('user_id', '')  # User ID for premium activation
        
        if amount < 1000:
            return jsonify({
                'success': False,
                'error': 'Số tiền tối thiểu là 1,000 VNĐ'
            }), 400
        
        # Tạo order code unique
        order_code = int(time.time())
        
        # Get IP and User Agent
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        user_agent = request.headers.get('User-Agent', '')
        
        # Lưu thông tin donation vào database (status: pending)
        if db_pool:
            try:
                conn = db_pool.getconn()
                cursor = conn.cursor()
                
                # Store user_id in message field if premium purchase
                stored_message = message
                if is_premium and user_id:
                    stored_message = f"PREMIUM:{user_id}|{message}" if message else f"PREMIUM:{user_id}"
                
                cursor.execute("""
                    INSERT INTO donations 
                    (order_code, amount, donor_name, donor_email, message, 
                     payment_status, ip_address, user_agent, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (
                    str(order_code), amount, name, email if email else None, 
                    stored_message if stored_message else None, 'pending', ip_address, user_agent
                ))
                
                conn.commit()
                cursor.close()
                db_pool.putconn(conn)
                print(f">>> Donation record created: {order_code} (Premium: {is_premium})")
            except Exception as e:
                print(f">>> Error saving donation: {e}")
                # Continue anyway, payment link is more important
        
        # Tạo description
        description = f"{'Premium Access' if is_premium else 'Donate'} {amount:,} VND"
        if message and not is_premium:
            description += f" - {message[:50]}"
        
        # Tạo payment link
        result = payos.create_payment_link(
            order_code=order_code,
            amount=amount,
            description=description,
            return_url=PAYOS_RETURN_URL,
            cancel_url=PAYOS_CANCEL_URL,
            buyer_name=name,
            buyer_email=email if email else None
        )
        
        if 'error' in result:
            # Update status to failed
            if db_pool:
                try:
                    conn = db_pool.getconn()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE donations 
                        SET payment_status = 'failed'
                        WHERE order_code = %s
                    """, (str(order_code),))
                    conn.commit()
                    cursor.close()
                    db_pool.putconn(conn)
                except:
                    pass
            
            return jsonify({
                'success': False,
                'error': result.get('error', 'Lỗi tạo link thanh toán')
            }), 500
        
        # Check if PayOS returned error in response
        if result.get('code') != '00':
            error_msg = result.get('desc', 'Lỗi từ PayOS')
            print(f">>> PayOS Error: {error_msg}")
            
            # Update status to failed
            if db_pool:
                try:
                    conn = db_pool.getconn()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE donations 
                        SET payment_status = 'failed'
                        WHERE order_code = %s
                    """, (str(order_code),))
                    conn.commit()
                    cursor.close()
                    db_pool.putconn(conn)
                except:
                    pass
            
            return jsonify({
                'success': False,
                'error': f'PayOS: {error_msg}'
            }), 500
        
        # Lấy checkout URL từ response
        data = result.get('data')
        if not data or not isinstance(data, dict):
            return jsonify({
                'success': False,
                'error': 'Không nhận được dữ liệu từ PayOS'
            }), 500
        
        checkout_url = data.get('checkoutUrl', '')
        
        if not checkout_url:
            return jsonify({
                'success': False,
                'error': 'Không nhận được link thanh toán'
            }), 500
        
        return jsonify({
            'success': True,
            'checkoutUrl': checkout_url,
            'orderCode': order_code
        })
        
    except Exception as e:
        print(f">>> Donate Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@donate_bp.route('/payos/return')
def payos_return():
    """Xử lý khi thanh toán thành công"""
    from app import db_pool
    from utils.download_limit import activate_premium
    
    order_code = request.args.get('orderCode', '')
    status = request.args.get('status', '')
    
    # Update donation status to success and activate premium if applicable
    if db_pool and order_code:
        try:
            conn = db_pool.getconn()
            cursor = conn.cursor()
            
            # Get donation info
            cursor.execute("""
                SELECT message, amount, donor_name FROM donations
                WHERE order_code = %s
            """, (order_code,))
            
            result = cursor.fetchone()
            if result:
                message = result[0] or ''
                amount = result[1]
                donor_name = result[2] or 'Người ủng hộ'
                
                # Check if this is a premium purchase
                if message.startswith('PREMIUM:'):
                    # Extract user_id
                    parts = message.split('|')[0]
                    user_id = parts.replace('PREMIUM:', '')
                    
                    # Activate premium
                    success = activate_premium(db_pool, user_id, order_code, amount)
                    if success:
                        print(f">>> Premium activated for user {user_id[:8]}... (order: {order_code})")
                else:
                    # Auto-create donation message for regular donations
                    if message and message.strip():
                        try:
                            cursor.execute("""
                                INSERT INTO donation_messages 
                                (order_code, donor_name, message, created_at, is_approved)
                                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, TRUE)
                                ON CONFLICT (order_code) DO NOTHING
                            """, (order_code, donor_name, message.strip()))
                            print(f">>> Auto-created donation message for {order_code}")
                        except Exception as msg_err:
                            print(f">>> Error creating donation message: {msg_err}")
            
            # Update donation status
            cursor.execute("""
                UPDATE donations 
                SET payment_status = 'success',
                    paid_at = CURRENT_TIMESTAMP
                WHERE order_code = %s
            """, (order_code,))
            
            conn.commit()
            cursor.close()
            db_pool.putconn(conn)
            print(f">>> Donation {order_code} marked as success")
        except Exception as e:
            print(f">>> Error updating donation status: {e}")
    
    # Lưu order_code vào session để cho phép post message
    session['pending_donation'] = order_code
    
    return render_template('donate_result.html', 
                         success=True,
                         order_code=order_code,
                         status=status,
                         can_post_message=True)

@donate_bp.route('/payos/cancel')
def payos_cancel():
    """Xử lý khi hủy thanh toán"""
    from app import db_pool
    
    order_code = request.args.get('orderCode', '')
    
    # Update donation status to cancelled
    if db_pool and order_code:
        try:
            conn = db_pool.getconn()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE donations 
                SET payment_status = 'cancelled'
                WHERE order_code = %s
            """, (order_code,))
            
            conn.commit()
            cursor.close()
            db_pool.putconn(conn)
            print(f">>> Donation {order_code} marked as cancelled")
        except Exception as e:
            print(f">>> Error updating donation status: {e}")
    
    return render_template('donate_result.html',
                         success=False,
                         order_code=order_code)

@donate_bp.route('/payos/webhook', methods=['POST'])
def payos_webhook():
    """Webhook nhận thông báo từ PayOS"""
    try:
        from app import db_pool
        
        webhook_data = request.get_json()
        print(f">>> PayOS Webhook received: {webhook_data}")
        
        # Verify signature
        is_valid = payos.verify_webhook_signature(webhook_data)
        
        if not is_valid:
            print(">>> PayOS Webhook: Invalid signature")
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Extract data from webhook
        data = webhook_data.get('data', {})
        order_code = data.get('orderCode', '')
        amount = data.get('amount', 0)
        transaction_id = data.get('transactionDateTime', '')
        payment_method = data.get('counterAccountName', '')
        
        # Update donation in database
        if db_pool and order_code:
            try:
                conn = db_pool.getconn()
                cursor = conn.cursor()
                
                # Get donation details first
                cursor.execute("""
                    SELECT donor_name, message FROM donations
                    WHERE order_code = %s
                """, (str(order_code),))
                
                donation_info = cursor.fetchone()
                
                # Update donation status
                cursor.execute("""
                    UPDATE donations 
                    SET payment_status = 'success',
                        paid_at = CURRENT_TIMESTAMP,
                        transaction_id = %s,
                        payment_method = %s
                    WHERE order_code = %s
                """, (transaction_id, payment_method, str(order_code)))
                
                # Auto-create donation message if donor provided name and message
                if donation_info:
                    donor_name = donation_info[0] or 'Người ủng hộ'
                    message = donation_info[1]
                    
                    # Only create message if there's actual content
                    if message and message.strip() and not message.startswith('PREMIUM:'):
                        try:
                            cursor.execute("""
                                INSERT INTO donation_messages 
                                (order_code, donor_name, message, created_at, is_approved)
                                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, TRUE)
                                ON CONFLICT (order_code) DO NOTHING
                            """, (str(order_code), donor_name, message.strip()))
                            print(f">>> Auto-created donation message for {order_code}")
                        except Exception as msg_err:
                            print(f">>> Error creating donation message: {msg_err}")
                
                conn.commit()
                cursor.close()
                db_pool.putconn(conn)
                
                print(f">>> Webhook: Donation {order_code} updated successfully")
            except Exception as e:
                print(f">>> Webhook: Error updating donation: {e}")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f">>> PayOS Webhook Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@donate_bp.route('/api/donate/message', methods=['POST'])
def post_donation_message():
    """Lưu lời nhắn sau khi donate thành công"""
    try:
        from app import db_pool
        
        data = request.get_json()
        order_code = data.get('order_code', '')
        message = data.get('message', '').strip()
        donor_name = data.get('donor_name', 'Anonymous').strip()
        
        # Kiểm tra session
        pending_donation = session.get('pending_donation')
        if not pending_donation or pending_donation != order_code:
            return jsonify({
                'success': False,
                'error': 'Phiên làm việc không hợp lệ'
            }), 403
        
        # Validate message
        if not message or len(message) > 500:
            return jsonify({
                'success': False,
                'error': 'Lời nhắn phải từ 1-500 ký tự'
            }), 400
        
        if not donor_name or len(donor_name) > 100:
            donor_name = 'Anonymous'
        
        # Lưu vào database
        if db_pool:
            conn = db_pool.getconn()
            cursor = conn.cursor()
            
            # Kiểm tra xem order_code đã post message chưa
            cursor.execute("""
                SELECT COUNT(*) FROM donation_messages 
                WHERE order_code = %s
            """, (order_code,))
            
            count = cursor.fetchone()[0]
            if count > 0:
                cursor.close()
                db_pool.putconn(conn)
                return jsonify({
                    'success': False,
                    'error': 'Bạn đã gửi lời nhắn cho đơn hàng này rồi'
                }), 400
            
            # Insert message
            cursor.execute("""
                INSERT INTO donation_messages 
                (order_code, donor_name, message, created_at, is_approved)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, TRUE)
            """, (order_code, donor_name, message))
            
            conn.commit()
            cursor.close()
            db_pool.putconn(conn)
            
            # Xóa pending donation khỏi session
            session.pop('pending_donation', None)
            
            return jsonify({
                'success': True,
                'message': 'Cảm ơn bạn đã chia sẻ!'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Database không khả dụng'
            }), 500
            
    except Exception as e:
        print(f">>> Post message error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@donate_bp.route('/api/donate/messages')
def get_donation_messages():
    """Lấy danh sách lời nhắn donate (hiển thị trên trang chủ)"""
    try:
        from app import db_pool
        
        limit = int(request.args.get('limit', 10))
        if limit > 50:
            limit = 50
        
        if db_pool:
            conn = db_pool.getconn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT donor_name, message, created_at
                FROM donation_messages
                WHERE is_approved = TRUE
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'donor_name': row[0],
                    'message': row[1],
                    'created_at': row[2].isoformat() if row[2] else None
                })
            
            cursor.close()
            db_pool.putconn(conn)
            
            return jsonify({
                'success': True,
                'messages': messages
            })
        else:
            return jsonify({
                'success': False,
                'messages': []
            })
            
    except Exception as e:
        print(f">>> Get messages error: {e}")
        return jsonify({
            'success': False,
            'messages': []
        })


@donate_bp.route('/api/donate/stats')
def get_donation_stats():
    """Lấy thống kê donations"""
    try:
        from app import db_pool
        
        if not db_pool:
            return jsonify({
                'success': False,
                'error': 'Database not available'
            }), 500
        
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Total donations
        cursor.execute("""
            SELECT 
                COUNT(*) as total_count,
                COALESCE(SUM(amount), 0) as total_amount,
                COUNT(CASE WHEN payment_status = 'success' THEN 1 END) as success_count,
                COALESCE(SUM(CASE WHEN payment_status = 'success' THEN amount ELSE 0 END), 0) as success_amount
            FROM donations
        """)
        
        row = cursor.fetchone()
        stats = {
            'total_donations': row[0],
            'total_amount': row[1],
            'successful_donations': row[2],
            'successful_amount': row[3]
        }
        
        # Recent donations (last 10 successful)
        cursor.execute("""
            SELECT donor_name, amount, paid_at
            FROM donations
            WHERE payment_status = 'success'
            ORDER BY paid_at DESC
            LIMIT 10
        """)
        
        recent = []
        for row in cursor.fetchall():
            recent.append({
                'donor_name': row[0],
                'amount': row[1],
                'paid_at': row[2].isoformat() if row[2] else None
            })
        
        stats['recent_donations'] = recent
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        print(f">>> Get donation stats error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@donate_bp.route('/api/admin/donations')
def admin_get_donations():
    """Admin: Lấy danh sách donations (requires login)"""
    try:
        from app import db_pool
        from flask import session
        
        # Check admin login
        if not session.get('admin_logged_in'):
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 401
        
        if not db_pool:
            return jsonify({
                'success': False,
                'error': 'Database not available'
            }), 500
        
        # Pagination
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        offset = (page - 1) * limit
        
        # Filter by status
        status_filter = request.args.get('status', 'all')
        
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Build query
        where_clause = ""
        params = []
        if status_filter != 'all':
            where_clause = "WHERE payment_status = %s"
            params.append(status_filter)
        
        # Get total count
        cursor.execute(f"SELECT COUNT(*) FROM donations {where_clause}", params)
        total_count = cursor.fetchone()[0]
        
        # Get donations
        query = f"""
            SELECT 
                order_code, amount, donor_name, donor_email, 
                payment_status, payment_method, transaction_id,
                created_at, paid_at, ip_address
            FROM donations
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        
        donations = []
        for row in cursor.fetchall():
            donations.append({
                'order_code': row[0],
                'amount': row[1],
                'donor_name': row[2],
                'donor_email': row[3],
                'payment_status': row[4],
                'payment_method': row[5],
                'transaction_id': row[6],
                'created_at': row[7].isoformat() if row[7] else None,
                'paid_at': row[8].isoformat() if row[8] else None,
                'ip_address': row[9]
            })
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({
            'success': True,
            'donations': donations,
            'total': total_count,
            'page': page,
            'limit': limit
        })
        
    except Exception as e:
        print(f">>> Admin get donations error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
