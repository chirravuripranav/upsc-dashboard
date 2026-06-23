"""
watcher.py — WhatsApp Message Listener (Exit-on-message mode)
- Watches queue.jsonl for new unprocessed messages
- Exits when a message is found (this triggers a system notification to wake up Antigravity)
- Antigravity auto-restarts this watcher after processing each message
"""
import json
import os
import sys
import time

QUEUE_FILE     = 'queue.jsonl'
PROCESSED_FILE = 'processed.txt'

def get_processed_count():
    if os.path.exists(PROCESSED_FILE):
        c = open(PROCESSED_FILE).read().strip()
        return int(c) if c.isdigit() else 0
    return 0

def get_queue_count():
    if not os.path.exists(QUEUE_FILE):
        return 0
    with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
        return sum(1 for line in f if line.strip())

def get_message_at(index):
    with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
        lines = [l for l in f if l.strip()]
        if index < len(lines):
            return json.loads(lines[index])
    return None

print('[*] Watcher listening for WhatsApp messages...', flush=True)

processed = get_processed_count()

while True:
    total = get_queue_count()
    if total > processed:
        msg = get_message_at(processed)
        if msg:
            # Mark as processed
            with open(PROCESSED_FILE, 'w') as f:
                f.write(str(processed + 1))

            # Output message for Antigravity
            print(f"[INCOMING] {msg['user']}: {msg['text']}", flush=True)
            print(f"[CHAT_ID] {msg['chat_id']}", flush=True)
            sys.exit(0)  # EXIT to trigger system notification
    time.sleep(0.5)
