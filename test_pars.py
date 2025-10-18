import requests
import json

merchant_id = "45209320-b090-4116-a1bd-8abd770d7787"  
callback_url = "https://drcode-med.ir/payment/status/"  

request_data = {
    "merchant_id": merchant_id,
    "amount": 10000 * 10,  
    "callback_url": callback_url,
    "description": "تست پرداخت زرین‌پال",
}

print("🔹 REQUEST DATA:\n", json.dumps(request_data, indent=2))

response = requests.post(
    "https://api.zarinpal.com/pg/v4/payment/request.json",
    json=request_data,
    headers={"Content-Type": "application/json"}
)

print("\n🔸 STATUS:", response.status_code)
print("🔸 RESPONSE TEXT:\n", response.text)
