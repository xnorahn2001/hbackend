# Hayat Backend API - Updated: 2026-02-26
from flask import Flask, jsonify, request
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

import sqlite3
import datetime
import os
import re

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

DB_FILE = 'hayat.db'
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:hyatdatabase24@db.wmazkbrspvdrwrummeqe.supabase.co:5432/postgres')

class CursorWrapper:
    def __init__(self, conn, is_pg):
        self.db_conn = conn
        self.is_pg = is_pg
        self.cursor = conn.cursor()

    def _convert_query(self, query):
        if self.is_pg:
            query = query.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
            query = query.replace('?', '%s')
        return query

    def execute(self, query, params=None):
        query = self._convert_query(query)
        if params is not None:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        return self

    def executemany(self, query, params_list):
        query = self._convert_query(query)
        self.cursor.executemany(query, params_list)
        return self

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    @property
    def lastrowid(self):
        if self.is_pg:
            self.cursor.execute("SELECT LASTVAL()")
            return self.cursor.fetchone()['lastval']
        return self.cursor.lastrowid

class DBConnection:
    def __init__(self):
        self.is_postgres = bool(DATABASE_URL and PSYCOPG2_AVAILABLE)
        if self.is_postgres:
            self.conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        else:
            self.conn = sqlite3.connect(DB_FILE)
            self.conn.row_factory = sqlite3.Row

    def cursor(self):
        return CursorWrapper(self.conn, self.is_postgres)

    def execute(self, query, params=None):
        return self.cursor().execute(query, params)

    def executemany(self, query, params_list):
        return self.cursor().executemany(query, params_list)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

def get_db_connection():
    return DBConnection()


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
        description TEXT,
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

    c.execute('''CREATE TABLE IF NOT EXISTS shared_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        url TEXT,
        type TEXT,
        owner TEXT,
        description TEXT,
        contentType TEXT,
        fileData TEXT,
        parentId INTEGER,
        timestamp TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS roadmap (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        category TEXT,
        status TEXT,
        priority TEXT,
        owner TEXT,
        due_date TEXT,
        start_date TEXT,
        progress INTEGER DEFAULT 0,
        parentId INTEGER,
        description TEXT,
        timestamp TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS shared_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner TEXT,
        shared_with TEXT,
        day_name TEXT,
        archived_date TEXT,
        plan_content TEXT,
        timestamp TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS common_projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        icon TEXT,
        status TEXT,
        type TEXT,
        budget TEXT,
        person TEXT,
        tags TEXT,
        endDate TEXT,
        subitems TEXT,
        timestamp TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS calendar_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        note TEXT NOT NULL,
        user TEXT,
        type TEXT,
        timestamp TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        author TEXT,
        content TEXT,
        timestamp TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS meeting_minutes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL,
        meeting_date TEXT,
        start_time TEXT,
        end_time TEXT,
        next_meeting_date TEXT,
        next_meeting_time TEXT,
        attendance TEXT,
        items TEXT,
        created_by TEXT,
        timestamp TEXT
    )''')

    # Migration: Ensure columns exist if tables already created
    try: c.execute("ALTER TABLE users ADD COLUMN last_seen TEXT")
    except: pass
    try: c.execute("ALTER TABLE users ADD COLUMN password TEXT")
    except: pass
    try: c.execute("ALTER TABLE messages ADD COLUMN is_read INTEGER DEFAULT 0")
    except: pass
    try: c.execute("ALTER TABLE tasks ADD COLUMN description TEXT")
    except: pass
    try: c.execute("ALTER TABLE tasks ADD COLUMN task_time TEXT")
    except: pass
    try: c.execute("ALTER TABLE tasks ADD COLUMN project_name TEXT")
    except: pass
    try: c.execute("ALTER TABLE tasks ADD COLUMN task_date TEXT")
    except: pass
    try: c.execute("ALTER TABLE roadmap ADD COLUMN parentId INTEGER")
    except: pass
    try: c.execute("ALTER TABLE roadmap ADD COLUMN description TEXT")
    except: pass
    try: c.execute("ALTER TABLE roadmap ADD COLUMN start_date TEXT")
    except: pass
    try: c.execute("ALTER TABLE shared_links ADD COLUMN description TEXT")
    except: pass
    try: c.execute("ALTER TABLE shared_links ADD COLUMN owner TEXT")
    except: pass
    try: c.execute("ALTER TABLE shared_links ADD COLUMN contentType TEXT")
    except: pass
    try: c.execute("ALTER TABLE shared_links ADD COLUMN fileData TEXT")
    except: pass
    try: c.execute("ALTER TABLE shared_links ADD COLUMN parentId INTEGER")
    except: pass
    
    # Calendar Enhancements
    try: c.execute("ALTER TABLE calendar_events ADD COLUMN start_time TEXT")
    except: pass
    try: c.execute("ALTER TABLE calendar_events ADD COLUMN end_time TEXT")
    except: pass
    try: c.execute("ALTER TABLE calendar_events ADD COLUMN color TEXT")
    except: pass
    try: c.execute("ALTER TABLE calendar_events ADD COLUMN guests TEXT")
    except: pass
    try: c.execute("ALTER TABLE calendar_events ADD COLUMN location TEXT")
    except: pass
    try: c.execute("ALTER TABLE calendar_events ADD COLUMN description TEXT")
    except: pass
    
    try:
        c.execute("CREATE TABLE IF NOT EXISTS common_projects (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, icon TEXT, status TEXT, type TEXT, budget TEXT, person TEXT, tags TEXT, endDate TEXT, subitems TEXT, timestamp TEXT)")
    except: pass

    # Insert Initial Users if empty
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        users = [
            ('ghada@hyat.co', 'أ. غاده', 'المدير العام', '', '#6366f1', '123456'),
            ('lina@hyat.co', 'أ. لينا', 'مدير المشاريع', '', '#ec4899', '123456'),
            ('norah@hyat.co', 'م. نورة', 'Tech Lead', '', '#10b981', '123456')
        ]
        c.executemany('INSERT INTO users (email, name, role, avatar, color, password) VALUES (?, ?, ?, ?, ?, ?)', users)
    
    conn.commit()
    conn.close()
    print("Database initialized.")

# --- API ENDPOINTS ---

@app.route('/api/users/update', methods=['PUT'])
def update_user_profile():
    data = request.json
    email = data.get('email')
    conn = get_db_connection()
    
    # Dynamic update query
    fields = []
    values = []
    
    if 'name' in data:
        fields.append("name = ?")
        values.append(data['name'])
    if 'password' in data:
        fields.append("password = ?")
        values.append(data['password'])
    if 'avatar' in data:
        fields.append("avatar = ?")
        values.append(data['avatar'])
    
    if not fields:
        return jsonify({"status": "no change"}), 200
        
    values.append(email)
    query = f"UPDATE users SET {', '.join(fields)} WHERE email = ?"
    
    conn.execute(query, values)
    conn.commit()
    
    # Return updated user
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    
    return jsonify({"status": "updated", "user": dict(user)}), 200

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
                if (now - last_seen).total_seconds() < 25: # Online if seen in last 25s
                    is_online = True
            except: pass
        d['is_online'] = is_online
        result.append(d)
    return jsonify(result)

@app.route('/api/admin/clear_all', methods=['POST'])
def clear_all_data():
    user_email = request.args.get('user_email')
    if not user_email or user_email.lower() != 'norah@hyat.co':
        return jsonify({"status": "unauthorized"}), 403
        
    conn = get_db_connection()
    # Keeping tasks, roadmap, and shared_plans as per user preference
    conn.execute('DELETE FROM shared_links')
    conn.execute('DELETE FROM messages')
    conn.execute('DELETE FROM posts')
    conn.execute('DELETE FROM common_projects')
    conn.execute('DELETE FROM calendar_events')
    conn.execute('DELETE FROM meeting_minutes')
    conn.commit()
    conn.close()
    return jsonify({"status": "cleared"}), 200

@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    email = data.get('email')
    if not email: return jsonify({"status": "error"}), 400
    conn = get_db_connection()
    conn.execute('UPDATE users SET last_seen = ? WHERE email = ?', 
                 (datetime.datetime.now(datetime.timezone.utc).isoformat(), email))
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
        c.execute('''INSERT INTO tasks 
                     (title, assigned_to, assigned_from, status, priority, type, description, subtasks, task_time, task_date, project_name, created_at) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (data.get('title'), data.get('assigned_to'), data.get('from'), 'pending', 
                   data.get('priority'), data.get('type'), data.get('details', ''), 
                   subtasks_json, data.get('taskTime'), data.get('taskDate'), data.get('project_name'),
                   datetime.datetime.now(datetime.timezone.utc).isoformat()))
        conn.commit()
        task_id = c.lastrowid
        conn.close()
        return jsonify({"status": "created", "id": task_id}), 201
    except Exception as e:
        print(f"Error adding task: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    user_email = request.args.get('user_email')
    conn = get_db_connection()
    task = conn.execute('SELECT assigned_to, assigned_from FROM tasks WHERE id = ?', (id,)).fetchone()
    
    if not task:
        conn.close()
        return jsonify({"status": "not_found"}), 404
        
    # Check permission (Owner, Sender, or GM)
    if user_email and (user_email.lower() == 'norah@hyat.co' or 
                       str(task['assigned_to']).lower() == user_email.lower() or 
                       str(task['assigned_from']).lower() == user_email.lower()):
        conn.execute('DELETE FROM tasks WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "deleted"}), 200
    
    conn.close()
    return jsonify({"status": "unauthorized"}), 403

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
    import json
    subtasks_json = json.dumps(data.get('subtasks')) if 'subtasks' in data else None
    
    conn = get_db_connection()
    conn.execute('''UPDATE tasks SET 
                    title = COALESCE(?, title),
                    assigned_to = COALESCE(?, assigned_to),
                    priority = COALESCE(?, priority),
                    type = COALESCE(?, type),
                    description = COALESCE(?, description),
                    task_time = COALESCE(?, task_time),
                    task_date = COALESCE(?, task_date),
                    project_name = COALESCE(?, project_name),
                    subtasks = COALESCE(?, subtasks)
                    WHERE id = ?''',
                 (data.get('title'), data.get('assigned_to'), data.get('priority'), data.get('type'), 
                  data.get('details'), data.get('taskTime'), data.get('taskDate'), data.get('project_name'), subtasks_json, id))
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
                 (data['from'], data['to'], data['text'], datetime.datetime.now(datetime.timezone.utc).isoformat()))
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
                 (data['from'], data['to'], data['subject'], data['text'], images_json, datetime.datetime.now(datetime.timezone.utc).isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"status": "posted"}), 201

@app.route('/api/posts/<int:id>', methods=['DELETE'])
def delete_post(id):
    user_email = request.args.get('user_email')
    conn = get_db_connection()
    post = conn.execute('SELECT sender FROM posts WHERE id = ?', (id,)).fetchone()
    
    if not post:
        conn.close()
        return jsonify({"status": "not_found"}), 404
        
    if user_email and (user_email.lower() == 'norah@hyat.co' or 
                       str(post['sender']).lower() == user_email.lower()):
        conn.execute('DELETE FROM posts WHERE id = ?', (id,))
        conn.execute('DELETE FROM comments WHERE post_id = ?', (id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "deleted"}), 200
        
    conn.close()
    return jsonify({"status": "unauthorized"}), 403

# --- SHARED LINKS API ---
@app.route('/api/links', methods=['GET'])
def get_links():
    conn = get_db_connection()
    links = conn.execute('SELECT * FROM shared_links ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(l) for l in links])

@app.route('/api/links', methods=['POST'])
def add_link():
    data = request.json
    import json
    file_data_json = json.dumps(data.get('fileData')) if data.get('fileData') else None
    
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO shared_links (name, url, type, owner, description, contentType, fileData, parentId, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (data.get('name'), data.get('url'), data.get('type', 'link'), data.get('from'), 
                      data.get('desc'), data.get('contentType'), file_data_json, data.get('parentId'), 
                      datetime.datetime.now(datetime.timezone.utc).isoformat()))
        conn.commit()
        conn.close()
        return jsonify({"status": "created"}), 201
    except Exception as e:
        print(f"Error adding link: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/links/<int:id>', methods=['PUT'])
def update_link(id):
    data = request.json
    import json
    file_data_json = json.dumps(data.get('fileData')) if data.get('fileData') else None
    conn = get_db_connection()
    conn.execute('''UPDATE shared_links SET 
                    name = COALESCE(?, name),
                    url = COALESCE(?, url),
                    description = COALESCE(?, description),
                    contentType = COALESCE(?, contentType),
                    fileData = COALESCE(?, fileData)
                    WHERE id = ?''',
                 (data.get('name'), data.get('url'), data.get('desc'), data.get('contentType'), file_data_json, id))
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"}), 200

@app.route('/api/links/<int:id>', methods=['DELETE'])
def delete_link(id):
    user_email = request.args.get('user_email')
    conn = get_db_connection()
    link = conn.execute('SELECT owner FROM shared_links WHERE id = ?', (id,)).fetchone()
    
    if not link:
        conn.close()
        return jsonify({"status": "not_found"}), 404
        
    if user_email and (user_email.lower() == 'norah@hyat.co' or 
                       str(link['owner']).lower() == user_email.lower()):
        conn.execute('DELETE FROM shared_links WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "deleted"}), 200
        
    conn.close()
    return jsonify({"status": "unauthorized"}), 403

# --- ROADMAP API ---
@app.route('/api/roadmap', methods=['GET'])
def get_roadmap():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM roadmap ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(i) for i in items])

@app.route('/api/roadmap', methods=['POST'])
def add_roadmap():
    data = request.json
    try:
        conn = get_db_connection()
        # Using .get for all fields to avoid KeyErrors
        title = data.get('title', 'مهمة جديدة')
        category = data.get('category', 'general')
        status = data.get('status', 'pending')
        priority = data.get('priority', 'medium')
        owner = data.get('owner') or data.get('from') or None
        due_date = data.get('due_date')
        start_date = data.get('start_date')
        progress = data.get('progress', 0)
        parentId = data.get('parentId')
        description = data.get('description') or data.get('desc', '')

        conn.execute('''INSERT INTO roadmap 
                     (title, category, status, priority, owner, due_date, start_date, progress, parentId, description, timestamp) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (title, category, status, priority, owner, due_date, start_date, progress, parentId, description, 
                      datetime.datetime.now(datetime.timezone.utc).isoformat()))
        conn.commit()
        conn.close()
        return jsonify({"status": "created"}), 201
    except Exception as e:
        print(f"Error in add_roadmap: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/roadmap/<int:id>', methods=['DELETE'])
def delete_roadmap(id):
    user_email = request.args.get('user_email')
    # Roadmap items are generally team-wide, but let's allow GM to delete
    if user_email and user_email.lower() == 'norah@hyat.co':
        conn = get_db_connection()
        conn.execute('DELETE FROM roadmap WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "deleted"}), 200
    
    return jsonify({"status": "unauthorized"}), 403

@app.route('/api/roadmap/<int:id>', methods=['PUT'])
def update_roadmap_item(id):
    data = request.json
    try:
        conn = get_db_connection()
        # COALESCE helps keep existing values if new ones are null
        conn.execute('''UPDATE roadmap SET 
                    title = COALESCE(?, title),
                    category = COALESCE(?, category),
                    status = COALESCE(?, status),
                    priority = COALESCE(?, priority),
                    due_date = COALESCE(?, due_date),
                    start_date = COALESCE(?, start_date),
                    progress = COALESCE(?, progress),
                    description = COALESCE(?, description)
                    WHERE id = ?''',
                 (data.get('title'), data.get('category'), data.get('status'), data.get('priority'),
                  data.get('due_date'), data.get('start_date'), data.get('progress'), 
                  data.get('description') or data.get('desc'), id))
        conn.commit()
        conn.close()
        return jsonify({"status": "updated"}), 200
    except Exception as e:
        print(f"Error in update_roadmap: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- SHARED PLANS API ---
@app.route('/api/shared_plans', methods=['POST'])
def add_shared_plan():
    data = request.json
    import json
    conn = get_db_connection()
    conn.execute('INSERT INTO shared_plans (owner, shared_with, day_name, archived_date, plan_content, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                 (data.get('owner'), data.get('shared_with'), data.get('day_name'), data.get('archived_date'), 
                  json.dumps(data.get('content')), datetime.datetime.now(datetime.timezone.utc).isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"status": "shared"}), 201

@app.route('/api/shared_plans', methods=['GET'])
def get_shared_plans():
    conn = get_db_connection()
    plans = conn.execute('SELECT * FROM shared_plans ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(p) for p in plans])

@app.route('/api/shared_plans', methods=['DELETE'])
def delete_shared_plan():
    user_email = request.args.get('user_email')
    archived_date = request.args.get('archived_date')
    
    if not user_email or not archived_date:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400
        
    conn = get_db_connection()
    conn.execute('DELETE FROM shared_plans WHERE owner = ? AND archived_date = ?', (user_email, archived_date))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"}), 200

# --- PROJECTS API ---
@app.route('/api/projects', methods=['GET'])
def get_projects():
    conn = get_db_connection()
    projects = conn.execute('SELECT * FROM common_projects ORDER BY id DESC').fetchall()
    conn.close()
    import json
    results = []
    for p in projects:
        d = dict(p)
        try:
            d['subitems'] = json.loads(d['subitems']) if d['subitems'] else []
        except:
            d['subitems'] = []
        results.append(d)
    return jsonify(results)

@app.route('/api/projects', methods=['POST'])
def add_project():
    data = request.json
    import json
    subitems_json = json.dumps(data.get('subitems', []))
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO common_projects 
                 (name, icon, status, type, budget, person, tags, endDate, subitems, timestamp) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data.get('name'), data.get('icon'), data.get('status', 'working'), data.get('type'),
               data.get('budget'), data.get('person'), data.get('tags'), data.get('endDate'),
               subitems_json, datetime.datetime.now(datetime.timezone.utc).isoformat()))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return jsonify({"status": "created", "id": new_id}), 201

@app.route('/api/projects/<int:id>', methods=['PUT'])
def update_project(id):
    data = request.json
    import json
    conn = get_db_connection()
    
    # Get existing subitems if we're only updating some fields
    if 'subitems' in data:
        subitems_json = json.dumps(data.get('subitems'))
    else:
        subitems_json = None
    
    if subitems_json is not None:
         conn.execute('''UPDATE common_projects SET 
                        name = COALESCE(?, name),
                        icon = COALESCE(?, icon),
                        status = COALESCE(?, status),
                        type = COALESCE(?, type),
                        budget = COALESCE(?, budget),
                        person = COALESCE(?, person),
                        tags = COALESCE(?, tags),
                        endDate = COALESCE(?, endDate),
                        subitems = ?
                        WHERE id = ?''',
                     (data.get('name'), data.get('icon'), data.get('status'), data.get('type'), 
                      data.get('budget'), data.get('person'), data.get('tags'), data.get('endDate'),
                      subitems_json, id))
    else:
         conn.execute('''UPDATE common_projects SET 
                        name = COALESCE(?, name),
                        icon = COALESCE(?, icon),
                        status = COALESCE(?, status),
                        type = COALESCE(?, type),
                        budget = COALESCE(?, budget),
                        person = COALESCE(?, person),
                        tags = COALESCE(?, tags),
                        endDate = COALESCE(?, endDate)
                        WHERE id = ?''',
                     (data.get('name'), data.get('icon'), data.get('status'), data.get('type'), 
                      data.get('budget'), data.get('person'), data.get('tags'), data.get('endDate'), id))
         
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"}), 200

@app.route('/api/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    user_email = request.args.get('user_email')
    conn = get_db_connection()
    proj = conn.execute('SELECT person FROM common_projects WHERE id = ?', (id,)).fetchone()
    
    if not proj:
        conn.close()
        return jsonify({"status": "not_found"}), 404
        
    if user_email and (user_email.lower() == 'norah@hyat.co' or 
                       str(proj['person']).lower() == user_email.lower()):
        conn.execute('DELETE FROM common_projects WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "deleted"}), 200
        
    conn.close()
    return jsonify({"status": "unauthorized"}), 403

# --- CALENDAR API ---
@app.route('/api/calendar', methods=['GET'])
def get_calendar():
    conn = get_db_connection()
    events = conn.execute('SELECT * FROM calendar_events ORDER BY date ASC').fetchall()
    conn.close()
    return jsonify([dict(e) for e in events])

@app.route('/api/calendar', methods=['POST'])
def add_calendar_event():
    data = request.json
    import json
    guests_str = json.dumps(data.get('guests', [])) if data.get('guests') else '[]'
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO calendar_events 
                 (date, note, user, type, timestamp, start_time, end_time, color, guests, location, description) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data.get('date'), data.get('note'), data.get('user'), data.get('type', 'event'), 
               datetime.datetime.now(datetime.timezone.utc).isoformat(),
               data.get('start_time'), data.get('end_time'), data.get('color'),
               guests_str, data.get('location'), data.get('description')))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return jsonify({"status": "created", "id": new_id}), 201

@app.route('/api/calendar/<int:id>', methods=['PUT'])
def update_calendar_event(id):
    data = request.json
    import json
    guests_str = json.dumps(data.get('guests', [])) if 'guests' in data else None
    
    conn = get_db_connection()
    conn.execute('''UPDATE calendar_events SET 
                    date = COALESCE(?, date),
                    note = COALESCE(?, note),
                    user = COALESCE(?, user),
                    type = COALESCE(?, type),
                    start_time = COALESCE(?, start_time),
                    end_time = COALESCE(?, end_time),
                    color = COALESCE(?, color),
                    guests = COALESCE(?, guests),
                    location = COALESCE(?, location),
                    description = COALESCE(?, description)
                    WHERE id = ?''',
                 (data.get('date'), data.get('note'), data.get('user'), data.get('type'), 
                  data.get('start_time'), data.get('end_time'), data.get('color'),
                  guests_str, data.get('location'), data.get('description'), id))
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"}), 200

@app.route('/api/calendar/<int:id>', methods=['DELETE'])
def delete_calendar_event(id):
    user_email = request.args.get('user_email')
    conn = get_db_connection()
    event = conn.execute('SELECT user FROM calendar_events WHERE id = ?', (id,)).fetchone()
    
    if not event:
        conn.close()
        return jsonify({"status": "not_found"}), 404
        
    if user_email and (user_email.lower() == 'norah@hyat.co' or 
                       str(event['user']).lower() == user_email.lower()):
        conn.execute('DELETE FROM calendar_events WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "deleted"}), 200
        
    conn.close()
    return jsonify({"status": "unauthorized"}), 403

@app.route('/api/meetings', methods=['GET'])
def get_meetings():
    conn = get_db_connection()
    meetings = conn.execute('SELECT * FROM meeting_minutes ORDER BY id DESC').fetchall()
    conn.close()
    import json
    results = []
    for m in meetings:
        d = dict(m)
        try:
            d['attendance'] = json.loads(d['attendance']) if d['attendance'] else []
        except: d['attendance'] = []
        try:
            d['items'] = json.loads(d['items']) if d['items'] else []
        except: d['items'] = []
        results.append(d)
    return jsonify(results)

@app.route('/api/meetings', methods=['POST'])
def add_meeting():
    try:
        data = request.json
        import json
        attendance_json = json.dumps(data.get('attendance', []))
        items_json = json.dumps(data.get('items', []))
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO meeting_minutes 
                     (subject, meeting_date, start_time, end_time, next_meeting_date, next_meeting_time, attendance, items, created_by, timestamp) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (data.get('subject'), data.get('meeting_date'), data.get('start_time'), data.get('end_time'),
                   data.get('next_meeting_date'), data.get('next_meeting_time'),
                   attendance_json, items_json, data.get('created_by'),
                   datetime.datetime.now(datetime.timezone.utc).isoformat()))
        conn.commit()
        meeting_id = c.lastrowid
        conn.close()
        return jsonify({"status": "created", "id": meeting_id}), 201
    except Exception as e:
        print(f"Error adding meeting: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/meetings/<int:id>', methods=['DELETE'])
def delete_meeting(id):
    user_email = request.args.get('user_email')
    if not user_email or user_email.lower() != 'norah@hyat.co':
        return jsonify({"status": "unauthorized"}), 403
        
    conn = get_db_connection()
    conn.execute('DELETE FROM meeting_minutes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"}), 200

init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Serving on http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', debug=True, port=port)
