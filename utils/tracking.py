"""
Tracking utilities - Thu thập thông tin người dùng
"""
import requests
from flask import request
from user_agents import parse

def get_client_ip():
    """Lấy IP thực của client (xử lý proxy/Railway)"""
    # Railway/Proxy headers
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr or 'unknown'

def get_device_info():
    """Lấy thông tin thiết bị từ User-Agent"""
    user_agent_string = request.headers.get('User-Agent', '')
    user_agent = parse(user_agent_string)
    
    return {
        'device_type': user_agent.device.family,  # Mobile/Tablet/PC
        'os': f"{user_agent.os.family} {user_agent.os.version_string}",
        'browser': f"{user_agent.browser.family} {user_agent.browser.version_string}",
        'is_mobile': user_agent.is_mobile,
        'is_tablet': user_agent.is_tablet,
        'is_pc': user_agent.is_pc,
        'user_agent': user_agent_string[:200]  # Giới hạn độ dài
    }

def get_location_from_ip(ip_address):
    """Lấy vị trí từ IP (sử dụng API miễn phí)"""
    if ip_address == 'unknown' or ip_address.startswith('127.') or ip_address.startswith('192.168.'):
        return {
            'country': 'Unknown',
            'country_code': 'XX',
            'region': 'Unknown',
            'city': 'Unknown',
            'timezone': 'Unknown'
        }
    
    try:
        # Sử dụng ip-api.com (miễn phí, 45 requests/phút)
        response = requests.get(
            f'http://ip-api.com/json/{ip_address}',
            timeout=3
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'country': data.get('country', 'Unknown'),
                    'country_code': data.get('countryCode', 'XX'),
                    'region': data.get('regionName', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'timezone': data.get('timezone', 'Unknown'),
                    'lat': data.get('lat'),
                    'lon': data.get('lon')
                }
    except Exception as e:
        print(f"[WARNING] Location lookup failed: {e}")
    
    return {
        'country': 'Unknown',
        'country_code': 'XX',
        'region': 'Unknown',
        'city': 'Unknown',
        'timezone': 'Unknown'
    }

def get_full_tracking_info():
    """Lấy tất cả thông tin tracking"""
    ip = get_client_ip()
    device = get_device_info()
    location = get_location_from_ip(ip)
    
    return {
        'ip_address': ip,
        'device_type': device['device_type'],
        'os': device['os'],
        'browser': device['browser'],
        'is_mobile': device['is_mobile'],
        'is_tablet': device['is_tablet'],
        'is_pc': device['is_pc'],
        'user_agent': device['user_agent'],
        'country': location['country'],
        'country_code': location['country_code'],
        'region': location['region'],
        'city': location['city'],
        'timezone': location['timezone'],
        'latitude': location.get('lat'),
        'longitude': location.get('lon')
    }
