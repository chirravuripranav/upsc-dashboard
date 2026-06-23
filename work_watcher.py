"""
work_watcher.py
- Watches work_queue.jsonl for new tasks from Telegram
- Exits with the task when found → Antigravity gets notified and does the work
- Antigravity then sends results back via send_reply.py and restarts this watcher
"""
import json, os, sys, time

QUEUE_FILE     = 'work_queue.jsonl'
PROCESSED_FILE = 'work_processed.txt'

def get_processed():
    if os.path.exists(PROCESSED_FILE):
        c = open(PROCESSED_FILE).read().strip()
        return int(c) if c.isdigit() else 0
    return 0

def get_total():
    if not os.path.exists(QUEUE_FILE):
        return 0
    with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
        return sum(1 for l in f if l.strip())

def get_entry(index):
    with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
        lines = [l for l in f if l.strip()]
        if index < len(lines):
            return json.loads(lines[index])
    return None

print('[*] Work watcher ready. Waiting for /work tasks from Telegram...', flush=True)

processed = get_processed()

while True:
    total = get_total()
    if total > processed:
        entry = get_entry(processed)
        if entry:
            with open(PROCESSED_FILE, 'w') as f:
                f.write(str(processed + 1))
            print(f"[WORK TASK] {entry['user']}: {entry['task']}", flush=True)
            print(f"[CHAT_ID] {entry['chat_id']}", flush=True)
            sys.exit(0)
    time.sleep(0.5)
