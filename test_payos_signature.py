"""Test PayOS signature generation"""
import hmac
import hashlib
import json

# Test data
checksum_key = "15b90df2d3ca3cfb"  # First 16 chars from log

test_data = {
    "amount": 10000,
    "buyerName": "Anonymous",
    "cancelUrl": "https://downloaderpro.io.vn/payos/cancel",
    "description": "Donate 10,000 VND",
    "orderCode": 1770909487,
    "returnUrl": "https://downloaderpro.io.vn/payos/return"
}

def create_signature_v1(data, key):
    """Version 1: No encoding"""
    sorted_keys = sorted(data.keys())
    query_parts = []
    
    for k in sorted_keys:
        value = data[k]
        if isinstance(value, bool):
            value_str = 'true' if value else 'false'
        elif isinstance(value, (int, float)):
            value_str = str(value)
        else:
            value_str = str(value)
        
        query_parts.append(f"{k}={value_str}")
    
    query_str = "&".join(query_parts)
    print(f"V1 Query: {query_str}")
    
    signature = hmac.new(
        key.encode("utf-8"),
        msg=query_str.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return signature

def create_signature_v2(data, key):
    """Version 2: Only specific fields for payment request"""
    # Theo docs, payment request signature chỉ dùng 5 fields này
    fields_for_signature = ["amount", "cancelUrl", "description", "orderCode", "returnUrl"]
    
    sorted_keys = sorted(fields_for_signature)
    query_parts = []
    
    for k in sorted_keys:
        if k in data:
            value = data[k]
            if isinstance(value, (int, float)):
                value_str = str(value)
            else:
                value_str = str(value)
            
            query_parts.append(f"{k}={value_str}")
    
    query_str = "&".join(query_parts)
    print(f"V2 Query (5 fields only): {query_str}")
    
    signature = hmac.new(
        key.encode("utf-8"),
        msg=query_str.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return signature

print("Testing PayOS Signature Generation")
print("=" * 60)
print(f"Checksum Key (first 16): {checksum_key}")
print(f"Test Data: {json.dumps(test_data, indent=2)}")
print("=" * 60)

sig1 = create_signature_v1(test_data, checksum_key)
print(f"Signature V1 (all fields): {sig1}")
print()

sig2 = create_signature_v2(test_data, checksum_key)
print(f"Signature V2 (5 fields): {sig2}")
print()

print("=" * 60)
print("Note: Checksum key in test is only first 16 chars")
print("Real signature will be different with full 64-char key")
