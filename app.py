import os
import base64
import time
import requests
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
# 優先讀取環境變數中的 Secret Key，若無則使用預設值
app.secret_key = os.environ.get('SECRET_KEY', 'helen_art_secret_key')

# --- 設定區 ---
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
        
        # --- 刪除邏輯 ---
        if action == 'delete_painting':
            try:
                requests.post(GAS_WEB_APP_URL, json={"action": "delete", "id": request.form.get('id')}, timeout=15)
                return redirect(url_for('admin'))
            except Exception as e:
                error_msg = f"刪除失敗: {str(e)}"

        # --- 新增或編輯邏輯 ---
        elif action in ['add_painting', 'edit_painting']:
            try:
                # 初始圖片網址（若為編輯且沒傳新圖，則保留舊圖網址）
                img_url = request.form.get('old_image_url', '')
                file = request.files.get('file')
                
                # 判斷是否有新上傳的檔案
                if file and file.filename != '':
                    print(f"正在處理圖片上傳: {file.filename}")
                    
                    # 讀取並轉換為 Base64 字串 (修正關鍵：加上 .decode('utf-8'))
                    img_data = file.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    
                    # 傳送至 ImgBB
                    res = requests.post(
                        "https://api.imgbb.com/1/upload", 
                        data={"key": IMGBB_API_KEY, "image": img_base64},
                        timeout=30
                    ).json()
                    
                    # --- 偵錯 Log：在後端確認 ImgBB 的回應 ---
                    print("--- ImgBB API 回傳結果 ---")
                    print(res) 
                    
                    if res.get('success'):
                        img_url = res['data']['url']
                        print(f"圖片上傳成功！網址: {img_url}")
                    else:
                        error_detail = res.get('error', {}).get('message', '未知錯誤')
                        raise Exception(f"ImgBB 報錯: {error_detail}")

                # 組合要傳送給 Google Sheets 的 Payload
                # 我們將 img_url 同時帶入 image_url 欄位與 other1 欄位
                payload = {
                    "action": "add" if action == 'add_painting' else "update",
                    "id": request.form.get('id') if action == 'edit_painting' else f"painting{int(time.time())}",
                    "name": request.form.get('name'),
                    "price": request.form.get('price'),
                    "size": request.form.get('size'),
                    "material": request.form.get('material'),
                    "image_url": img_url,  # 更新主圖片欄位
                    "description_short": request.form.get('description_short'),
                    "poetic_text": request.form.get('poetic_text'),
                    "notices": request.form.get('notices'),
                    "lead_time": request.form.get('lead_time'),
                    "frame_time": request.form.get('frame_time'),
                    "hand_painted_disclaimer": request.form.get('hand_painted_disclaimer'),
                    "display_date": request.form.get('display_date'),
                    "finish": request.form.get('finish'),
                    "other1": img_url,      # 同步更新到 other1 欄位
                    "other2": request.form.get('other2', ''),
                    "other3": request.form.get('other3', '')
                }
                
                print(f"正在同步資料到 Google Sheets... Action: {payload['action']}")
                gas_res = requests.post(GAS_WEB_APP_URL, json=payload, timeout=25)
                print(f"Google Sheets 回應狀態碼: {gas_res.status_code}")
                
                return redirect(url_for('admin'))
                
            except Exception as e:
                print(f"發生錯誤: {str(e)}")
                error_msg = f"操作失敗: {str(e)}"

    # --- 讀取資料清單 ---
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
            error_msg = "資料庫連線異常，請檢查 GAS 佈署"
    except Exception as e:
        error_msg = f"讀取失敗: {str(e)}"

    return render_template('admin.html', paintings=paintings, error_msg=error_msg)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)