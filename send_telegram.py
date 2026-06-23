import sys
import os
import requests

def send_telegram(message):
    token = None
    chat_id = None
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('BOT_TOKEN='):
                    token = line.strip().split('=', 1)[1].strip()
                if line.startswith('TELEGRAM_CHAT_ID='):
                    chat_id = line.strip().split('=', 1)[1].strip()
                    
    if not token or not chat_id:
        print("[ERROR] Missing BOT_TOKEN or CHAT_ID in .env")
        sys.exit(1)
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("[SUCCESS] Message sent to Telegram!")
        else:
            print(f"[ERROR] Failed to send: {response.text}")
    except Exception as e:
        print(f"[ERROR] Exception: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        message = sys.argv[1]
        send_telegram(message)
    else:
        print("Usage: python send_telegram.py <message>")
