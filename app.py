import os
import base64
import time
import requests
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'helen_art_secret_key'

# --- 1. 設定區 ---
IMGBB_API_KEY = "bebac0016394472c839f571f730b34e1"
# 已更新為你提供的 paintadmin 副本 GAS 網址
GAS_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbx-CX_AKQ_XbD3QUCBwZLG71hkU5HdcfpUolN9FmwRir0GUio3JBgPUPcBWJ2Vfd36pOw/exec"

def get_artist_info():
    return {
        "artist_name": "Helen Hu",
        "bank_code": "822 (中國信託)",
        "bank_user": "胡海倫",
        "bank_account": "123-456789-000",
        "artist_intro": "從事藝術創作多年，擅長壓克力複合媒材，捕捉生活中的寧靜與詩意。"
    }

# --- 2. 路由與邏輯 ---

@app.route('/')
def index():
    return redirect(url_for('admin'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error_msg = None
    paintings = []

    if request.method == 'POST':
        action = request.form.get('action')
        
        # --- 新增畫作 ---
        if action == 'add_painting':
            file = request.files.get('file')
            if file:
                try:
                    # A. 上傳圖片到 ImgBB
                    img_base64 = base64.b64encode(file.read())
                    res = requests.post("https://api.imgbb.com/1/upload", 
                                        data={"key": IMGBB_API_KEY, "image": img_base64}).json()
                    img_url = res['data']['url']

                    # B. 準備傳送給 GAS 的 JSON 資料
                    payload = {
                        "id": f"p{int(time.time())}",
                        "name": request.form.get('name'),
                        "price": request.form.get('price'),
                        "size": request.form.get('size'),
                        "material": request.form.get('material'),
                        "image_url": img_url,
                        "poetic_text": request.form.get('poetic_text'),
                        "display_date": request.form.get('display_date'),
                        "finish": request.form.get('finish')
                    }
                    
                    # C. 發送 POST 請求給 GAS (不需金鑰)
                    requests.post(GAS_WEB_APP_URL, json=payload, timeout=15)
                    return redirect(url_for('admin'))
                    
                except Exception as e:
                    error_msg = f"上傳或寫入失敗: {str(e)}"

    # --- 3. 從 Google Sheets (GAS) 讀取畫作清單 ---
    try:
        # 呼叫 GAS 的 doGet 方法
        res = requests.get(GAS_WEB_APP_URL, timeout=15)
        
        if res.status_code == 200:
            rows = res.json()
            if isinstance(rows, list):
                for r in rows:
                    if len(r) > 5:
                        paintings.append({
                            'id': r[0],
                            'name': r[1] if r[1] else '未命名',
                            'image_url': r[5]
                        })
                paintings.reverse()
            else:
                error_msg = "讀取失敗：回傳格式不正確，請確認 GAS 部署為『所有人』存取。"
    except Exception as e:
        error_msg = f"讀取畫作清單失敗: {str(e)}"

    return render_template('admin.html', paintings=paintings, info=get_artist_info(), error_msg=error_msg)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)