import requests
import os
import sys
import argparse
import shutil

def get_config():
    config = {}
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    config[k.strip()] = v.strip()
    return config

def send_message(config, chat_id, text):
    sid = config.get('TWILIO_SID')
    token = config.get('TWILIO_AUTH_TOKEN')
    from_num = config.get('TWILIO_FROM', 'whatsapp:+14155238886')
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    
    # Twilio limit is 1600 characters for WhatsApp, but we can split by 1500
    max_len = 1500
    chunks = []
    while len(text) > max_len:
        split_idx = text.rfind('\n', 0, max_len)
        if split_idx == -1:
            split_idx = text.rfind(' ', 0, max_len)
        if split_idx == -1:
            split_idx = max_len
        chunks.append(text[:split_idx].strip())
        text = text[split_idx:].strip()
    if text:
        chunks.append(text)

    success = True
    for chunk in chunks:
        payload = {
            'From': from_num,
            'To': chat_id,
            'Body': chunk
        }
        for attempt in range(1, 4):
            try:
                r = requests.post(url, data=payload, auth=(sid, token), timeout=15)
                if r.status_code in (200, 201):
                    break
                print(f"[WARN] Send attempt {attempt} got status {r.status_code}: {r.text}")
            except Exception as e:
                print(f"[WARN] Send attempt {attempt} failed: {e}")
            if attempt < 3:
                import time; time.sleep(2)
        else:
            print("[ERROR] All 3 send attempts failed for chunk!")
            success = False
            
    return success

def send_document(config, chat_id, file_path):
    sid = config.get('TWILIO_SID')
    token = config.get('TWILIO_AUTH_TOKEN')
    from_num = config.get('TWILIO_FROM', 'whatsapp:+14155238886')
    ngrok_url = config.get('NGROK_URL')
    
    if not ngrok_url:
        print("[ERROR] NGROK_URL missing in .env, cannot send document via Twilio.")
        return False
        
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    filename = os.path.basename(file_path)
    
    # Copy file to media directory so Flask can serve it
    os.makedirs('media', exist_ok=True)
    dest_path = os.path.join('media', filename)
    shutil.copy2(file_path, dest_path)
    
    media_url = f"{ngrok_url}/media/{filename}"

    payload = {
        'From': from_num,
        'To': chat_id,
        'MediaUrl': media_url
    }
    
    for attempt in range(1, 4):
        try:
            r = requests.post(url, data=payload, auth=(sid, token), timeout=15)
            if r.status_code in (200, 201):
                return True
            print(f"[WARN] File send attempt {attempt} got status {r.status_code}: {r.text}")
        except Exception as e:
            print(f"[WARN] File send attempt {attempt} failed: {e}")
        if attempt < 3:
            import time; time.sleep(2)
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--text', help="Text to send")
    parser.add_argument('--file', help="Path to file to send")
    args = parser.parse_args()

    config = get_config()
    chat_id = config.get('CHAT_ID')
    if not config.get('TWILIO_SID') or not config.get('TWILIO_AUTH_TOKEN') or not chat_id:
        print("[ERROR] Missing TWILIO_SID, TWILIO_AUTH_TOKEN, or CHAT_ID in .env")
        sys.exit(1)

    if args.text:
        send_message(config, chat_id, args.text)
        print("[*] Message sent!")
    
    if args.file:
        send_document(config, chat_id, args.file)
        print("[*] File sent!")

if __name__ == '__main__':
    main()
