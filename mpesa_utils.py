import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import base64

def get_access_token():
    # YOUR ACTUAL KEYS
    consumer_key = "9pRt851pT9WzxtF7aJrBCj2oBTynL3XrkPDqpsLINHyFxXU1"
    consumer_secret = "7kAwXo2qU6c9IHh2Aw5Bdm5epp6RvQ0WeDP2RtCUumfOvrrePGxjCMpaGJt3TnKi"
    
    api_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    return r.json().get('access_token')

def send_stk_push(phone, amount):
    access_token = get_access_token()
    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # M-Pesa Password generation
    business_short_code = "174379"
    passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode((business_short_code + passkey + timestamp).encode()).decode()

    # Formating phone to 254...
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif not phone.startswith("254"):
        phone = "254" + phone

    payload = {
        "BusinessShortCode": business_short_code,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(float(amount)),
        "PartyA": phone,
        "PartyB": business_short_code,
        "PhoneNumber": phone,
        "CallBackURL": "https://google.com", # We will replace this with your Localtunnel link later
        "AccountReference": "SmartexFurniture",
        "TransactionDesc": "Payment for furniture"
    }
    
    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()

