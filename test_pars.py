import requests
import json
from django.conf import settings

def test_parspal_minimal():
    """تست با حداقل فیلدها"""
    config = settings.PARSPAL_CONFIG
    
    url = "https://sandbox.api.parspal.com/v1/payment/request"
    headers = {
        'Content-Type': 'application/json',
        'ApiKey': config['API_KEY']
    }
    
    data = {
        "amount": 10000,
        "return_url": "http://127.0.0.1:8000/",
        "currency": "IRR"
    }
    
    print("=== Test 1: Minimal Fields ===")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        print(f"\nStatus: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✓ Success with minimal fields!")
            return True
        else:
            print("✗ Failed with minimal fields")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_parspal_with_description():
    """تست با افزودن description"""
    config = settings.PARSPAL_CONFIG
    
    url = "https://sandbox.api.parspal.com/v1/payment/request"
    headers = {
        'Content-Type': 'application/json',
        'ApiKey': config['API_KEY']
    }
    
    data = {
        "amount": 10000,
        "return_url": "http://127.0.0.1:8000/",
        "currency": "IRR",
        "description": "Test Payment"
    }
    
    print("\n=== Test 2: With Description ===")
    print(f"Data: {json.dumps(data, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✓ Success with description!")
            return True
        else:
            print("✗ Failed with description")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_parspal_with_order_id():
    """تست با افزودن order_id"""
    config = settings.PARSPAL_CONFIG
    
    url = "https://sandbox.api.parspal.com/v1/payment/request"
    headers = {
        'Content-Type': 'application/json',
        'ApiKey': config['API_KEY']
    }
    
    data = {
        "amount": 10000,
        "return_url": "http://127.0.0.1:8000/",
        "currency": "IRR",
        "description": "Test Payment",
        "order_id": "TEST123"
    }
    
    print("\n=== Test 3: With Order ID ===")
    print(f"Data: {json.dumps(data, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✓ Success with order_id!")
            return True
        else:
            print("✗ Failed with order_id")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_parspal_with_payer():
    """تست با افزودن اطلاعات پرداخت‌کننده"""
    config = settings.PARSPAL_CONFIG
    
    url = "https://sandbox.api.parspal.com/v1/payment/request"
    headers = {
        'Content-Type': 'application/json',
        'ApiKey': config['API_KEY']
    }
    
    data = {
        "amount": 10000,
        "return_url": "http://127.0.0.1:8000/",
        "currency": "IRR",
        "description": "Test Payment",
        "order_id": "TEST123",
        "payer": {
            "name": "Test User",
            "mobile": "09121234567",
            "email": "test@example.com"
        }
    }
    
    print("\n=== Test 4: With Payer Info ===")
    print(f"Data: {json.dumps(data, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✓ Success with payer info!")
            return True
        else:
            print("✗ Failed with payer info")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == '__main__':
    import django
    django.setup()
    
    print("Testing Parspal API...")
    print("=" * 50)
    
    test_parspal_minimal()
    test_parspal_with_description()
    test_parspal_with_order_id()
    test_parspal_with_payer()
