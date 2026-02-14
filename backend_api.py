from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin requests so the HTML can talk to this server

DB_FILE = 'hayat.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Tables Initialization
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        role TEXT,
        avatar TEXT,
        color TEXT,
        last_seen TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        assigned_to TEXT,
        assigned_from TEXT,
        status TEXT DEFAULT 'pending',
        priority TEXT DEFAULT 'medium',
        type TEXT DEFAULT 'dev',
        subtasks TEXT,
        created_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        content TEXT,
        timestamp TEXT,
        is_read INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        author TEXT,
        mention TEXT,
        subject TEXT,
        content TEXT,
        images TEXT,
        timestamp TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        author TEXT,
        content TEXT,
        timestamp TEXT,
        FOREIGN KEY(post_id) REFERENCES posts(id)
    )''')

    # Migration: Ensure columns exist if tables already created
    try: c.execute("ALTER TABLE users ADD COLUMN last_seen TEXT")
    except: pass
    try: c.execute("ALTER TABLE messages ADD COLUMN is_read INTEGER DEFAULT 0")
    except: pass

    # Insert Initial Users if empty
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        users = [
            ('ghada@hyat.co', 'أ. غاده', 'المدير العام', '', '#6366f1'),
            ('lina@hyat.co', 'أ. لينا', 'مدير المشاريع', '', '#ec4899'),
            ('norah@hyat.co', 'م. نورة', 'Tech Lead', '', '#10b981')
        ]
        c.executemany('INSERT INTO users (email, name, role, avatar, color) VALUES (?, ?, ?, ?, ?)', users)
    
    conn.commit()
    conn.close()
    print("Database initialized.")

# --- API ENDPOINTS ---

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    
    if user:
        return jsonify({
            "status": "success", 
            "user": dict(user)
        }), 200
    else:
        return jsonify({"status": "error", "message": "User not found"}), 401

@app.route('/api/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    
    result = []
    now = datetime.datetime.now()
    for u in users:
        d = dict(u)
        is_online = False
        if d.get('last_seen'):
            try:
                last_seen = datetime.datetime.fromisoformat(d['last_seen'])
                if (now - last_seen).total_seconds() < 40: # Online if seen in last 40s
                    is_online = True
            except: pass
        d['is_online'] = is_online
        result.append(d)
    return jsonify(result)

@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    email = data.get('email')
    if not email: return jsonify({"status": "error"}), 400
    conn = get_db_connection()
    conn.execute('UPDATE users SET last_seen = ? WHERE email = ?', 
                 (datetime.datetime.now().isoformat(), email))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"}), 200

@app.route('/api/messages/read', methods=['POST'])
def mark_read():
    data = request.json
    sender = data.get('from')
    receiver = data.get('to')
    conn = get_db_connection()
    conn.execute('UPDATE messages SET is_read = 1 WHERE sender = ? AND receiver = ?', 
                 (sender, receiver))
    conn.commit()
    conn.close()
    return jsonify({"status": "read"}), 200

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(t) for t in tasks])

@app.route('/api/tasks', methods=['POST'])
def add_task():
    try:
        data = request.json
        print(f"Adding task: {data}")
        import json
        subtasks_json = json.dumps(data.get('subtasks', []))
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT INTO tasks (title, assigned_to, assigned_from, status, priority, type, subtasks, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                  (data['title'], data['to'], data['from'], 'pending', data['priority'], data['type'], subtasks_json, datetime.datetime.now().isoformat()))
        conn.commit()
        task_id = c.lastrowid
        conn.close()
        return jsonify({"status": "created", "id": task_id}), 201
    except Exception as e:
        print(f"Error adding task: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tasks WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"}), 200

@app.route('/api/tasks/<int:id>/status', methods=['PUT'])
def update_task_status(id):
    data = request.json
    status = data.get('status')
    conn = get_db_connection()
    conn.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, id))
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"}), 200

@app.route('/api/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    data = request.json
    conn = get_db_connection()
    conn.execute('''UPDATE tasks SET 
                    title = COALESCE(?, title),
                    assigned_to = COALESCE(?, assigned_to),
                    priority = COALESCE(?, priority),
                    type = COALESCE(?, type)
                    WHERE id = ?''',
                 (data.get('title'), data.get('to'), data.get('priority'), data.get('type'), id))
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"}), 200

# --- MESSAGES API --- (Simple implementation)
@app.route('/api/messages', methods=['GET'])
def get_messages():
    # In real app, filter by user
    conn = get_db_connection()
    msgs = conn.execute('SELECT * FROM messages ORDER BY id ASC').fetchall()
    conn.close()
    return jsonify([dict(m) for m in msgs])

@app.route('/api/messages', methods=['POST'])
def send_message():
    data = request.json
    conn = get_db_connection()
    conn.execute('INSERT INTO messages (sender, receiver, content, timestamp) VALUES (?, ?, ?, ?)',
                 (data['from'], data['to'], data['text'], datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"status": "sent"}), 201

# --- POSTS API (The Square) ---
@app.route('/api/posts', methods=['GET'])
def get_posts():
    conn = get_db_connection()
    # Fetch posts
    posts_rows = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    posts = [dict(p) for p in posts_rows]
    
    # Fetch comments for each post
    import json
    for post in posts:
        comment_rows = conn.execute('SELECT * FROM comments WHERE post_id = ? ORDER BY id ASC', (post['id'],)).fetchall()
        post['comments'] = [dict(c) for c in comment_rows]
        # Parse images JSON
        if post['images']:
            try:
                post['images'] = json.loads(post['images'])
            except:
                post['images'] = []
        else:
            post['images'] = []
            
    conn.close()
    return jsonify(posts)

@app.route('/api/posts', methods=['POST'])
def add_post():
    data = request.json
    import json
    images_json = json.dumps(data.get('images', []))
    
    conn = get_db_connection()
    conn.execute('INSERT INTO posts (author, mention, subject, content, images, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                 (data['from'], data['to'], data['subject'], data['text'], images_json, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"status": "posted"}), 201

@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    data = request.json
    conn = get_db_connection()
    conn.execute('INSERT INTO comments (post_id, author, content, timestamp) VALUES (?, ?, ?, ?)',
                 (post_id, data['from'], data['text'], datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"status": "commented"}), 201

init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Serving on http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', debug=True, port=port)
