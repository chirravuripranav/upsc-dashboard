"""
relay.py — Polls Telegram for ONE message, writes it to incoming.json, then exits.
Antigravity reads incoming.json, replies, runs send_reply.py, then restarts this script.
"""
import time
import requests
import os
import json
import sys

# ── Load .env ─────────────────────────────────────────────────────────────────
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

env = load_env('.env')
BOT_TOKEN = env.get('BOT_TOKEN', '')
CHAT_ID   = env.get('CHAT_ID', '')

if not BOT_TOKEN:
    print('[ERROR] BOT_TOKEN missing'); sys.exit(1)

TG_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

def get_updates(offset=None):
    try:
        r = requests.get(TG_URL + "getUpdates",
                         params={'timeout': 30, 'offset': offset},
                         timeout=40)
        return r.json()
    except Exception as e:
        print(f"[WARN] {e}")
        return None

def send_typing(chat_id):
    try:
        requests.post(TG_URL + "sendChatAction",
                      json={'chat_id': chat_id, 'action': 'typing'},
                      timeout=5)
    except:
        pass

# ── Load offset ───────────────────────────────────────────────────────────────
offset = None
if os.path.exists('offset.txt'):
    c = open('offset.txt').read().strip()
    if c.isdigit():
        offset = int(c)

print('[*] Relay waiting for Telegram message...')

# ── Poll until we get a message ───────────────────────────────────────────────
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
            user    = msg['chat'].get('first_name', chat_id)

            if not text:
                continue

            # Whitelist check / first-time lock
            if not CHAT_ID:
                with open('.env', 'a') as f:
                    f.write(f'\nCHAT_ID={chat_id}\n')
                print(f'[*] Locked to chat ID: {chat_id}')
            elif chat_id != CHAT_ID:
                print(f'[*] Ignored unauthorized: {chat_id}')
                continue

            # Show typing indicator to user
            send_typing(chat_id)

            # Write message to file for Antigravity to read
            data = {'chat_id': chat_id, 'text': text, 'user': user}
            with open('incoming.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)

            print(f'[INCOMING] {user}: {text}')
            sys.exit(0)   # Signal Antigravity that a message arrived

    time.sleep(1)
