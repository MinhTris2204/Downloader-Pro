"""Auth Controller - Xử lý đăng ký, đăng nhập, OTP, Premium"""
from flask import Blueprint, render_template, request, jsonify, redirect, session, url_for
import time
import sys
import os
import re
import random
import string
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

auth_bp = Blueprint('auth', __name__)

# ===== UTILITY FUNCTIONS =====

def hash_password(password):
    """Hash password using bcrypt"""
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    """Verify password against hash"""
    import bcrypt
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def generate_session_token():
    """Generate secure session token"""
    return secrets.token_hex(32)

def _send_email_task(email, otp, purpose):
    try:
        import smtplib
        import requests
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        smtp_host = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('MAIL_PORT', 587))
        smtp_user = os.environ.get('MAIL_USERNAME', '')
        smtp_pass = os.environ.get('MAIL_PASSWORD', '')
        webhook_url = os.environ.get('GOOGLE_MAIL_WEBHOOK', '')
        
        if not webhook_url and (not smtp_user or not smtp_pass):
            print(f"[AUTH] Email system not configured. OTP for {email}: {otp}")
            return
            
        if purpose == 'verify':
            subject = '🔐 Mã xác thực OTP - Downloader Pro'
            body = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 20px auto; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="background-color: #f8fafc; padding: 30px; border-bottom: 3px solid #3b82f6; text-align: center;">
                    <h1 style="color: #1e293b; margin: 0; font-size: 24px; font-weight: 800;">⬇️ Downloader Pro</h1>
                    <p style="color: #64748b; margin-top: 8px; font-size: 14px;">Xác thực tài khoản của bạn</p>
                </div>
                <div style="padding: 40px; text-align: center;">
                    <p style="color: #334155; font-size: 16px; margin-bottom: 25px;">Chào bạn, mã xác thực OTP của bạn là:</p>
                    <div style="background-color: #f1f5f9; padding: 20px 40px; border-radius: 8px; display: inline-block; border: 1px dashed #3b82f6;">
                        <span style="font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #2563eb;">{otp}</span>
                    </div>
                    <p style="color: #94a3b8; font-size: 14px; margin-top: 25px;">⏱️ Mã này có hiệu lực trong <strong style="color: #1e293b;">5 phút</strong>.</p>
                </div>
                <div style="background-color: #f8fafc; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="color: #64748b; font-size: 12px; margin: 0;">Nếu bạn không yêu cầu mã này, vui lòng bỏ qua email.</p>
                    <p style="color: #94a3b8; font-size: 11px; margin-top: 5px;">&copy; 2026 Downloader Pro Team</p>
                </div>
            </div>
            """
        else:
            subject = '🔑 Đặt lại mật khẩu - Downloader Pro'
            body = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 20px auto; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="background-color: #f8fafc; padding: 30px; border-bottom: 3px solid #0f172a; text-align: center;">
                    <h1 style="color: #1e293b; margin: 0; font-size: 24px; font-weight: 800;">⬇️ Downloader Pro</h1>
                    <p style="color: #64748b; margin-top: 8px; font-size: 14px;">Yêu cầu đặt lại mật khẩu</p>
                </div>
                <div style="padding: 40px; text-align: center;">
                    <p style="color: #334155; font-size: 16px; margin-bottom: 25px;">Mã OTP để đặt lại mật khẩu của bạn là:</p>
                    <div style="background-color: #f1f5f9; padding: 20px 40px; border-radius: 8px; display: inline-block; border: 1px dashed #0f172a;">
                        <span style="font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #0f172a;">{otp}</span>
                    </div>
                    <p style="color: #94a3b8; font-size: 14px; margin-top: 25px;">⏱️ Mã này có hiệu lực trong <strong style="color: #1e293b;">5 phút</strong>.</p>
                </div>
                <div style="background-color: #f8fafc; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="color: #64748b; font-size: 12px; margin: 0;">Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.</p>
                    <p style="color: #94a3b8; font-size: 11px; margin-top: 5px;">&copy; 2026 Downloader Pro Team</p>
                </div>
            </div>
            """
        
        if webhook_url:
            # Bypass SMTP entirely, use Google Apps Script HTTP Webhook
            resp = requests.post(webhook_url, json={
                'to': email,
                'subject': subject,
                'body': body
            }, timeout=15)
            print(f"[AUTH] OTP sent via Webhook to {email}. Status: {resp.status_code}")
            return

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'Downloader Pro <{smtp_user}>'
        msg['To'] = email
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, email, msg.as_string())
        
        print(f"[AUTH] OTP sent via SMTP to {email}")
    except Exception as e:
        print(f"[AUTH ERROR] Failed to send OTP email: {e}")
        import traceback
        traceback.print_exc()

def send_otp_email(email, otp, purpose='verify'):
    """Send OTP via email asynchronously using SocketIO background task"""
    try:
        from app import socketio
        socketio.start_background_task(_send_email_task, email, otp, purpose)
    except Exception as e:
        # Fallback to threading if socketio fails
        import threading
        thread = threading.Thread(target=_send_email_task, args=(email, otp, purpose))
        thread.daemon = True
        thread.start()
    return True

@auth_bp.route('/api/auth/test-email')
def api_test_email():
    """Endpoint để test lỗi gửi email trực tiếp trên trình duyệt"""
    try:
        import smtplib
        import requests
        from email.mime.text import MIMEText
        
        smtp_host = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('MAIL_PORT', 587))
        smtp_user = os.environ.get('MAIL_USERNAME', '')
        smtp_pass = os.environ.get('MAIL_PASSWORD', '')
        webhook_url = os.environ.get('GOOGLE_MAIL_WEBHOOK', '')
        
        # Test Webhook if configured
        if webhook_url:
            test_email = smtp_user or "test@example.com"
            resp = requests.post(webhook_url, json={
                'to': test_email,
                'subject': 'Test Cấu Hình Webhook Email',
                'body': '<p>Đây là email test qua hệ thống Google Apps Script Webhook.</p>'
            }, timeout=15)
            return jsonify({
                'success': True, 
                'message': f'Đã gửi test qua Webhook. Status HTTP: {resp.status_code}', 
                'method': 'webhook'
            })
            
        if not smtp_user or not smtp_pass:
            return jsonify({'success': False, 'error': 'Chưa cấu hình MAIL_USERNAME / MAIL_PASSWORD hoặc GOOGLE_MAIL_WEBHOOK'})
            
        msg = MIMEText('Đây là email test từ hệ thống Railway của bạn.', 'plain', 'utf-8')
        msg['Subject'] = 'Test Cấu Hình Email'
        msg['From'] = f'Downloader Pro <{smtp_user}>'
        msg['To'] = smtp_user
        
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.set_debuglevel(1)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, smtp_user, msg.as_string())
            
        return jsonify({'success': True, 'message': f'Gửi test thành công đến {smtp_user}', 'method': 'smtp'})
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()})

def get_current_user():
    """Get current logged in user from session"""
    from app import db_pool
    user_id = session.get('user_id')
    if not user_id or not db_pool:
        return None
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, email, is_verified, created_at, google_id
            FROM users WHERE id = %s
        """, (user_id,))
        row = cursor.fetchone()
        cursor.close()
        db_pool.putconn(conn)
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'is_verified': row[3],
                'created_at': row[4],
                'google_id': row[5]
            }
    except Exception as e:
        print(f"[AUTH ERROR] Get current user failed: {e}")
    return None

def get_user_premium_info(user_id):
    """Get user premium status and download info"""
    from app import db_pool
    if not db_pool:
        return None
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Get active premium subscription
        cursor.execute("""
            SELECT id, amount, starts_at, expires_at, is_active
            FROM premium_subscriptions 
            WHERE user_id = %s AND is_active = TRUE AND expires_at > NOW()
            ORDER BY expires_at DESC LIMIT 1
        """, (user_id,))
        premium_row = cursor.fetchone()
        
        is_premium = premium_row is not None
        premium_expires = None
        premium_days_left = 0
        
        if premium_row:
            premium_expires = premium_row[3]
            delta = premium_expires - datetime.now()
            premium_days_left = max(0, delta.days)
        
        # Count downloads this week (for free users)
        # Try to get from user_downloads table, if not exists, return 0
        downloads_this_week = 0
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM user_downloads 
                WHERE user_id = %s 
                AND download_time >= DATE_TRUNC('week', CURRENT_DATE)
            """, (str(user_id),))
            downloads_this_week = cursor.fetchone()[0]
        except Exception as e:
            print(f"[AUTH WARNING] user_downloads table not found or error: {e}")
            downloads_this_week = 0
        
        free_downloads_left = max(0, 2 - downloads_this_week)
        
        cursor.close()
        db_pool.putconn(conn)
        
        return {
            'is_premium': is_premium,
            'premium_expires': premium_expires.isoformat() if premium_expires else None,
            'premium_days_left': premium_days_left,
            'downloads_this_week': downloads_this_week,
            'free_downloads_left': free_downloads_left if not is_premium else -1,  # -1 = unlimited
            'max_free_downloads': 2
        }
    except Exception as e:
        print(f"[AUTH ERROR] Get premium info failed: {e}")
        import traceback
        traceback.print_exc()
        # Return default values instead of None to prevent template errors
        return {
            'is_premium': False,
            'premium_expires': None,
            'premium_days_left': 0,
            'downloads_this_week': 0,
            'free_downloads_left': 2,
            'max_free_downloads': 2
        }


# ===== AUTH PAGES =====

@auth_bp.route('/login')
def login_page():
    """Trang đăng nhập"""
    if session.get('user_id'):
        return redirect('/account')
    
    # Google OAuth Client ID for frontend
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
    return render_template('auth/login.html', google_client_id=google_client_id)

@auth_bp.route('/register')
def register_page():
    """Trang đăng ký"""
    if session.get('user_id'):
        return redirect('/account')
    return render_template('auth/register.html')

@auth_bp.route('/forgot-password')
def forgot_password_page():
    """Trang quên mật khẩu"""
    return render_template('auth/forgot_password.html')

@auth_bp.route('/account')
def account_page():
    """Trang tài khoản"""
    try:
        user = get_current_user()
        if not user:
            return redirect('/login')
        
        print(f"[ACCOUNT] Loading account page for user: {user.get('username')}")
        
        premium_info = get_user_premium_info(user['id'])
        
        # Ensure premium_info is always a dict
        if not premium_info:
            premium_info = {
                'is_premium': False,
                'premium_expires': None,
                'premium_days_left': 0,
                'downloads_this_month': 0,
                'free_downloads_left': 2,
                'max_free_downloads': 2
            }
        
        print(f"[ACCOUNT] Premium info: {premium_info}")
        
        google_client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
        return render_template('auth/account.html', user=user, premium_info=premium_info, google_client_id=google_client_id)
    except Exception as e:
        print(f"[ACCOUNT ERROR] Failed to load account page: {e}")
        import traceback
        traceback.print_exc()
        return f"Error loading account page: {str(e)}", 500


# ===== AUTH API =====

@auth_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    """API đăng ký tài khoản"""
    try:
        from app import db_pool
        data = request.get_json(silent=True) or {}
        
        username = data.get('username', '').strip().lower()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password:
            return jsonify({'success': False, 'error': 'Vui lòng điền đầy đủ thông tin'}), 200
        
        if len(username) < 3 or len(username) > 30:
            return jsonify({'success': False, 'error': 'Tên đăng nhập phải từ 3-30 ký tự'}), 200
        
        if not re.match(r'^[a-z0-9_]+$', username):
            return jsonify({'success': False, 'error': 'Tên đăng nhập chỉ chứa chữ thường, số và dấu _'}), 200
        
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'success': False, 'error': 'Email không hợp lệ'}), 200
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Mật khẩu phải có ít nhất 6 ký tự'}), 200
        
        if password != confirm_password:
            return jsonify({'success': False, 'error': 'Mật khẩu xác nhận không khớp'}), 200
        
        if not db_pool:
            return jsonify({'success': False, 'error': 'Lỗi hệ thống'}), 500
        
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Check existing username
        cursor.execute("SELECT id, is_verified FROM users WHERE username = %s", (username,))
        existing_username = cursor.fetchone()
        
        if existing_username and existing_username[1]:
            cursor.close()
            db_pool.putconn(conn)
            return jsonify({'success': False, 'error': 'Tên đăng nhập đã tồn tại'}), 200
            
        # Check existing email
        cursor.execute("SELECT id, is_verified FROM users WHERE email = %s", (email,))
        existing_email = cursor.fetchone()
        
        if existing_email and existing_email[1]:
            cursor.close()
            db_pool.putconn(conn)
            return jsonify({'success': False, 'error': 'Email đã được sử dụng và xác thực'}), 200
            
        # If unverified account exists with this username or email, delete it so user can register again
        if (existing_username and not existing_username[1]) or (existing_email and not existing_email[1]):
            cursor.execute("DELETE FROM users WHERE (username = %s OR email = %s) AND is_verified = FALSE", (username, email))
        
        # Create user (unverified)
        password_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, is_verified, created_at)
            VALUES (%s, %s, %s, FALSE, CURRENT_TIMESTAMP)
            RETURNING id
        """, (username, email, password_hash))
        
        user_id = cursor.fetchone()[0]
        
        # Generate and save OTP
        otp = generate_otp()
        cursor.execute("""
            INSERT INTO otp_codes (user_id, email, otp_code, purpose, expires_at, created_at)
            VALUES (%s, %s, %s, 'verify', NOW() + INTERVAL '5 minutes', CURRENT_TIMESTAMP)
        """, (user_id, email, otp))
        
        conn.commit()
        cursor.close()
        db_pool.putconn(conn)
        
        # Send OTP email
        send_otp_email(email, otp, 'verify')
        
        # Store user_id temporarily for OTP verification
        session['pending_user_id'] = user_id
        session['pending_email'] = email
        
        return jsonify({
            'success': True,
            'message': 'Đã gửi mã OTP đến email của bạn',
            'need_otp': True
        })
        
    except Exception as e:
        print(f"[AUTH ERROR] Register failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Lỗi hệ thống, vui lòng thử lại'}), 500


@auth_bp.route('/api/auth/verify-otp', methods=['POST'])
def api_verify_otp():
    """API xác thực OTP"""
    try:
        from app import db_pool
        data = request.get_json(silent=True) or {}
        
        otp = data.get('otp', '').strip()
        purpose = data.get('purpose', 'verify')
        
        if not otp or len(otp) != 6:
            return jsonify({'success': False, 'error': 'Mã OTP không hợp lệ'}), 200
        
        if purpose == 'verify':
            user_id = session.get('pending_user_id')
            email = session.get('pending_email')
        else:
            user_id = session.get('reset_user_id')
            email = session.get('reset_email')
        
        if not user_id or not email:
            return jsonify({'success': False, 'error': 'Phiên làm việc hết hạn. Vui lòng thử lại.'}), 200
        
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Verify OTP
        cursor.execute("""
            SELECT id FROM otp_codes 
            WHERE user_id = %s AND email = %s AND otp_code = %s 
            AND purpose = %s AND is_used = FALSE AND expires_at > NOW()
            ORDER BY created_at DESC LIMIT 1
        """, (user_id, email, otp, purpose))
        
        otp_row = cursor.fetchone()
        if not otp_row:
            cursor.close()
            db_pool.putconn(conn)
            return jsonify({'success': False, 'error': 'Mã OTP không đúng hoặc đã hết hạn'}), 200
        
        # Mark OTP as used
        cursor.execute("UPDATE otp_codes SET is_used = TRUE WHERE id = %s", (otp_row[0],))
        
        if purpose == 'verify':
            # Mark user as verified
            cursor.execute("UPDATE users SET is_verified = TRUE WHERE id = %s", (user_id,))
            
            # Get username for session
            cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
            username = cursor.fetchone()[0]
            
            # Auto login after verification
            session.pop('pending_user_id', None)
            session.pop('pending_email', None)
            session.permanent = True  # Make session persistent
            session['user_id'] = user_id
            session['username'] = username
            
            conn.commit()
            cursor.close()
            db_pool.putconn(conn)
            
            return jsonify({
                'success': True,
                'message': 'Xác thực thành công! Chào mừng bạn đến Downloader Pro.',
                'redirect': '/'
            })
        else:
            # Password reset - allow changing password
            session['reset_verified'] = True
            
            conn.commit()
            cursor.close()
            db_pool.putconn(conn)
            
            return jsonify({
                'success': True,
                'message': 'Xác thực OTP thành công. Bạn có thể đặt mật khẩu mới.',
                'can_reset': True
            })
        
    except Exception as e:
        print(f"[AUTH ERROR] Verify OTP failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Lỗi hệ thống'}), 500


@auth_bp.route('/api/auth/resend-otp', methods=['POST'])
def api_resend_otp():
    """API gửi lại OTP"""
    try:
        from app import db_pool
        data = request.get_json(silent=True) or {}
        purpose = data.get('purpose', 'verify')
        
        if purpose == 'verify':
            user_id = session.get('pending_user_id')
            email = session.get('pending_email')
        else:
            user_id = session.get('reset_user_id')
            email = session.get('reset_email')
        
        if not user_id or not email:
            return jsonify({'success': False, 'error': 'Phiên làm việc hết hạn'}), 200
        
        # Rate limit - max 1 OTP per 60 seconds
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT created_at FROM otp_codes 
            WHERE user_id = %s AND purpose = %s 
            ORDER BY created_at DESC LIMIT 1
        """, (user_id, purpose))
        
        last_otp = cursor.fetchone()
        if last_otp:
            time_diff = (datetime.now() - last_otp[0]).total_seconds()
            if time_diff < 60:
                cursor.close()
                db_pool.putconn(conn)
                wait = int(60 - time_diff)
                return jsonify({'success': False, 'error': f'Vui lòng đợi {wait} giây trước khi gửi lại'}), 429
        
        # Generate new OTP
        otp = generate_otp()
        cursor.execute("""
            INSERT INTO otp_codes (user_id, email, otp_code, purpose, expires_at, created_at)
            VALUES (%s, %s, %s, %s, NOW() + INTERVAL '5 minutes', CURRENT_TIMESTAMP)
        """, (user_id, email, otp, purpose))
        
        conn.commit()
        cursor.close()
        db_pool.putconn(conn)
        
        send_otp_email(email, otp, purpose)
        
        return jsonify({'success': True, 'message': 'Đã gửi lại mã OTP'})
        
    except Exception as e:
        print(f"[AUTH ERROR] Resend OTP failed: {e}")
        return jsonify({'success': False, 'error': 'Lỗi hệ thống'}), 500


@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    """API đăng nhập"""
    try:
        from app import db_pool
        data = request.get_json(silent=True) or {}
        
        login_id = data.get('login_id', '').strip().lower()
        password = data.get('password', '')
        
        if not login_id or not password:
            return jsonify({'success': False, 'error': 'Vui lòng nhập đầy đủ thông tin'}), 200
        
        if not db_pool:
            return jsonify({'success': False, 'error': 'Lỗi hệ thống'}), 500
        
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Login by username or email
        cursor.execute("""
            SELECT id, username, email, password_hash, is_verified 
            FROM users 
            WHERE username = %s OR email = %s
        """, (login_id, login_id))
        
        user = cursor.fetchone()
        cursor.close()
        db_pool.putconn(conn)
        
        if not user:
            return jsonify({'success': False, 'error': 'Tài khoản không tồn tại'}), 200
        
        user_id, username, email, password_hash, is_verified = user
        
        # Check if user registered via Google (no password)
        if not password_hash:
            return jsonify({'success': False, 'error': 'Tài khoản này đăng nhập bằng Google. Vui lòng dùng nút "Đăng nhập với Google".'}), 200
        
        if not check_password(password, password_hash):
            return jsonify({'success': False, 'error': 'Mật khẩu không đúng'}), 200
        
        if not is_verified:
            # Resend OTP for unverified users
            session['pending_user_id'] = user_id
            session['pending_email'] = email
            
            otp = generate_otp()
            conn = db_pool.getconn()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO otp_codes (user_id, email, otp_code, purpose, expires_at, created_at)
                VALUES (%s, %s, %s, 'verify', NOW() + INTERVAL '5 minutes', CURRENT_TIMESTAMP)
            """, (user_id, email, otp))
            conn.commit()
            cursor.close()
            db_pool.putconn(conn)
            
            send_otp_email(email, otp, 'verify')
            
            return jsonify({
                'success': False,
                'error': 'Tài khoản chưa xác thực email. Đã gửi lại mã OTP.',
                'need_otp': True,
                'purpose': 'verify'
            }), 200
        
        # Login success
        session.permanent = True  # Make session persistent
        session['user_id'] = user_id
        session['username'] = username
        
        # Debug logging
        print(f"[LOGIN DEBUG] Session set for user {username} (ID: {user_id})")
        print(f"[LOGIN DEBUG] Session data after login: {dict(session)}")
        print(f"[LOGIN DEBUG] Session permanent: {session.permanent}")
        
        return jsonify({
            'success': True,
            'message': f'Chào mừng, {username}!',
            'redirect': '/'
        })
        
    except Exception as e:
        print(f"[AUTH ERROR] Login failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Lỗi hệ thống'}), 500


@auth_bp.route('/api/auth/google', methods=['POST'])
def api_google_login():
    """API đăng nhập bằng Google"""
    try:
        from app import db_pool
        data = request.get_json(silent=True) or {}
        
        credential = data.get('credential', '')
        
        if not credential:
            return jsonify({'success': False, 'error': 'Token Google không hợp lệ'}), 200
        
        # Decode Google JWT token
        import jwt
        
        google_client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
        
        # Decode without verification first (we'll verify the issuer manually)
        try:
            # For Google Sign-In, we need to verify the token
            # Use Google's tokeninfo endpoint for verification
            verify_url = f'https://oauth2.googleapis.com/tokeninfo?id_token={credential}'
            import requests as http_req
            resp = http_req.get(verify_url, timeout=10)
            
            if resp.status_code != 200:
                return jsonify({'success': False, 'error': 'Token Google không hợp lệ'}), 200
            
            payload = resp.json()
            
            # Verify audience
            if payload.get('aud') != google_client_id:
                return jsonify({'success': False, 'error': 'Token không hợp lệ cho ứng dụng này'}), 200
            
        except Exception as e:
            print(f"[AUTH ERROR] Google token verification failed: {e}")
            return jsonify({'success': False, 'error': 'Không thể xác thực Google token'}), 200
        
        google_id = payload.get('sub', '')
        email = payload.get('email', '').lower()
        name = payload.get('name', '')
        
        if not google_id or not email:
            return jsonify({'success': False, 'error': 'Không lấy được thông tin Google'}), 200
        
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Check if user exists with this Google ID
        cursor.execute("SELECT id, username FROM users WHERE google_id = %s", (google_id,))
        user = cursor.fetchone()
        
        if user:
            # Existing Google user - login
            session.permanent = True  # Make session persistent
            session['user_id'] = user[0]
            session['username'] = user[1]
            cursor.close()
            db_pool.putconn(conn)
            return jsonify({
                'success': True,
                'message': f'Chào mừng, {user[1]}!',
                'redirect': '/'
            })
        
        # Check if email already exists (linking account)
        cursor.execute("SELECT id, username FROM users WHERE email = %s", (email,))
        existing = cursor.fetchone()
        
        if existing:
            # Link Google to existing account
            cursor.execute("UPDATE users SET google_id = %s, is_verified = TRUE WHERE id = %s", 
                         (google_id, existing[0]))
            conn.commit()
            session.permanent = True  # Make session persistent
            session['user_id'] = existing[0]
            session['username'] = existing[1]
            cursor.close()
            db_pool.putconn(conn)
            return jsonify({
                'success': True,
                'message': f'Đã liên kết Google. Chào mừng, {existing[1]}!',
                'redirect': '/'
            })
        
        # New user - create account
        username = email.split('@')[0].lower()
        username = re.sub(r'[^a-z0-9_]', '', username)[:20]
        
        # Ensure unique username
        base_username = username
        counter = 1
        while True:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if not cursor.fetchone():
                break
            username = f"{base_username}{counter}"
            counter += 1
        
        cursor.execute("""
            INSERT INTO users (username, email, google_id, is_verified, created_at)
            VALUES (%s, %s, %s, TRUE, CURRENT_TIMESTAMP)
            RETURNING id
        """, (username, email, google_id))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        db_pool.putconn(conn)
        
        session.permanent = True  # Make session persistent
        session['user_id'] = user_id
        session['username'] = username
        
        return jsonify({
            'success': True,
            'message': f'Đăng ký thành công! Chào mừng, {username}!',
            'redirect': '/'
        })
        
    except Exception as e:
        print(f"[AUTH ERROR] Google login failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Lỗi đăng nhập Google'}), 500


@auth_bp.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """API đăng xuất"""
    session.pop('user_id', None)
    session.pop('pending_user_id', None)
    session.pop('pending_email', None)
    session.pop('reset_user_id', None)
    session.pop('reset_email', None)
    session.pop('reset_verified', None)
    return jsonify({'success': True, 'message': 'Đã đăng xuất', 'redirect': '/'})


@auth_bp.route('/api/auth/forgot-password', methods=['POST'])
def api_forgot_password():
    """API quên mật khẩu - gửi OTP"""
    try:
        from app import db_pool
        data = request.get_json(silent=True) or {}
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'success': False, 'error': 'Vui lòng nhập email'}), 200
        
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            db_pool.putconn(conn)
            return jsonify({'success': False, 'error': 'Email không tồn tại trong hệ thống'}), 200
        
        user_id = user[0]
        
        # Generate OTP
        otp = generate_otp()
        cursor.execute("""
            INSERT INTO otp_codes (user_id, email, otp_code, purpose, expires_at, created_at)
            VALUES (%s, %s, %s, 'reset', NOW() + INTERVAL '5 minutes', CURRENT_TIMESTAMP)
        """, (user_id, email, otp))
        
        conn.commit()
        cursor.close()
        db_pool.putconn(conn)
        
        send_otp_email(email, otp, 'reset')
        
        session['reset_user_id'] = user_id
        session['reset_email'] = email
        
        return jsonify({
            'success': True,
            'message': 'Đã gửi mã OTP đến email của bạn',
            'need_otp': True
        })
        
    except Exception as e:
        print(f"[AUTH ERROR] Forgot password failed: {e}")
        return jsonify({'success': False, 'error': 'Lỗi hệ thống'}), 500


@auth_bp.route('/api/auth/reset-password', methods=['POST'])
def api_reset_password():
    """API đặt lại mật khẩu"""
    try:
        from app import db_pool
        data = request.get_json(silent=True) or {}
        
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        if not session.get('reset_verified'):
            return jsonify({'success': False, 'error': 'Chưa xác thực OTP'}), 200
        
        user_id = session.get('reset_user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Phiên làm việc hết hạn'}), 200
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': 'Mật khẩu phải có ít nhất 6 ký tự'}), 200
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'error': 'Mật khẩu xác nhận không khớp'}), 200
        
        password_hash = hash_password(new_password)
        
        conn = db_pool.getconn()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (password_hash, user_id))
        conn.commit()
        cursor.close()
        db_pool.putconn(conn)
        
        # Clear session
        session.pop('reset_user_id', None)
        session.pop('reset_email', None)
        session.pop('reset_verified', None)
        
        return jsonify({
            'success': True,
            'message': 'Đổi mật khẩu thành công! Vui lòng đăng nhập lại.',
            'redirect': '/login'
        })
        
    except Exception as e:
        print(f"[AUTH ERROR] Reset password failed: {e}")
        return jsonify({'success': False, 'error': 'Lỗi hệ thống'}), 500


@auth_bp.route('/api/auth/me')
def api_get_me():
    """API lấy thông tin user hiện tại"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'logged_in': False})
    
    premium_info = get_user_premium_info(user['id'])
    
    return jsonify({
        'success': True,
        'logged_in': True,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'is_verified': user['is_verified'],
            'has_google': user['google_id'] is not None
        },
        'premium': premium_info
    })


@auth_bp.route('/api/auth/check-download', methods=['POST'])
def api_check_download():
    """API kiểm tra quyền tải xuống"""
    from app import db_pool
    
    user = get_current_user()
    
    if not user:
        # Require login - no guest downloads allowed
        return jsonify({
            'success': False,
            'can_download': False,
            'reason': 'require_login',
            'message': 'Vui lòng đăng nhập để tải xuống. Đăng ký miễn phí để nhận 2 lượt tải mỗi tuần!',
            'logged_in': False
        })
    
    # Logged in user
    premium_info = get_user_premium_info(user['id'])
    
    if premium_info and premium_info['is_premium']:
        return jsonify({
            'success': True,
            'can_download': True,
            'is_premium': True,
            'premium_days_left': premium_info['premium_days_left'],
            'logged_in': True
        })
    
    # Check if user has exceeded free download limit (2 per week)
    if premium_info and premium_info['downloads_this_week'] >= 2:
        return jsonify({
            'success': False,
            'can_download': False,
            'reason': 'limit_reached',
            'message': 'Bạn đã hết 2 lượt tải miễn phí trong tuần này. Nâng cấp Premium để tải không giới hạn!',
            'downloads_used': premium_info['downloads_this_week'],
            'max_free': 2,
            'is_premium': False,
            'logged_in': True
        })
    
    return jsonify({
        'success': True,
        'can_download': True,
        'downloads_left': premium_info['free_downloads_left'] if premium_info else 2,
        'max_free': 2,
        'is_premium': False,
        'logged_in': True
    })


@auth_bp.route('/api/auth/record-download', methods=['POST'])
def api_record_download():
    """API ghi nhận lượt tải"""
    from app import db_pool
    
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    platform = data.get('platform', 'unknown')
    
    if user:
        user_id = str(user['id'])
    else:
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        user_id = hashlib.md5(ip_address.encode()).hexdigest()
    
    if db_pool:
        try:
            conn = db_pool.getconn()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_downloads (user_id, platform, download_time)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
            """, (user_id, platform))
            conn.commit()
            cursor.close()
            db_pool.putconn(conn)
        except Exception as e:
            print(f"[AUTH ERROR] Record download failed: {e}")
    
    return jsonify({'success': True})


# ===== PREMIUM API =====

@auth_bp.route('/api/premium/purchase', methods=['POST'])
def api_purchase_premium():
    """API mua Premium - tạo link thanh toán PayOS"""
    try:
        from app import db_pool
        from config.payos_config import (
            PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY,
            PAYOS_RETURN_URL, PAYOS_CANCEL_URL
        )
        from utils.payos_helper import PayOS
        
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Vui lòng đăng nhập để mua Premium'}), 401
        
        data = request.get_json(silent=True) or {}
        amount = int(data.get('amount', 0))
        
        if amount < 1000:
            return jsonify({'success': False, 'error': 'Số tiền tối thiểu là 1,000 VNĐ'}), 200
        
        # Create PayOS instance
        if not PAYOS_CLIENT_ID or not PAYOS_API_KEY or not PAYOS_CHECKSUM_KEY:
            return jsonify({'success': False, 'error': 'Hệ thống thanh toán chưa được cấu hình'}), 500
        
        payos = PayOS(PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY)
        
        order_code = int(time.time())
        
        # Get IP
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        user_agent = request.headers.get('User-Agent', '')
        
        # Save donation record with premium flag
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Create pending premium subscription
        from datetime import datetime, timedelta
        starts_at = datetime.now()
        expires_at = datetime.now() + timedelta(days=30)
        
        cursor.execute("""
            INSERT INTO premium_subscriptions 
            (user_id, order_code, amount, starts_at, expires_at, is_active,
             payment_status, donor_email, ip_address, user_agent, created_at)
            VALUES (%s, %s, %s, %s, %s, FALSE, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """, (
            user['id'], str(order_code), amount, starts_at, expires_at,
            'pending', user['email'], ip_address, user_agent
        ))
        
        conn.commit()
        cursor.close()
        db_pool.putconn(conn)
        
        # Build return URL with premium flag
        base_url = os.environ.get('BASE_URL', request.host_url.rstrip('/'))
        return_url = f"{base_url}/premium/return"
        cancel_url = f"{base_url}/premium/cancel"
        
        # Format description
        if amount >= 1000000:
            amount_str = f"{amount//1000000}M"
        elif amount >= 1000:
            amount_str = f"{amount//1000}K"
        else:
            amount_str = str(amount)
        description = f"Premium {amount_str}"
        
        # Create payment link
        result = payos.create_payment_link(
            order_code=order_code,
            amount=amount,
            description=description,
            return_url=return_url,
            cancel_url=cancel_url,
            buyer_name=user['username'],
            buyer_email=user['email']
        )
        
        if 'error' in result:
            return jsonify({'success': False, 'error': result.get('error', 'Lỗi tạo link thanh toán')}), 500
        
        if result.get('code') != '00':
            return jsonify({'success': False, 'error': f"PayOS: {result.get('desc', 'Lỗi')}"}), 500
        
        checkout_data = result.get('data')
        if not checkout_data:
            return jsonify({'success': False, 'error': 'Không nhận được dữ liệu'}), 500
        
        checkout_url = checkout_data.get('checkoutUrl', '')
        
        return jsonify({
            'success': True,
            'checkoutUrl': checkout_url,
            'orderCode': order_code
        })
        
    except Exception as e:
        print(f"[AUTH ERROR] Purchase premium failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/premium/return')
def premium_return():
    """Xử lý khi thanh toán premium thành công"""
    from app import db_pool
    
    order_code = request.args.get('orderCode', '')
    
    if db_pool and order_code:
        try:
            conn = db_pool.getconn()
            cursor = conn.cursor()
            
            # Update premium subscription to active
            cursor.execute("""
                UPDATE premium_subscriptions 
                SET payment_status = 'success',
                    is_active = TRUE,
                    paid_at = CURRENT_TIMESTAMP
                WHERE order_code = %s
            """, (order_code,))
            
            conn.commit()
            cursor.close()
            db_pool.putconn(conn)
            print(f">>> Premium subscription {order_code} activated")
        except Exception as e:
            print(f">>> Error processing premium return: {e}")
            import traceback
            traceback.print_exc()
    
    return redirect('/account?premium=success')


@auth_bp.route('/premium/cancel')
def premium_cancel():
    """Xử lý khi hủy thanh toán premium"""
    from app import db_pool
    
    order_code = request.args.get('orderCode', '')
    
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
        except Exception as e:
            print(f">>> Error processing premium cancel: {e}")
    
    return redirect('/account?premium=cancel')
