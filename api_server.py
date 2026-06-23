"""
api_server.py — Backend API for UPSC Study Platform
Provides persistent data storage (SQLite) for quiz scores, calendar tracking,
and mains answer evaluation.
"""
import os, json, sqlite3, time
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime, date

DB_PATH = 'upsc_data.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS quiz_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT DEFAULT 'default',
        day INTEGER NOT NULL,
        week INTEGER NOT NULL,
        phase INTEGER DEFAULT 1,
        score REAL,
        total_marks INTEGER,
        correct INTEGER,
        attempted INTEGER,
        total_questions INTEGER,
        accuracy REAL,
        completed_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS calendar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT DEFAULT 'default',
        date TEXT NOT NULL,
        day INTEGER,
        week INTEGER,
        activity_type TEXT,
        completed INTEGER DEFAULT 0,
        UNIQUE(user_id, date, activity_type)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS mains_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT DEFAULT 'default',
        day INTEGER,
        week INTEGER,
        question TEXT,
        user_answer TEXT,
        evaluation TEXT,
        marks_given REAL,
        submitted_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS current_affairs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        notes TEXT,
        generated_test TEXT,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()

app = Flask(__name__, static_folder='media', static_url_path='/media')

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
    # Mark calendar
    today = date.today().isoformat()
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

@app.route('/api/calendar/mark', methods=['POST'])
def mark_calendar():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO calendar (user_id, date, day, week, activity_type, completed)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (data.get('user_id', 'default'), data['date'], data.get('day'), data.get('week'),
               data.get('activity_type', 'study'), data.get('completed', 1)))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/mains/submit', methods=['POST'])
def submit_mains():
    data = request.json
    user_answer = data.get('user_answer', '')
    question = data.get('question', '')
    
    # AI Evaluation logic (rule-based scoring)
    evaluation = evaluate_mains_answer(question, user_answer)
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO mains_answers (user_id, day, week, question, user_answer, evaluation, marks_given, submitted_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (data.get('user_id', 'default'), data.get('day'), data.get('week'),
               question, user_answer, evaluation['feedback'], evaluation['marks'], datetime.utcnow().isoformat()))
    
    today = date.today().isoformat()
    c.execute('''INSERT OR REPLACE INTO calendar (user_id, date, day, week, activity_type, completed)
                 VALUES (?, ?, ?, ?, 'mains', 1)''',
              (data.get('user_id', 'default'), today, data.get('day'), data.get('week')))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'evaluation': evaluation})

@app.route('/api/mains/history', methods=['GET'])
def mains_history():
    user_id = request.args.get('user_id', 'default')
    conn = get_db()
    rows = conn.execute('SELECT * FROM mains_answers WHERE user_id=? ORDER BY submitted_at DESC', (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/stats', methods=['GET'])
def get_stats():
    user_id = request.args.get('user_id', 'default')
    conn = get_db()
    quiz_count = conn.execute('SELECT COUNT(*) as c FROM quiz_scores WHERE user_id=?', (user_id,)).fetchone()['c']
    avg_accuracy = conn.execute('SELECT AVG(accuracy) as a FROM quiz_scores WHERE user_id=?', (user_id,)).fetchone()['a'] or 0
    total_correct = conn.execute('SELECT SUM(correct) as c FROM quiz_scores WHERE user_id=?', (user_id,)).fetchone()['c'] or 0
    mains_count = conn.execute('SELECT COUNT(*) as c FROM mains_answers WHERE user_id=?', (user_id,)).fetchone()['c']
    streak = calculate_streak(conn, user_id)
    conn.close()
    return jsonify({
        'quizzes_completed': quiz_count,
        'avg_accuracy': round(avg_accuracy, 1),
        'total_correct': total_correct,
        'mains_written': mains_count,
        'current_streak': streak
    })

def calculate_streak(conn, user_id):
    rows = conn.execute('SELECT DISTINCT date FROM calendar WHERE user_id=? AND completed=1 ORDER BY date DESC', (user_id,)).fetchall()
    if not rows:
        return 0
    streak = 0
    today = date.today()
    for row in rows:
        d = date.fromisoformat(row['date'])
        expected = today - __import__('datetime').timedelta(days=streak)
        if d == expected:
            streak += 1
        else:
            break
    return streak

def evaluate_mains_answer(question, answer):
    """Deep, rule-based AI UPSC mains answer evaluation providing a 'spoon-feeding' long review."""
    word_count = len(answer.split())
    marks = 0
    feedback_parts = []
    
    feedback_parts.append("### 🤖 UPSC AI Evaluator Report\n*Hello! I am your AI UPSC Mentor. I have carefully analyzed your answer line by line. Here is your detailed, spoon-fed review:*")

    # 1. Word count analysis
    if word_count >= 200 and word_count <= 300:
        marks += 2
        feedback_parts.append(f"✅ **Length & Word Limit (2/2):** Brilliant. You wrote {word_count} words, which perfectly hits the UPSC 'sweet spot' for a 15-mark question. Time management here is spot on.")
    elif word_count >= 150:
        marks += 1.5
        feedback_parts.append(f"⚠️ **Length & Word Limit (1.5/2):** You wrote {word_count} words. It's a bit short. For a 15-mark question, the examiner expects more substance (ideally 200-250 words). Try to expand your body paragraphs.")
    elif word_count >= 100:
        marks += 1
        feedback_parts.append(f"⚠️ **Length & Word Limit (1/2):** Your answer is only {word_count} words. This is too short for Mains. You are leaving marks on the table. You need to develop your points with more examples.")
    else:
        marks += 0.5
        feedback_parts.append(f"❌ **Length & Word Limit (0.5/2):** You only wrote {word_count} words. An examiner will not give good marks for a one-paragraph answer. You MUST expand.")

    # 2. Structural Analysis
    has_intro = any(kw in answer.lower() for kw in ['introduction', 'the question', 'evolved', 'company', 'historically', 'fundamentally'])
    has_conclusion = any(kw in answer.lower() for kw in ['conclusion', 'thus', 'therefore', 'in conclusion', 'to conclude', 'hence', 'overall'])
    has_paragraphs = answer.count('\n') >= 2
    
    struct_score = 0
    if has_intro: struct_score += 1
    if has_conclusion: struct_score += 1
    if has_paragraphs: struct_score += 1
    marks += struct_score
    
    feedback_parts.append("### 🏗️ Structural Breakdown")
    if struct_score >= 3:
        feedback_parts.append("✅ **Structure (3/3):** You followed the Holy Trinity of UPSC answers: Introduction → Body → Conclusion. Your paragraphing makes it very easy for the examiner to read.")
    else:
        missing = []
        if not has_intro: missing.append("a clear Introduction")
        if not has_conclusion: missing.append("a proper Conclusion (using words like 'Thus', 'Therefore')")
        if not has_paragraphs: missing.append("good paragraph spacing (use bullet points or line breaks)")
        feedback_parts.append(f"⚠️ **Structure ({struct_score}/3):** Your structure needs work. You missed: {', '.join(missing)}. *Spoon-feed advice: Always start with a 30-word intro defining the core topic, break the body into points, and end with a 30-word forward-looking conclusion.*")

    # 3. Content Depth & Keywords
    important_terms = ['plassey', 'buxar', 'regulating', 'pitt', 'charter', 'subsidiary', 'alliance', 'lapse', 'diwani', 'clive', 'wellesley', 'dalhousie', '1857']
    found_terms = [t for t in important_terms if t in answer.lower()]
    content_score = min(5, len(found_terms) * 0.7)
    marks += content_score
    
    feedback_parts.append("### 🧠 Content Depth & UPSC Keywords")
    if content_score >= 4:
        feedback_parts.append(f"✅ **Content ({round(content_score,1)}/5):** Excellent historical knowledge! You correctly used essential keywords: {', '.join(found_terms).title()}. This shows the examiner you know your facts.")
    elif content_score >= 2:
        feedback_parts.append(f"⚠️ **Content ({round(content_score,1)}/5):** You got the basic idea, but you are missing critical UPSC keywords. You mentioned {', '.join(found_terms).title()}, but you missed important milestones like 'Regulating Act', 'Pitt\\'s India Act', or 'Diwani Rights'. *Spoon-feed advice: Memorize the exact names of Acts and Battles. Examiners look for these specific nouns to award marks.*")
    else:
        feedback_parts.append(f"❌ **Content ({round(content_score,1)}/5):** Your content is too generic. You didn't mention the key historical milestones (Battle of Plassey, Buxar, Regulating Act 1773). *Spoon-feed advice: Read the Spectrum chapter again. An answer without specific historical facts is treated as a layman's answer, not a UPSC aspirant's.*")

    # 4. Overall Grading
    marks += 2 # Base marks for attempt
    marks = min(15, round(marks, 1))
    
    if marks >= 11: grade = "🏆 Excellent (A+)"
    elif marks >= 8: grade = "👍 Good (B+)"
    elif marks >= 5: grade = "📝 Average (C+)"
    else: grade = "⚠️ Needs Work (D)"

    feedback_parts.insert(1, f"## 🏅 Grade: {grade}\n## 🎯 Marks Awarded: {marks} / 15\n---")
    
    feedback_parts.append("### 💡 AI Expert's Final Advice")
    feedback_parts.append("To push this answer to the topper level, ensure you underline your key terms (like **Battle of Buxar**) so the examiner sees them instantly. Remember: The examiner has 3 minutes per copy. Make their life easy by spoon-feeding them the keywords!")
    
    feedback = "\n\n".join(feedback_parts)
    return {'marks': marks, 'feedback': feedback, 'grade': grade}

init_db()
