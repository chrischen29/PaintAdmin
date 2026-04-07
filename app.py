import os
import sqlite3
import base64
import time
import requests
import json
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'helen_art_secret_key'

# --- 基礎設定 ---
IMGBB_API_KEY = "bebac0016394472c839f571f730b34e1"
DB_FILE = "gallery.db"

# --- 1. 資料庫初始化 ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 建立與 Google Sheets 對應的欄位 (A:Q)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS paintings (
            id TEXT PRIMARY KEY,
            name TEXT,
            price TEXT,
            size TEXT,
            material TEXT,
            image_url TEXT,
            description TEXT,
            poetic_text TEXT,
            category TEXT,
            tags TEXT,
            location TEXT,
            is_sold TEXT,
            display_date TEXT,
            finish_status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_artist_info():
    return {
        "artist_name": "Helen Hu",
        "bank_code": "822 (中國信託)",
        "bank_user": "胡海倫",
        "bank_account": "123-456789-000",
        "artist_intro": "從事藝術創作多年，擅長壓克力複合媒材，捕捉生活中的寧靜與詩意。"
    }

# --- 2. 路由設定 ---

@app.route('/')
def index():
    return redirect(url_for('admin'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    error_msg = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        # 新增畫作邏輯
        if action == 'add_painting':
            file = request.files.get('file')
            if file:
                try:
                    # 上傳至 ImgBB
                    img_base64 = base64.b64encode(file.read())
                    res = requests.post("https://api.imgbb.com/1/upload", 
                                        data={"key": IMGBB_API_KEY, "image": img_base64}).json()
                    img_url = res['data']['url']

                    # 寫入資料庫
                    new_id = f"p{int(time.time())}"
                    cursor.execute('''
                        INSERT INTO paintings (id, name, price, size, material, image_url, poetic_text, display_date, finish_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        new_id, 
                        request.form.get('name'), 
                        request.form.get('price'),
                        request.form.get('size'), 
                        request.form.get('material'), 
                        img_url,
                        request.form.get('poetic_text'),
                        request.form.get('display_date'),
                        request.form.get('finish')
                    ))
                    conn.commit()
                    return redirect(url_for('admin'))
                except Exception as e:
                    error_msg = f"上傳失敗: {str(e)}"

        # 刪除畫作邏輯
        elif action == 'delete_painting':
            target_id = request.form.get('id')
            cursor.execute('DELETE FROM paintings WHERE id = ?', (target_id,))
            conn.commit()
            return redirect(url_for('admin'))

    # 讀取畫作清單 (依時間排序)
    cursor.execute('SELECT id, name, image_url FROM paintings ORDER BY id DESC')
    rows = cursor.fetchall()
    paintings = [{'id': r[0], 'name': r[1], 'image_url': r[2]} for r in rows]
    
    conn.close()
    return render_template('admin.html', paintings=paintings, info=get_artist_info(), error_msg=error_msg)

if __name__ == '__main__':
    init_db()
    # 確保在 Render 上能運行
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)