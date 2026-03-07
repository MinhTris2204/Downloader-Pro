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

# Initialize PayOS with validation
def get_payos_instance():
    """Get PayOS instance with proper error handling"""
    if not PAYOS_CLIENT_ID or not PAYOS_API_KEY or not PAYOS_CHECKSUM_KEY:
        print(">>> PayOS Error: Missing credentials in environment variables")
        print(f">>> PAYOS_CLIENT_ID: {'SET' if PAYOS_CLIENT_ID else 'NOT SET'}")
        print(f">>> PAYOS_API_KEY: {'SET' if PAYOS_API_KEY else 'NOT SET'}")
        print(f">>> PAYOS_CHECKSUM_KEY: {'SET' if PAYOS_CHECKSUM_KEY else 'NOT SET'}")
        return None
    return PayOS(PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY)

@donate_bp.route('/donate')
def donate_page():
    """Trang donate"""
    return render_template('donate.html')

@donate_bp.route('/api/donate/create', methods=['POST'])
def create_donation():
    """Tạo link thanh toán donate"""
    try:
        from app import db_pool
        
        # Check PayOS configuration first
        payos = get_payos_instance()
        if not payos:
            return jsonify({
                'success': False,
                'error': 'Hệ thống thanh toán chưa được cấu hình. Vui lòng liên hệ admin để kích hoạt PayOS.'
            }), 500
        
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
        
        # Lưu thông tin premium subscription vào database (status: pending)
        if db_pool and is_premium and user_id:
            try:
                from datetime import datetime, timedelta
                conn = db_pool.getconn()
                cursor = conn.cursor()
                
                # Create pending premium subscription
                starts_at = datetime.now()
                expires_at = datetime.now() + timedelta(days=30)
                
                cursor.execute("""
                    INSERT INTO premium_subscriptions 
                    (user_id, order_code, amount, starts_at, expires_at, is_active,
                     payment_status, donor_email, ip_address, user_agent, created_at)
                    VALUES (%s, %s, %s, %s, %s, FALSE, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (
                    int(user_id), str(order_code), amount, starts_at, expires_at,
                    'pending', email if email else None, ip_address, user_agent
                ))
                
                conn.commit()
                cursor.close()
                db_pool.putconn(conn)
                print(f">>> Premium subscription created (pending): {order_code}")
            except Exception as e:
                print(f">>> Error saving premium subscription: {e}")
                # Continue anyway, payment link is more important
        
        # Tạo description (PayOS yêu cầu tối đa 25 ký tự)
        if is_premium:
            description = "Premium Access"
        else:
            # Format: "Donate 100K" (tối đa 25 ký tự)
            if amount >= 1000000:
                amount_str = f"{amount//1000000}M"
            elif amount >= 1000:
                amount_str = f"{amount//1000}K"
            else:
                amount_str = str(amount)
            description = f"Donate {amount_str}"
        
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
            if db_pool and is_premium and user_id:
                try:
                    conn = db_pool.getconn()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE premium_subscriptions 
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
            if db_pool and is_premium and user_id:
                try:
                    conn = db_pool.getconn()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE premium_subscriptions 
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
    
    order_code = request.args.get('orderCode', '')
    status = request.args.get('status', '')
    
    premium_info = None
    
    # Update premium subscription status to success
    if db_pool and order_code:
        try:
            from datetime import datetime, timedelta
            conn = db_pool.getconn()
            cursor = conn.cursor()
            
            # Get premium subscription info
            cursor.execute("""
                SELECT ps.user_id, ps.amount, u.username, ps.expires_at, ps.is_active
                FROM premium_subscriptions ps
                LEFT JOIN users u ON ps.user_id = u.id
                WHERE ps.order_code = %s
            """, (order_code,))
            
            result = cursor.fetchone()
            if result:
                user_id = result[0]
                amount = result[1]
                username = result[2] or 'User'
                current_expires = result[3]
                is_active = result[4]
                
                premium_info = {
                    'username': username,
                    'amount': amount,
                    'message': f'PREMIUM:{user_id}'
                }
                
                # Update subscription to active and set paid_at
                cursor.execute("""
                    UPDATE premium_subscriptions 
                    SET payment_status = 'success',
                        is_active = TRUE,
                        paid_at = CURRENT_TIMESTAMP
                    WHERE order_code = %s
                """, (order_code,))
                
                print(f">>> Premium subscription {order_code} activated for user {user_id}")
            
            conn.commit()
            cursor.close()
            db_pool.putconn(conn)
        except Exception as e:
            print(f">>> Error updating premium subscription: {e}")
    
    return render_template('donate_result.html', 
                         success=True,
                         order_code=order_code,
                         status=status,
                         donation_info=premium_info)

@donate_bp.route('/payos/cancel')
def payos_cancel():
    """Xử lý khi hủy thanh toán"""
    from app import db_pool
    
    order_code = request.args.get('orderCode', '')
    
    # Update premium subscription status to cancelled
    if db_pool and order_code:
        try:
            conn = db_pool.getconn()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE premium_subscriptions 
                SET payment_status = 'cancelled'
                WHERE order_code = %s
            """, (order_code,))
            
            conn.commit()
            cursor.close()
            db_pool.putconn(conn)
            print(f">>> Premium subscription {order_code} marked as cancelled")
        except Exception as e:
            print(f">>> Error updating premium subscription: {e}")
    
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
                
                # Update premium subscription status
                cursor.execute("""
                    UPDATE premium_subscriptions 
                    SET payment_status = 'success',
                        is_active = TRUE,
                        paid_at = CURRENT_TIMESTAMP,
                        transaction_id = %s,
                        payment_method = %s
                    WHERE order_code = %s
                """, (transaction_id, payment_method, str(order_code)))
                
                conn.commit()
                cursor.close()
                db_pool.putconn(conn)
                
                print(f">>> Webhook: Premium subscription {order_code} updated successfully")
            except Exception as e:
                print(f">>> Webhook: Error updating premium subscription: {e}")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f">>> PayOS Webhook Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

