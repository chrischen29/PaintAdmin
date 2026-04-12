import os
import base64
import time
import requests
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
# 建議未來將此改為環境變數以提高安全性
app.secret_key = os.environ.get('SECRET_KEY', 'helen_art_secret_key')

# ImgBB API 配置
IMGBB_API_KEY = "bebac0016394472c839f571f730b34e1"
# Google Apps Script 佈署網址
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
        
        # --- 刪除功能 ---
        if action == 'delete_painting':
            try:
                requests.post(GAS_WEB_APP_URL, json={"action": "delete", "id": request.form.get('id')}, timeout=15)
                return redirect(url_for('admin'))
            except Exception as e:
                error_msg = f"刪除失敗: {str(e)}"

        # --- 新增或編輯功能 ---
        elif action in ['add_painting', 'edit_painting']:
            try:
                # 1. 處理圖片：優先檢查是否有新上傳的檔案
                img_url = request.form.get('old_image_url', '')
                file = request.files.get('file')
                
                if file and file.filename != '':
                    # 將檔案轉為 Base64 字串並解碼為 utf-8 格式，這是 API 要求的標準
                    img_data = file.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    
                    # 呼叫 ImgBB API
                    res = requests.post(
                        "https://api.imgbb.com/1/upload", 
                        data={"key": IMGBB_API_KEY, "image": img_base64},
                        timeout=30
                    ).json()
                    
                    if res.get('success'):
                        img_url = res['data']['url']
                    else:
                        raise Exception(f"ImgBB 錯誤: {res.get('error', {}).get('message', '上傳失敗')}")

                # 2. 準備傳送到 Google Sheets 的資料
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
                
                # 3. 同步到資料庫 (Google Sheets)
                response = requests.post(GAS_WEB_APP_URL, json=payload, timeout=25)
                if response.status_code != 200:
                    raise Exception("資料庫同步失敗，請檢查 GAS 權限")
                    
                return redirect(url_for('admin'))
                
            except Exception as e:
                error_msg = f"操作失敗: {str(e)}"

    # --- 讀取資料清單 ---
    try:
        res = requests.get(GAS_WEB_APP_URL, timeout=15)
        if res.status_code == 200:
            rows = res.json()
            # 確保欄位長度足夠，避免 IndexError
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
            paintings.reverse() # 讓最新的作品排在上面
        else:
            error_msg = "資料庫讀取異常"
    except Exception as e:
        error_msg = f"無法連接到資料庫: {str(e)}"

    return render_template('admin.html', paintings=paintings, error_msg=error_msg)

if __name__ == '__main__':
    # 支援 Render 部署的 Port 設定
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)