"""
Test tracking functionality
"""
from utils.tracking import get_device_info, get_location_from_ip, get_full_tracking_info
from flask import Flask, request

# Create test Flask app
app = Flask(__name__)

def test_device_info():
    """Test device info parsing"""
    print("\n=== Testing Device Info ===")
    
    test_user_agents = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Mobile Safari/537.36"
    ]
    
    with app.test_request_context(headers={'User-Agent': test_user_agents[0]}):
        info = get_device_info()
        print(f"iPhone: {info}")
        assert info['is_mobile'] == True
    
    with app.test_request_context(headers={'User-Agent': test_user_agents[1]}):
        info = get_device_info()
        print(f"Windows PC: {info}")
        assert info['is_pc'] == True
    
    print("✓ Device info test passed!")

def test_location():
    """Test location lookup"""
    print("\n=== Testing Location Lookup ===")
    
    # Test with public IP (Google DNS)
    location = get_location_from_ip("8.8.8.8")
    print(f"Google DNS location: {location}")
    assert location['country'] != 'Unknown'
    
    # Test with local IP
    location = get_location_from_ip("127.0.0.1")
    print(f"Localhost location: {location}")
    assert location['country'] == 'Unknown'
    
    print("✓ Location test passed!")

def test_full_tracking():
    """Test full tracking info"""
    print("\n=== Testing Full Tracking ===")
    
    with app.test_request_context(
        headers={
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)',
            'X-Forwarded-For': '8.8.8.8'
        }
    ):
        info = get_full_tracking_info()
        print(f"Full tracking info: {info}")
        assert 'ip_address' in info
        assert 'device_type' in info
        assert 'country' in info
    
    print("✓ Full tracking test passed!")

if __name__ == '__main__':
    print("Starting tracking tests...")
    
    try:
        test_device_info()
        test_location()
        test_full_tracking()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
