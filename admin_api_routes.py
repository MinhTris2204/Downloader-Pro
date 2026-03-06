# Admin API Routes for User and Premium Management
# Add these routes to app.py after the admin_dashboard route

"""
# ==================== ADMIN API: USERS MANAGEMENT ====================

@app.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    '''Get all users with filters'''
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Get filters
        user_type = request.args.get('type', 'all')
        search = request.args.get('search', '').strip()
        
        # Base query
        query = '''
            SELECT 
                u.id,
                u.username,
                u.email,
                u.google_id,
                u.created_at,
                u.is_verified,
                CASE 
                    WHEN ps.id IS NOT NULL AND ps.expires_at > NOW() THEN true 
                    ELSE false 
                END as is_premium,
                ps.expires_at as premium_expires,
                (SELECT COUNT(*) FROM user_downloads WHERE user_id = u.id) as total_downloads
            FROM users u
            LEFT JOIN premium_subscriptions ps ON u.id = ps.user_id AND ps.is_active = true AND ps.expires_at > NOW()
            WHERE 1=1
        '''
        
        params = []
        
        # Apply filters
        if search:
            query += ' AND (u.username ILIKE %s OR u.email ILIKE %s)'
            params.extend([f'%{search}%', f'%{search}%'])
        
        if user_type == 'premium':
            query += ' AND ps.id IS NOT NULL AND ps.expires_at > NOW()'
        elif user_type == 'free':
            query += ' AND (ps.id IS NULL OR ps.expires_at <= NOW())'
        elif user_type == 'google':
            query += ' AND u.google_id IS NOT NULL'
        
        query += ' ORDER BY u.created_at DESC LIMIT 100'
        
        cursor.execute(query, params)
        users = cursor.fetchall()
        
        # Get stats
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(DISTINCT u.id) 
            FROM users u
            JOIN premium_subscriptions ps ON u.id = ps.user_id
            WHERE ps.is_active = true AND ps.expires_at > NOW()
        ''')
        premium_users = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE created_at >= CURRENT_DATE
        ''')
        users_today = cursor.fetchone()[0]
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({
            'success': True,
            'users': [{
                'id': u[0],
                'username': u[1],
                'email': u[2],
                'has_google': u[3] is not None,
                'created_at': u[4].isoformat() if u[4] else None,
                'is_verified': u[5],
                'is_premium': u[6],
                'premium_expires': u[7].isoformat() if u[7] else None,
                'total_downloads': u[8] or 0
            } for u in users],
            'stats': {
                'total': total_users,
                'premium': premium_users,
                'today': users_today,
                'online': 0  # Will be updated from Socket.IO
            }
        })
        
    except Exception as e:
        print(f'[ERROR] Admin get users: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    '''Delete a user'''
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({'success': True, 'message': 'Đã xóa người dùng'})
        
    except Exception as e:
        print(f'[ERROR] Admin delete user: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/users/<int:user_id>/toggle-premium', methods=['POST'])
def admin_toggle_user_premium(user_id):
    '''Toggle premium status for a user'''
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        data = request.get_json()
        days = data.get('days', 30)
        
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        # Check if user has active premium
        cursor.execute('''
            SELECT id, expires_at FROM premium_subscriptions 
            WHERE user_id = %s AND is_active = true AND expires_at > NOW()
            ORDER BY expires_at DESC LIMIT 1
        ''', (user_id,))
        
        existing = cursor.fetchone()
        
        if existing:
            # Extend existing premium
            cursor.execute('''
                UPDATE premium_subscriptions 
                SET expires_at = expires_at + INTERVAL '%s days'
                WHERE id = %s
            ''', (days, existing[0]))
        else:
            # Create new premium subscription
            cursor.execute('''
                INSERT INTO premium_subscriptions 
                (user_id, amount, starts_at, expires_at, is_active, order_code)
                VALUES (%s, 0, NOW(), NOW() + INTERVAL '%s days', true, 'ADMIN_GRANT')
            ''', (user_id, days))
        
        conn.commit()
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({'success': True, 'message': f'Đã thêm {days} ngày Premium'})
        
    except Exception as e:
        print(f'[ERROR] Admin toggle premium: {e}')
        return jsonify({'error': str(e)}), 500


# ==================== ADMIN API: PREMIUM MANAGEMENT ====================

@app.route('/api/admin/premium', methods=['GET'])
def admin_get_premium_subscriptions():
    '''Get all premium subscriptions'''
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        status_filter = request.args.get('status', 'all')
        
        query = '''
            SELECT 
                ps.id,
                ps.user_id,
                u.username,
                u.email,
                ps.order_code,
                ps.amount,
                ps.starts_at,
                ps.expires_at,
                ps.is_active,
                ps.created_at,
                CASE 
                    WHEN ps.expires_at > NOW() THEN 'active'
                    ELSE 'expired'
                END as status
            FROM premium_subscriptions ps
            JOIN users u ON ps.user_id = u.id
            WHERE 1=1
        '''
        
        if status_filter == 'active':
            query += ' AND ps.is_active = true AND ps.expires_at > NOW()'
        elif status_filter == 'expiring':
            query += ' AND ps.is_active = true AND ps.expires_at > NOW() AND ps.expires_at <= NOW() + INTERVAL \'7 days\''
        elif status_filter == 'expired':
            query += ' AND ps.expires_at <= NOW()'
        
        query += ' ORDER BY ps.created_at DESC LIMIT 200'
        
        cursor.execute(query)
        subscriptions = cursor.fetchall()
        
        # Get stats
        cursor.execute('''
            SELECT COUNT(*), COALESCE(SUM(amount), 0)
            FROM premium_subscriptions 
            WHERE is_active = true AND expires_at > NOW()
        ''')
        active_count, total_revenue = cursor.fetchone()
        
        cursor.execute('''
            SELECT COUNT(*) FROM premium_subscriptions 
            WHERE is_active = true AND expires_at > NOW() AND expires_at <= NOW() + INTERVAL '7 days'
        ''')
        expiring_count = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM premium_subscriptions 
            WHERE expires_at <= NOW()
        ''')
        expired_count = cursor.fetchone()[0]
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({
            'success': True,
            'subscriptions': [{
                'id': s[0],
                'user_id': s[1],
                'username': s[2],
                'email': s[3],
                'order_code': s[4],
                'amount': s[5],
                'starts_at': s[6].isoformat() if s[6] else None,
                'expires_at': s[7].isoformat() if s[7] else None,
                'is_active': s[8],
                'created_at': s[9].isoformat() if s[9] else None,
                'status': s[10]
            } for s in subscriptions],
            'stats': {
                'active': active_count,
                'revenue': total_revenue,
                'expiring': expiring_count,
                'expired': expired_count
            }
        })
        
    except Exception as e:
        print(f'[ERROR] Admin get premium: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/premium/<int:subscription_id>', methods=['DELETE'])
def admin_delete_premium(subscription_id):
    '''Delete a premium subscription'''
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM premium_subscriptions WHERE id = %s', (subscription_id,))
        conn.commit()
        
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({'success': True, 'message': 'Đã xóa gói Premium'})
        
    except Exception as e:
        print(f'[ERROR] Admin delete premium: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/premium/<int:subscription_id>/extend', methods=['POST'])
def admin_extend_premium(subscription_id):
    '''Extend premium subscription'''
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not db_pool:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        data = request.get_json()
        days = data.get('days', 30)
        
        conn = db_pool.getconn()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE premium_subscriptions 
            SET expires_at = expires_at + INTERVAL '%s days',
                is_active = true
            WHERE id = %s
        ''', (days, subscription_id))
        
        conn.commit()
        cursor.close()
        db_pool.putconn(conn)
        
        return jsonify({'success': True, 'message': f'Đã gia hạn thêm {days} ngày'})
        
    except Exception as e:
        print(f'[ERROR] Admin extend premium: {e}')
        return jsonify({'error': str(e)}), 500
"""
