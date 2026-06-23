import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import time
import requests
import os
import json

# ── Load config from .env files ──────────────────────────────────────────────
def load_env(path):
    config = {}
    if os.path.exists(path):
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    config[k.strip()] = v.strip()
    return config

# Load both .env files
local_env  = load_env('.env')                                 # telegram-bridge/.env  → BOT_TOKEN
parent_env = load_env(os.path.join('..', '.env'))            # project/.env          → GEMINI_API_KEY

BOT_TOKEN   = local_env.get('BOT_TOKEN', '')
GEMINI_KEY  = parent_env.get('GEMINI_API_KEY', '')
CHAT_ID     = local_env.get('CHAT_ID', '')

if not BOT_TOKEN:
    print("[ERROR] BOT_TOKEN missing in .env"); exit(1)
if not GEMINI_KEY:
    print("[ERROR] GEMINI_API_KEY missing in ../.env"); exit(1)

TG_URL      = f"https://api.telegram.org/bot{BOT_TOKEN}/"
GEMINI_URL  = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
)

# ── Conversation history (multi-turn) ────────────────────────────────────────
history = []

SYSTEM_PROMPT = (
    "You are Antigravity, a brilliant, friendly, and witty AI coding assistant. "
    "You help with coding, projects, ideas, and anything the user needs. "
    "Keep responses concise and conversational since you're replying on Telegram. "
    "Use emojis where appropriate to keep it fun."
)

# ── Telegram helpers ──────────────────────────────────────────────────────────
def get_updates(offset=None):
    try:
        r = requests.get(TG_URL + "getUpdates",
                         params={'timeout': 30, 'offset': offset},
                         timeout=40)
        return r.json()
    except Exception as e:
        print(f"[WARN] getUpdates error: {e}")
        return None

def send_message(chat_id, text):
    # Split long messages (Telegram limit is 4096 chars)
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for chunk in chunks:
        try:
            requests.post(TG_URL + "sendMessage",
                          json={'chat_id': chat_id, 'text': chunk, 'parse_mode': 'Markdown'},
                          timeout=15)
        except Exception as e:
            print(f"[WARN] sendMessage error: {e}")

def send_typing(chat_id):
    try:
        requests.post(TG_URL + "sendChatAction",
                      json={'chat_id': chat_id, 'action': 'typing'},
                      timeout=5)
    except:
        pass

# ── Gemini AI reply ───────────────────────────────────────────────────────────
def ask_gemini(user_text):
    history.append({"role": "user", "parts": [{"text": user_text}]})

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": history
    }

    try:
        r = requests.post(GEMINI_URL, json=payload, timeout=30)
        data = r.json()

        if 'candidates' in data and data['candidates']:
            reply = data['candidates'][0]['content']['parts'][0]['text']
            history.append({"role": "model", "parts": [{"text": reply}]})
            return reply
        else:
            print(f"[WARN] Gemini bad response: {data}")
            return "Sorry, I couldn't generate a reply right now. Try again!"
    except Exception as e:
        print(f"[WARN] Gemini error: {e}")
        return "⚠️ Error reaching Gemini. Please try again."

# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    global CHAT_ID

    print("[*] Antigravity Telegram Bot started!")
    print(f"[*] Bot token: ...{BOT_TOKEN[-10:]}")
    print(f"[*] Gemini key: ...{GEMINI_KEY[-6:]}")
    if CHAT_ID:
        print(f"[*] Locked to chat ID: {CHAT_ID}")
    else:
        print("[*] Waiting for first message to lock chat ID...")

    offset = None
    if os.path.exists('offset.txt'):
        content = open('offset.txt').read().strip()
        if content.isdigit():
            offset = int(content)

    while True:
        updates = get_updates(offset)

        if updates and updates.get('ok') and updates.get('result'):
            for update in updates['result']:
                offset = update['update_id'] + 1
                with open('offset.txt', 'w') as f:
                    f.write(str(offset))

                if 'message' not in update:
                    continue

                msg     = update['message']
                chat_id = str(msg['chat']['id'])
                text    = msg.get('text', '')

                if not text:
                    continue

                # Whitelist logic
                if not CHAT_ID:
                    CHAT_ID = chat_id
                    with open('.env', 'a') as f:
                        f.write(f"\nCHAT_ID={chat_id}\n")
                    print(f"[*] Locked to chat ID: {chat_id}")
                elif chat_id != CHAT_ID:
                    print(f"[*] Ignored unauthorized chat: {chat_id}")
                    continue

                print(f"\n[YOU] {text}")

                # Show typing indicator
                send_typing(chat_id)

                # Get AI reply
                reply = ask_gemini(text)
                print(f"[BOT] {reply}")

                # Send back to Telegram
                send_message(chat_id, reply)

        time.sleep(1)

if __name__ == '__main__':
    main()
