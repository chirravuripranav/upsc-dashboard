import discord
import os
import json
import requests
from datetime import datetime

def get_token():
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('BOT_TOKEN='):
                    return line.strip().split('=', 1)[1].strip()
    return None

def get_chat_id():
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('CHAT_ID='):
                    return line.strip().split('=', 1)[1].strip()
    return None

def update_env_chat_id(chat_id):
    lines = []
    found = False
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
    with open('.env', 'w', encoding='utf-8') as f:
        for line in lines:
            if line.startswith('CHAT_ID='):
                f.write(f'CHAT_ID={chat_id}\n')
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f'CHAT_ID={chat_id}\n')

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'[*] Discord bot logged in as {self.user}')

    async def on_message(self, message):
        if message.author == self.user:
            return

        # We only accept DMs (direct messages) to the bot
        if not isinstance(message.channel, discord.DMChannel):
            return

        chat_id = str(message.channel.id)
        whitelist_chat_id = get_chat_id()

        if not whitelist_chat_id:
            print(f"[*] Locking bot to first DM user. Chat ID: {chat_id}")
            update_env_chat_id(chat_id)
            whitelist_chat_id = chat_id
        elif chat_id != whitelist_chat_id:
            print(f"[*] Ignored message from unauthorized DM chat ID: {chat_id}")
            return

        # Get photos if any and download them locally
        photos = []
        for att in message.attachments:
            if att.content_type and att.content_type.startswith('image/'):
                try:
                    ext = att.filename.split('.')[-1] if '.' in att.filename else 'png'
                    filename = f"images/photo_{int(datetime.utcnow().timestamp())}_{att.id}.{ext}"
                    os.makedirs('images', exist_ok=True)
                    
                    r = requests.get(att.url, timeout=30)
                    if r.status_code == 200:
                        with open(filename, 'wb') as f:
                            f.write(r.content)
                        photos.append(filename)
                except Exception as e:
                    print(f"[ERROR] Failed to download attachment: {e}")

        text = message.content
        if photos:
            photos_str = ", ".join(photos)
            if text:
                text = f"[IMAGE RECEIVED: {photos_str}] {text}"
            else:
                text = f"[IMAGE RECEIVED: {photos_str}]"

        msg_obj = {
            'user': message.author.name,
            'text': text,
            'chat_id': chat_id,
            'photo': [{'url': url} for url in photos] if photos else None,
            'timestamp': datetime.utcnow().isoformat()
        }

        # Write to queue
        with open('queue.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps(msg_obj, ensure_ascii=False) + '\n')
            
        print(f"[RECEIVED] {message.author.name}: {text}", flush=True)

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
token = get_token()
if token:
    client.run(token)
else:
    print("[ERROR] No BOT_TOKEN found in .env")
