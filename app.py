import os
import base64
import time
import requests
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'helen_art_secret_key'

IMGBB_API_KEY = "bebac0016394472c839f571f730b34e1"
GAS_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbx-CX_AKQ_XbD3QUCBwZLG71hkU5HdcfpUolN9FmwRir0GUio3JBgPUPcBWJ2Vfd36pOw/exec"

@app.route('/')
def index():
    return redirect(url_for('admin'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error_msg = None
    paintings = []

    if request.method == 'POST':
        action = request.form.get('action')
        
        # --- 刪除 ---
        if action == 'delete_painting':
            requests.post(GAS_WEB_APP_URL, json={"action": "delete", "id": request.form.get('id')})
            return redirect(url_for('admin'))

        # --- 新增或編輯 ---
        elif action in ['add_painting', 'edit_painting']:
            try:
                # 處理圖片：如果有上傳新圖則呼叫 ImgBB，否則用舊網址
                img_url = request.form.get('old_image_url', '')
                file = request.files.get('file')
                if file and file.filename != '':
                    img_base64 = base64.b64encode(file.read())
                    res = requests.post("https://api.imgbb.com/1/upload", data={"key": IMGBB_API_KEY, "image": img_base64}).json()
                    img_url = res['data']['url']

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
                    "other1": request.form.get('other1', ''),
                    "other2": request.form.get('other2', ''),
                    "other3": request.form.get('other3', '')
                }
                requests.post(GAS_WEB_APP_URL, json=payload, timeout=20)
                return redirect(url_for('admin'))
            except Exception as e:
                error_msg = f"操作失敗: {str(e)}"

    # --- 讀取 ---
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
                        'other1': r[14] if len(r)>14 else '', 'other2': r[15] if len(r)>15 else '', 'other3': r[16] if len(r)>16 else ''
                    })
            paintings.reverse()
    except:
        error_msg = "無法連接到資料庫"

    return render_template('admin.html', paintings=paintings, error_msg=error_msg)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)