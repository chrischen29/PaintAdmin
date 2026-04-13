import os
import base64
import time
import requests
from flask import Flask, render_template, request, Response, redirect, url_for
from functools import wraps

app = Flask(__name__)
# 建議在 Render 的 Environment Variables 設定 SECRET_KEY
app.secret_key = os.environ.get('SECRET_KEY', 'helen_art_secret_key')

# --- 配置設定 ---
IMGBB_API_KEY = "bebac0016394472c839f571f730b34e1"
GAS_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbx-CX_AKQ_XbD3QUCBwZLG71hkU5HdcfpUolN9FmwRir0GUio3JBgPUPcBWJ2Vfd36pOw/exec"

# ==========================================
# 1. 管理員認證邏輯 (防止後台被隨意修改)
# ==========================================
ADMIN_USER = "admin"
ADMIN_PASSWORD = "123" 

def check_auth(username, password):
    return username == ADMIN_USER and password == ADMIN_PASSWORD

def authenticate():
    return Response(
        '管理員認證失敗，請輸入正確的帳號密碼。', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ==========================================
# 2. 路由設定
# ==========================================

# 首頁 (展示頁面)
@app.route('/')
def index():
    paintings = []
    try:
        res = requests.get(GAS_WEB_APP_URL, timeout=15)
        if res.status_code == 200:
            rows = res.json()
            for r in rows:
                if len(r) >= 6:
                    paintings.append({
                        'name': r[1],
                        'price': r[2],
                        'size': r[3],
                        'material': r[4],
                        'image_url': r[5],
                        'description_short': r[6] if len(r) > 6 else '',
                        'poetic_text': r[7] if len(r) > 7 else ''
                    })
            paintings.reverse()
    except Exception as e:
        print(f"首頁資料讀取失敗: {str(e)}")
    
    return render_template('index.html', paintings=paintings)

# 管理後台 (需輸入帳密)
@app.route('/admin', methods=['GET', 'POST'])
@requires_auth
def admin():
    error_msg = None
    paintings = []

    if request.method == 'POST':
        action = request.form.get('action')
        
        # --- A. 刪除邏輯 ---
        if action == 'delete_painting':
            try:
                requests.post(GAS_WEB_APP_URL, json={"action": "delete", "id": request.form.get('id')}, timeout=15)
                return redirect(url_for('admin'))
            except Exception as e:
                error_msg = f"刪除失敗: {str(e)}"

        # --- B. 新增或編輯邏輯 ---
        elif action in ['add_painting', 'edit_painting']:
            try:
                img_url = request.form.get('old_image_url', '')
                file = request.files.get('file')
                
                # 如果有新檔案則上傳至 ImgBB
                if file and file.filename != '':
                    img_data = file.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    
                    res = requests.post(
                        "https://api.imgbb.com/1/upload", 
                        data={"key": IMGBB_API_KEY, "image": img_base64},
                        timeout=30
                    ).json()
                    
                    if res.get('success'):
                        img_url = res['data']['url']
                    else:
                        error_detail = res.get('error', {}).get('message', '上傳失敗')
                        raise Exception(f"ImgBB 服務錯誤: {error_detail}")

                payload = {
                    "action": "add" if action == 'add_painting' else "update",
                    "id": request.form.get('id') if action == 'edit_painting' else f"painting{int(time.time())}",
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
                    "finish": request.form.get('finish'),
                    "other1": img_url,
                    "other2": request.form.get('other2', ''),
                    "other3": request.form.get('other3', '')
                }
                
                gas_res = requests.post(GAS_WEB_APP_URL, json=payload, timeout=25)
                if gas_res.status_code == 200:
                    return redirect(url_for('admin'))
                else:
                    raise Exception(f"GAS 回應錯誤碼: {gas_res.status_code}")
                
            except Exception as e:
                error_msg = f"操作失敗: {str(e)}"

    # --- C. 獲取管理清單資料 ---
    try:
        res = requests.get(GAS_WEB_APP_URL, timeout=15)
        if res.status_code == 200:
            rows = res.json()
            for r in rows:
                if len(r) >= 14:
                    paintings.append({
                        'id': r[0], 'name': r[1], 'price': r[2], 'size': r[3], 'material': r[4],
                        'image_url': r[5], 'description_short': r[6], 'poetic_text': r[7],
                        'notices': r[8], 'lead_time': r[9], 'frame_time': r[10],
                        'hand_painted_disclaimer': r[11], 'display_date': r[12], 'finish': r[13],
                        'other1': r[14] if len(r)>14 else '', 
                        'other2': r[15] if len(r)>15 else '', 
                        'other3': r[16] if len(r)>16 else ''
                    })
            paintings.reverse()
        else:
            error_msg = "無法讀取資料庫，請檢查 GAS 部署權限"
    except Exception as e:
        error_msg = f"系統連線錯誤: {str(e)}"

    return render_template('admin.html', paintings=paintings, error_msg=error_msg)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)