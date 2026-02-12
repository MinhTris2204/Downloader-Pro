"""PayOS Helper - Simplified version
Xử lý API calls cho PayOS"""
import hmac
import hashlib
import json
import requests
from typing import Dict, Any

class PayOS:
    def __init__(self, client_id: str, api_key: str, checksum_key: str):
        self.client_id = client_id
        self.api_key = api_key
        self.checksum_key = checksum_key
        self.api_url = "https://api-merchant.payos.vn/v2/payment-requests"
    
    def create_payment_link(self,
                           order_code: int,
                           amount: int,
                           description: str,
                           return_url: str,
                           cancel_url: str,
                           buyer_name: str = None,
                           buyer_email: str = None,
                           ) -> Dict[str, Any]:
        """Tạo link thanh toán PayOS"""
        payload = {
            "orderCode": order_code,
            "amount": amount,
            "description": description,
            "returnUrl": return_url,
            "cancelUrl": cancel_url,
        }
        
        if buyer_name:
            payload["buyerName"] = buyer_name
        if buyer_email:
            payload["buyerEmail"] = buyer_email
        
        # Tạo signature
        payload["signature"] = self._create_signature(payload)
        
        headers = {
            "x-client-id": self.client_id,
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        
        try:
            print(f">>> PayOS API Request: {self.api_url}")
            print(f">>> Payload: orderCode={payload.get('orderCode')}, amount={payload.get('amount')}")
            
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            
            print(f">>> PayOS API Status: {response.status_code}")
            print(f">>> PayOS API Response: {response.text[:500]}")
            
            response.raise_for_status()
            result = response.json()
            return result
            
        except requests.exceptions.RequestException as e:
            print(f">>> PayOS API Error: {type(e).__name__}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f">>> Response status: {e.response.status_code}")
                print(f">>> Response body: {e.response.text[:500]}")
            return {"error": str(e), "code": "API_ERROR"}
        except Exception as e:
            print(f">>> PayOS Unexpected Error: {type(e).__name__}: {e}")
            return {"error": str(e), "code": "UNKNOWN_ERROR"}
    
    def _create_signature(self, data: Dict[str, Any]) -> str:
        """Tạo signature cho request theo chuẩn PayOS
        
        Theo docs PayOS:
        - Payment request signature chỉ dùng 5 fields: 
          amount, cancelUrl, description, orderCode, returnUrl
        - Sort alphabetically
        - Format: key1=value1&key2=value2
        - HMAC SHA256
        """
        # Chỉ lấy 5 fields cho payment request signature
        signature_fields = ["amount", "cancelUrl", "description", "orderCode", "returnUrl"]
        
        payload_for_signature = {}
        for key in signature_fields:
            if key in data and data[key] is not None and data[key] != "":
                payload_for_signature[key] = data[key]
        
        # Sort keys alphabetically
        sorted_keys = sorted(payload_for_signature.keys())
        query_parts = []
        
        for key in sorted_keys:
            value = payload_for_signature[key]
            # Convert value to string
            if isinstance(value, bool):
                value_str = 'true' if value else 'false'
            elif isinstance(value, (int, float)):
                value_str = str(value)
            elif isinstance(value, str):
                value_str = value
            else:
                # For complex types, use JSON
                value_str = json.dumps(value, separators=(',', ':'), ensure_ascii=False)
            
            query_parts.append(f"{key}={value_str}")
        
        data_query_str = "&".join(query_parts)
        print(f">>> Signature data (5 fields only): {data_query_str}")
        
        # Create HMAC SHA256 signature
        signature = hmac.new(
            self.checksum_key.encode("utf-8"),
            msg=data_query_str.encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        print(f">>> Generated signature: {signature}")
        return signature
    
    def verify_webhook_signature(self, webhook_data: Dict[str, Any]) -> bool:
        """Verify webhook signature từ PayOS"""
        try:
            received_signature = webhook_data.get("signature", "")
            if not received_signature:
                print(">>> PayOS Webhook: No signature in data")
                return False
            
            payload_for_verify = {k: v for k, v in webhook_data.items() if k != "signature"}
            expected_signature = self._create_signature(payload_for_verify)
            
            is_valid = received_signature.lower() == expected_signature.lower()
            
            if not is_valid:
                print(f">>> PayOS Webhook: Signature mismatch")
                print(f">>> Received: {received_signature}")
                print(f">>> Expected: {expected_signature}")
            
            return is_valid
            
        except Exception as e:
            print(f">>> PayOS Webhook Verification Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False
