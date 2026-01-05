import hmac
import hashlib
import json
import time
from typing import Optional, Dict, Any
import httpx
from fastapi import HTTPException
from app.core.config import settings

class PayOSService:
    
    def __init__(self):
        self.client_id = settings.PAYOS_CLIENT_ID
        self.api_key = settings.PAYOS_API_KEY
        self.checksum_key = settings.PAYOS_CHECKSUM_KEY
        self.base_url = "https://api-merchant.payos.vn"
        
    def _generate_signature(self, data_str: str) -> str:
        return hmac.new(
            self.checksum_key.encode('utf-8'),
            data_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _create_signature_data(self, data: Dict[str, Any]) -> str:
        sorted_keys = sorted(data.keys())
        return "&".join([f"{k}={data[k]}" for k in sorted_keys])

    async def create_payment_link(
        self,
        order_id: int,
        order_code: int,
        amount: int,
        description: str,
        buyer_name: str,
        buyer_email: str,
        buyer_phone: str,
        return_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        
        if not settings.PAYOS_ENABLED:
            raise HTTPException(status_code=503, detail="PayOS is not enabled")
        
        sign_data = {
            "amount": amount,
            "cancelUrl": cancel_url or settings.PAYOS_CANCEL_URL_COMPUTED,
            "description": description,
            "orderCode": order_code,
            "returnUrl": return_url or settings.PAYOS_RETURN_URL_COMPUTED
        }
    
        sign_str = self._create_signature_data(sign_data)
        signature = self._generate_signature(sign_str)
        
        payment_data = {
            **sign_data,
            "buyerName": buyer_name,
            "buyerEmail": buyer_email,
            "buyerPhone": buyer_phone,
            "buyerAddress": "Vietnam",
            "items": [],
            "expiredAt": int(time.time()) + 900,
            "signature": signature
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v2/payment-requests",
                    json=payment_data,
                    headers={
                        "x-client-id": self.client_id,
                        "x-api-key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    print(f"PayOS Response Error: {response.text}")
                
                response.raise_for_status()
                result = response.json()
                
                if result.get("code") == "00":
                    data = result.get("data", {})
                    return {
                        "checkoutUrl": data.get("checkoutUrl"),
                        "qrCode": data.get("qrCode"),
                        "orderCode": str(payment_data["orderCode"]),
                        "bin": data.get("bin"),
                        "accountNumber": data.get("accountNumber"),
                        "accountName": data.get("accountName"),
                        "payment_url": data.get("checkoutUrl"), 
                        "qr_code": data.get("qrCode")
                    }
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"PayOS error: {result.get('desc', 'Unknown error')}"
                    )
                    
            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"PayOS API error: {str(e)}"
                )
    
    def verify_webhook_signature(
        self,
        webhook_data: Dict[str, Any],
        signature: str
    ) -> bool:
        sorted_data = dict(sorted(webhook_data.items()))
        data_str = "&".join([f"{k}={v}" for k, v in sorted_data.items()])
        calculated_signature = self._generate_signature(data_str)
        return hmac.compare_digest(calculated_signature, signature)
    
    async def check_payment_status(self, order_code: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/v2/payment-requests/{order_code}",
                    headers={
                        "x-client-id": self.client_id,
                        "x-api-key": self.api_key,
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                if result.get("code") == "00":
                    return result.get("data", {})
                else:
                    raise HTTPException(status_code=400, detail=f"PayOS error: {result.get('desc')}")
            except httpx.HTTPError as e:
                raise HTTPException(status_code=500, detail=f"PayOS API error: {str(e)}")

    async def cancel_payment(self, order_code: str, reason: Optional[str] = None) -> bool:
         async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(
                    f"{self.base_url}/v2/payment-requests/{order_code}",
                    headers={
                        "x-client-id": self.client_id,
                        "x-api-key": self.api_key,
                    },
                    json={"cancellationReason": reason or "User cancelled"},
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("code") == "00"
            except httpx.HTTPError:
                return False