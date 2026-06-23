import time
import requests
import os
import json

# Try to load token from .env
token = None
whitelist_chat_id = None

if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('BOT_TOKEN='):
                token = line.strip().split('=', 1)[1].strip()
            if line.startswith('TELEGRAM_CHAT_ID='):
                whitelist_chat_id = line.strip().split('=', 1)[1].strip()

if not token or token == 'YOUR_TELEGRAM_TOKEN_HERE':
    print("[ERROR] Please set your BOT_TOKEN in the .env file!", flush=True)
    exit(1)

API_URL = f"https://api.telegram.org/bot{token}/"

def get_updates(offset=None):
    url = API_URL + "getUpdates"
    params = {'timeout': 100, 'offset': offset}
    try:
        response = requests.get(url, params=params, timeout=110)
        return response.json()
    except Exception as e:
        print(f"[WARNING] Network error: {e}")
        return None

def main():
    print(f"[*] Starting Telegram Bridge Poller...")
    print(f"[*] Waiting for messages...")
    
    offset = None
    
    # Try to read last offset to avoid duplicate messages on restart
    if os.path.exists('offset.txt'):
        with open('offset.txt', 'r') as f:
            content = f.read().strip()
            if content.isdigit():
                offset = int(content)

    while True:
        updates = get_updates(offset)
        
        if updates and "result" in updates:
            for update in updates["result"]:
                offset = update["update_id"] + 1
                
                # Save offset
                with open('offset.txt', 'w') as f:
                    f.write(str(offset))
                
                if "message" in update and "text" in update["message"]:
                    chat_id = str(update["message"]["chat"]["id"])
                    text = update["message"]["text"]
                    
                    # Save to queue.jsonl
                    entry = {
                        'chat_id': chat_id,
                        'text': text,
                        'user': 'Telegram User',
                        'platform': 'telegram',
                        'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    }
                    
                    # Auto-whitelist the first person who messages it, or check against existing whitelist
                    global whitelist_chat_id
                    if not whitelist_chat_id:
                        print(f"[*] Locking bot to first user. Chat ID: {chat_id}", flush=True)
                        whitelist_chat_id = chat_id
                        with open('.env', 'a') as f:
                            f.write(f"\nTELEGRAM_CHAT_ID={chat_id}\n")
                        print(f"[TELEGRAM_MESSAGE] From: {chat_id} | Text: {text}", flush=True)
                        with open('queue.jsonl', 'a', encoding='utf-8') as f:
                            f.write(json.dumps(entry) + '\n')
                    elif chat_id == whitelist_chat_id:
                        print(f"[TELEGRAM_MESSAGE] From: {chat_id} | Text: {text}", flush=True)
                        with open('queue.jsonl', 'a', encoding='utf-8') as f:
                            f.write(json.dumps(entry) + '\n')
                    else:
                        print(f"[*] Ignored message from unauthorized chat ID: {chat_id}", flush=True)
                        
        time.sleep(1)

if __name__ == '__main__':
    main()
