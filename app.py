import os
import sqlite3
import requests
import base64
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'helen_art_secret_2026'
IMGBB_API_KEY = "bebac0016394472c839f571f730b34e1"

# --- 資料庫初始化 ---
def get_db():
    db = sqlite3.connect('database.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with get_db() as conn:
        # 作品表
        conn.execute('''CREATE TABLE IF NOT EXISTS paintings 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price TEXT, size TEXT, 
             material TEXT, poetic_text TEXT, image_url TEXT, finish TEXT, display_date TEXT)''')
        # 網站資訊表 (介紹、匯款等)
        conn.execute('''CREATE TABLE IF NOT EXISTS site_info 
            (key TEXT PRIMARY KEY, value TEXT)''')
        
        # 初始資料 (如果沒資料的話)
        count = conn.execute('SELECT count(*) FROM site_info').fetchone()[0]
        if count == 0:
            default_info = [
                ('artist_name', '胡敏慧'),
                ('artist_intro', '願我的畫可以帶給您內心的寧靜...'),
                ('bank_code', '700'),
                ('bank_account', '0311771-0085840'),
                ('bank_user', '胡敏慧')
            ]
            conn.executemany('INSERT INTO site_info VALUES (?, ?)', default_info)
    print("資料庫初始化完成")

init_db()

# --- 路由 ---

@app.route('/')
def index():
    with get_db() as conn:
        paintings = conn.execute('SELECT * FROM paintings ORDER BY display_date DESC').fetchall()
        site_info = {row['key']: row['value'] for row in conn.execute('SELECT * FROM site_info').fetchall()}
    return render_template('index.html', paintings=paintings, info=site_info)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == '123':
            session['logged_in'] = True
            return redirect(url_for('admin'))
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    with get_db() as conn:
        if request.method == 'POST':
            action = request.form.get('action')
            
            # A. 更新網站基本資訊
            if action == 'update_info':
                for key in ['artist_name', 'artist_intro', 'bank_code', 'bank_account', 'bank_user']:
                    conn.execute('UPDATE site_info SET value = ? WHERE key = ?', (request.form.get(key), key))
            
            # B. 新增作品 (包含上傳 ImgBB)
            elif action == 'add_painting':
                file = request.files.get('file')
                img_url = ""
                if file:
                    img_base64 = base64.b64encode(file.read())
                    res = requests.post("https://api.imgbb.com/1/upload", data={"key": IMGBB_API_KEY, "image": img_base64}).json()
                    if res['success']: img_url = res['data']['url']
                
                conn.execute('INSERT INTO paintings (name, price, size, material, poetic_text, image_url, finish, display_date) VALUES (?,?,?,?,?,?,?,?)',
                             (request.form.get('name'), request.form.get('price'), request.form.get('size'), 
                              request.form.get('material'), request.form.get('poetic_text'), img_url, 
                              request.form.get('finish'), request.form.get('display_date')))
            
            # C. 刪除作品
            elif action == 'delete_painting':
                conn.execute('DELETE FROM paintings WHERE id = ?', (request.form.get('id'),))
            
            conn.commit()
            return redirect(url_for('admin'))

        paintings = conn.execute('SELECT * FROM paintings ORDER BY display_date DESC').fetchall()
        site_info = {row['key']: row['value'] for row in conn.execute('SELECT * FROM site_info').fetchall()}
        return render_template('admin.html', paintings=paintings, info=site_info)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run()