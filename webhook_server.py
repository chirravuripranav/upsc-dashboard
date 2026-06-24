"""
webhook_server.py — Pure Relay Bot (Twilio WhatsApp)
- Receives messages via Twilio webhook
- Queues ALL messages for Antigravity (real AI agent) to process directly
"""
import os, sys, json
from flask import Flask, request, jsonify
from datetime import datetime
import requests

def load_env(path):
    config = {}
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    config[k.strip()] = v.strip()
    return config

env        = load_env('.env')
TWILIO_SID = env.get('TWILIO_SID', '')
TWILIO_AUTH_TOKEN = env.get('TWILIO_AUTH_TOKEN', '')
NGROK_TOKEN = env.get('NGROK_TOKEN', '')
CHAT_ID     = env.get('CHAT_ID', '')

if not TWILIO_SID or not TWILIO_AUTH_TOKEN:
    print('[WARNING] TWILIO_SID or TWILIO_AUTH_TOKEN missing in .env. Bridge functions disabled, but web server will still run.')

app = Flask(__name__, static_folder='media', static_url_path='/app')

from flask import send_from_directory

@app.route('/media/<path:filename>')
def serve_media(filename):
    return send_from_directory('media', filename)

@app.route('/')
def root():
    from flask import redirect
    return redirect('/app/')

@app.route('/app/')
def serve_index():
    return app.send_static_file('index.html')

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

@app.route('/webhook', methods=['POST'])
def webhook():
    # Twilio sends data as form-urlencoded
    data = request.form
    if not data:
        return jsonify({'ok': True})

    sender = data.get('From', '')
    text = data.get('Body', '')
    num_media = int(data.get('NumMedia', 0))
    
    if not sender.startswith('whatsapp:'):
        return jsonify({'ok': True})
        
    chat_id = sender

    # Whitelist check / locking
    global CHAT_ID
    if not CHAT_ID:
        print(f"[*] Locking bot to first user. Chat ID: {chat_id}")
        update_env_chat_id(chat_id)
        CHAT_ID = chat_id
    elif CHAT_ID != chat_id:
        print(f'[IGNORED] Unauthorized: {chat_id}')
        return jsonify({'ok': True})

    # Handle photo
    if num_media > 0:
        media_url = data.get('MediaUrl0')
        content_type = data.get('MediaContentType0', '')
        if media_url and content_type.startswith('image/'):
            try:
                ext = content_type.split('/')[-1]
                if ext == 'jpeg': ext = 'jpg'
                filename = f"images/photo_{int(datetime.utcnow().timestamp())}.{ext}"
                os.makedirs('images', exist_ok=True)
                
                # Download image from Twilio
                img_data = requests.get(media_url, auth=(TWILIO_SID, TWILIO_AUTH_TOKEN)).content
                with open(filename, 'wb') as f:
                    f.write(img_data)
                
                if text:
                    text = f"[IMAGE RECEIVED: {filename}] {text}"
                else:
                    text = f"[IMAGE RECEIVED: {filename}]"
            except Exception as e:
                text = f"[ERROR DOWNLOADING IMAGE]: {e}"

    # Write to queue
    entry = {
        'chat_id': chat_id,
        'text': text,
        'user': 'WhatsApp User', # Twilio doesn't provide name by default in sandbox
        'timestamp': datetime.utcnow().isoformat()
    }
    with open('queue.jsonl', 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print(f'[QUEUED] {chat_id}: {text}', flush=True)

    # Twilio expects XML response for TwiML, but we use REST API to reply later
    # We can just return empty TwiML
    return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 200, {'Content-Type': 'application/xml'}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'Twilio Pure relay running'})

# ============ IMPORT API ROUTES ============
from api_server import init_db, get_db, evaluate_mains_answer
from datetime import date as date_type
import sqlite3

@app.route('/api/score', methods=['POST'])
def save_score():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO quiz_scores (user_id, day, week, phase, score, total_marks, correct, attempted, total_questions, accuracy, completed_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data.get('user_id', 'default'), data['day'], data.get('week', 1), data.get('phase', 1),
               data['score'], data['total_marks'], data['correct'], data['attempted'],
               data['total_questions'], data['accuracy'], datetime.utcnow().isoformat()))
    today = date_type.today().isoformat()
    c.execute('''INSERT OR REPLACE INTO calendar (user_id, date, day, week, activity_type, completed)
                 VALUES (?, ?, ?, ?, 'quiz', 1)''',
              (data.get('user_id', 'default'), today, data['day'], data.get('week', 1)))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'message': 'Score saved!'})

@app.route('/api/scores', methods=['GET'])
def get_scores():
    user_id = request.args.get('user_id', 'default')
    conn = get_db()
    rows = conn.execute('SELECT * FROM quiz_scores WHERE user_id=? ORDER BY completed_at DESC', (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/calendar', methods=['GET'])
def get_calendar():
    user_id = request.args.get('user_id', 'default')
    conn = get_db()
    rows = conn.execute('SELECT * FROM calendar WHERE user_id=? ORDER BY date DESC', (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/mains/submit', methods=['POST'])
def submit_mains():
    data = request.json
    user_answer = data.get('user_answer', '')
    question = data.get('question', '')
    evaluation = evaluate_mains_answer(question, user_answer)
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO mains_answers (user_id, day, week, question, user_answer, evaluation, marks_given, submitted_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (data.get('user_id', 'default'), data.get('day'), data.get('week'),
               question, user_answer, evaluation['feedback'], evaluation['marks'], datetime.utcnow().isoformat()))
    today = date_type.today().isoformat()
    c.execute('''INSERT OR REPLACE INTO calendar (user_id, date, day, week, activity_type, completed)
                 VALUES (?, ?, ?, ?, 'mains', 1)''',
              (data.get('user_id', 'default'), today, data.get('day'), data.get('week')))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'evaluation': evaluation})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    user_id = request.args.get('user_id', 'default')
    conn = get_db()
    quiz_count = conn.execute('SELECT COUNT(*) as c FROM quiz_scores WHERE user_id=?', (user_id,)).fetchone()['c']
    avg_accuracy = conn.execute('SELECT AVG(accuracy) as a FROM quiz_scores WHERE user_id=?', (user_id,)).fetchone()['a'] or 0
    total_correct = conn.execute('SELECT SUM(correct) as c FROM quiz_scores WHERE user_id=?', (user_id,)).fetchone()['c'] or 0
    mains_count = conn.execute('SELECT COUNT(*) as c FROM mains_answers WHERE user_id=?', (user_id,)).fetchone()['c']
    conn.close()
    return jsonify({
        'quizzes_completed': quiz_count,
        'avg_accuracy': round(avg_accuracy, 1),
        'total_correct': total_correct,
        'mains_written': mains_count
    })

@app.route('/api/current_affairs/generate', methods=['POST'])
def generate_ca():
    data = request.json
    notes = data.get('notes', '')
    if not notes:
        return jsonify({'error': 'No notes provided'}), 400
        
    groq_api_key = env.get('GROQ_API_KEY')
    # Check parent .env if not found locally
    if not groq_api_key:
        parent_env = r'c:\Users\prana\Downloads\project\.env'
        if os.path.exists(parent_env):
            with open(parent_env, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('GROQ_API_KEY='):
                        groq_api_key = line.split('=', 1)[1].strip()
                        break
                        
    if not groq_api_key:
        return jsonify({'error': 'GROQ_API_KEY missing from .env'}), 500
        
    try:
        from groq import Groq
        client = Groq(api_key=groq_api_key)
        
        prompt = f"""You are a strict UPSC examiner. The user has provided Current Affairs notes below.
Generate 2 difficult MCQs (with 4 options, the correct answer, and an explanation) based ONLY on these notes.
Also generate 1 Mains question (250 words, 15 marks) based on the notes.
Format your output beautifully in Markdown.

NOTES:
{notes}
"""
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1024,
            top_p=1
        )
        generated_test = completion.choices[0].message.content
        
        # Save to database
        conn = get_db()
        c = conn.cursor()
        c.execute('''INSERT INTO current_affairs (notes, generated_test, created_at)
                     VALUES (?, ?, ?)''', (notes, generated_test, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        
        return jsonify({'generated': generated_test})
    except Exception as e:
        print(f"[ERROR] Groq generation failed: {e}")
        return jsonify({'error': str(e)}), 500


def setup_tunnel():
    from pyngrok import ngrok, conf
    NGROK_TOKEN = os.getenv('NGROK_TOKEN', '')
    if NGROK_TOKEN:
        conf.get_default().auth_token = NGROK_TOKEN
    try:
        tunnel = ngrok.connect(5000, "http", domain="driving-mahogany-identify.ngrok-free.dev")
        public_url = tunnel.public_url.replace('http://', 'https://')
        print(f'\n{"="*50}')
        print(f'[*] ngrok tunnel active: {public_url}')
        print(f'[*] WEBHOOK URL: {public_url}/webhook')
        print(f'{"="*50}\n')
        return public_url
    except Exception as e:
        print(f'[WARN] ngrok failed: {e}, running local-only')
        return None

if __name__ == '__main__':
    os.makedirs('media', exist_ok=True)
    init_db()
    
    # Auto-detect: if on EC2 (Linux), use Waitress on port 80. Otherwise, use ngrok + Flask dev.
    import platform
    if platform.system() == 'Linux':
        print(f'\n{"="*50}')
        print(f'[*] EC2 MODE: Server starting on Port 80')
        print(f'{"="*50}\n')
        from waitress import serve
        serve(app, host='0.0.0.0', port=80)
    else:
        print(f'[*] LOCAL MODE: Starting with ngrok tunnel...')
        setup_tunnel()
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
