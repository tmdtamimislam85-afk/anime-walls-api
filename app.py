from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import hashlib

app = Flask(__name__)
CORS(app)

# Database Path Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_STATIC = os.path.join(BASE_DIR, 'anime_walls.db')
DB_LIVE = os.path.join(BASE_DIR, 'anime_walls_live.db')
DB_ADMIN = os.path.join(BASE_DIR, 'admin.db')

def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Row fetch korle dictionary-r moto access kora jay
    return conn

# --- Admin Login API ---
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    conn = get_db_connection(DB_ADMIN)
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                        (username, hashed_password)).fetchone()
    conn.close()

    if user:
        return jsonify({"success": True, "message": "Login Successful"})
    else:
        return jsonify({"success": False, "message": "Invalid Credentials"}), 401

# --- Dashboard Stats API ---
@app.route('/api/admin/stats', methods=['GET'])
def get_stats():
    try:
        # Static Stats
        conn_static = get_db_connection(DB_STATIC)
        static_row = conn_static.execute('SELECT COUNT(*) as total, SUM(love) as love, SUM(share) as share FROM wallpapers').fetchone()
        conn_static.close()

        # Live Stats
        conn_live = get_db_connection(DB_LIVE)
        live_row = conn_live.execute('SELECT COUNT(*) as total, SUM(love) as love, SUM(share) as share FROM live_wallpapers').fetchone()
        conn_live.close()

        res = {
            "totalWallpapers": (static_row['total'] or 0) + (live_row['total'] or 0),
            "staticCount": static_row['total'] or 0,
            "liveCount": live_row['total'] or 0,
            "totalLove": (static_row['love'] or 0) + (live_row['love'] or 0),
            "totalShare": (static_row['share'] or 0) + (live_row['share'] or 0)
        }
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Wallpaper API Endpoints ---

@app.route('/api/wallpapers', methods=['GET'])
def get_wallpapers():
    conn = get_db_connection(DB_STATIC)
    rows = conn.execute('SELECT * FROM wallpapers ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/api/wallpapers/category/<name>', methods=['GET'])
def get_by_category(name):
    conn = get_db_connection(DB_STATIC)
    rows = conn.execute('SELECT * FROM wallpapers WHERE category = ?', (name,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection(DB_STATIC)
    rows = conn.execute('SELECT * FROM categories').fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/api/wallpapers/love/<int:id>', methods=['POST'])
def update_love(id):
    conn = get_db_connection(DB_STATIC)
    conn.execute('UPDATE wallpapers SET love = love + 1 WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Love count updated!"})

@app.route('/api/wallpapers/share/<int:id>', methods=['POST'])
def update_share(id):
    conn = get_db_connection(DB_STATIC)
    conn.execute('UPDATE wallpapers SET share = share + 1 WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Share count updated!"})

@app.route('/api/live-wallpapers', methods=['GET'])
def get_live_wallpapers():
    conn = get_db_connection(DB_LIVE)
    rows = conn.execute('SELECT * FROM live_wallpapers ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)