import os
import base64
import time
import requests
from flask import Flask, render_template, request, Response, redirect, url_for, session, flash
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'helen_art_secret_key')

# --- 多資料來源配置 ---
GAS_SOURCES = {
    "Paint_Data": "https://script.google.com/macros/s/AKfycbxrf_drpmwz0GhQYNOLLYjbAmgkWGVLA-rqDpZ23G-pgjgVbwdrFBgETU82pN-8vqmS/exec",
    "paintadmin": "https://script.google.com/macros/s/AKfycbx-CX_AKQ_XbD3QUCBwZLG71hkU5HdcfpUolN9FmwRir0GUio3JBgPUPcBWJ2Vfd36pOw/exec"
}
DEFAULT_SOURCE = "Paint_Data"
IMGBB_API_KEY = "bebac0016394472c839f571f730b34e1"

# ==========================================
# 1. 管理員認證（改用 session，不用 Basic Auth）
# ==========================================
ADMIN_USER = "admin"
ADMIN_PASSWORD = "123"

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == ADMIN_USER and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = '帳號或密碼錯誤，請再試一次。'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ==========================================
# 2. 路由設定
# ==========================================

@app.route('/')
def index():
    source_key = request.args.get('source', DEFAULT_SOURCE)
    gas_url = GAS_SOURCES.get(source_key, GAS_SOURCES[DEFAULT_SOURCE])
    
    paintings = []
    try:
        res = requests.get(gas_url, timeout=15)
        if res.status_code == 200:
            rows = res.json()
            for r in rows:
                if len(r) >= 6:
                    paintings.append({
                        'name': r[1], 'price': r[2], 'size': r[3], 'material': r[4],
                        'image_url': r[5], 'description_short': r[6] if len(r) > 6 else '',
                        'poetic_text': r[7] if len(r) > 7 else ''
                    })
            paintings.reverse()
    except Exception as e:
        print(f"讀取失敗: {e}")
    return render_template('index.html', paintings=paintings, current_source=source_key)

@app.route('/admin', methods=['GET', 'POST'])
@requires_auth
def admin():
    source_key = request.args.get('source', DEFAULT_SOURCE)
    gas_url = GAS_SOURCES.get(source_key, GAS_SOURCES[DEFAULT_SOURCE])
    error_msg = None
    paintings = []

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'delete_painting':
            try:
                requests.post(gas_url, json={"action": "delete", "id": request.form.get('id')}, timeout=15)
                return redirect(url_for('admin', source=source_key))
            except Exception as e:
                error_msg = f"刪除失敗: {e}"

        elif action in ['add_painting', 'edit_painting']:
            try:
                img_url = request.form.get('old_image_url', '')
                file = request.files.get('file')
                if file and file.filename != '':
                    img_data = file.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    res = requests.post("https://api.imgbb.com/1/upload", data={"key": IMGBB_API_KEY, "image": img_base64}, timeout=30).json()
                    if res.get('success'): img_url = res['data']['url']

                payload = {
                    "action": "add" if action == 'add_painting' else "update",
                    "id": request.form.get('id') if action == 'edit_painting' else f"p{int(time.time())}",
                    "name": request.form.get('name'),
                    "price": request.form.get('price'),
                    "size": request.form.get('size'),
                    "material": request.form.get('material'),
                    "image_url": img_url,
                    "description_short": request.form.get('description_short'),
                    "poetic_text": request.form.get('poetic_text'),
                    "notices": request.form.get('notices'),
                    "lead_time": request.form.get('lead_time'),
                    "frame_time": request.form.get('frame_time'),
                    "hand_painted_disclaimer": request.form.get('hand_painted_disclaimer'),
                    "display_date": request.form.get('display_date'),
                    "finish": request.form.get('finish')
                }
                requests.post(gas_url, json=payload, timeout=25)
                return redirect(url_for('admin', source=source_key))
            except Exception as e:
                error_msg = f"操作失敗: {e}"

    try:
        res = requests.get(gas_url, timeout=15)
        if res.status_code == 200:
            rows = res.json()
            for r in rows:
                if len(r) >= 14:
                    paintings.append({
                        'id': r[0], 'name': r[1], 'price': r[2], 'size': r[3], 'material': r[4],
                        'image_url': r[5], 'description_short': r[6], 'poetic_text': r[7],
                        'notices': r[8], 'lead_time': r[9], 'frame_time': r[10],
                        'hand_painted_disclaimer': r[11], 'display_date': r[12], 'finish': r[13]
                    })
            paintings.reverse()
    except Exception as e:
        error_msg = f"連線錯誤: {e}"

    return render_template('admin.html', paintings=paintings, error_msg=error_msg, current_source=source_key, sources=GAS_SOURCES.keys())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
