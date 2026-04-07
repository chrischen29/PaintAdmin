import os
import base64
import time
import requests
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'helen_art_secret_key'

# --- 設定區 ---
IMGBB_API_KEY = "bebac0016394472c839f571f730b34e1"
GAS_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbx-CX_AKQ_XbD3QUCBwZLG71hkU5HdcfpUolN9FmwRir0GUio3JBgPUPcBWJ2Vfd36pOw/exec"

def get_artist_info():
    return {"artist_name": "Helen Hu"}

@app.route('/')
def index():
    return redirect(url_for('admin'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error_msg = None
    paintings = []

    if request.method == 'POST':
        action = request.form.get('action')
        
        # --- 刪除功能 ---
        if action == 'delete_painting':
            payload = {"action": "delete", "id": request.form.get('id')}
            requests.post(GAS_WEB_APP_URL, json=payload, timeout=15)
            return redirect(url_for('admin'))

        # --- 編輯功能 ---
        elif action == 'edit_painting':
            payload = {
                "action": "update",
                "id": request.form.get('id'),
                "name": request.form.get('name'),
                "price": request.form.get('price'),
                "size": request.form.get('size'),
                "material": request.form.get('material'),
                "description_short": request.form.get('description_short'),
                "poetic_text": request.form.get('poetic_text'),
                "notices": request.form.get('notices'),
                "lead_time": request.form.get('lead_time'),
                "frame_time": request.form.get('frame_time'),
                "hand_painted_disclaimer": request.form.get('hand_painted_disclaimer'),
                "display_date": request.form.get('display_date'),
                "finish": request.form.get('finish')
            }
            requests.post(GAS_WEB_APP_URL, json=payload, timeout=15)
            return redirect(url_for('admin'))

        # --- 新增功能 ---
        elif action == 'add_painting':
            file = request.files.get('file')
            if file:
                try:
                    img_base64 = base64.b64encode(file.read())
                    res = requests.post("https://api.imgbb.com/1/upload", data={"key": IMGBB_API_KEY, "image": img_base64}).json()
                    img_url = res['data']['url']

                    payload = {
                        "action": "add",
                        "id": f"painting{int(time.time())}",
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
                    requests.post(GAS_WEB_APP_URL, json=payload, timeout=15)
                    return redirect(url_for('admin'))
                except Exception as e:
                    error_msg = f"操作失敗: {str(e)}"

    # --- 讀取功能 ---
    try:
        res = requests.get(GAS_WEB_APP_URL, timeout=15)
        if res.status_code == 200:
            rows = res.json()
            for r in rows:
                if len(r) > 5:
                    paintings.append({
                        'id': r[0], 'name': r[1], 'price': r[2], 'size': r[3],
                        'material': r[4], 'image_url': r[5], 'description_short': r[6],
                        'poetic_text': r[7], 'notices': r[8], 'lead_time': r[9],
                        'frame_time': r[10], 'hand_painted_disclaimer': r[11],
                        'display_date': r[12], 'finish': r[13]
                    })
            paintings.reverse()
    except Exception as e:
        error_msg = f"資料加載失敗: {str(e)}"

    return render_template('admin.html', paintings=paintings, error_msg=error_msg)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)