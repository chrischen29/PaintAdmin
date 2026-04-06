import os
import json
import base64
import time
import requests
from flask import Flask, render_template, request, redirect, url_for, session
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = 'helen_art_secret_key'

# --- 設定區 ---
IMGBB_API_KEY = "bebac0016394472c839f571f730b34e1"
SHEET_ID = "1EPiV8x-LYpPA0loGib2Se69tsdhvHLrZ_pvLZW65USo"
RANGE_NAME = "工作表1!A:Q"  # A 到 Q 剛好 17 欄

# Google Sheets 服務初始化
def get_sheets_service():
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    # 確保 credentials.json 已上傳至 GitHub 根目錄
    creds = service_account.Credentials.from_service_account_file('credentials.json', scopes=scope)
    return build('sheets', 'v4', credentials=creds)

# 模擬畫家基本資訊 (未來可改為存在 Sheets 的另一個分頁)
def get_artist_info():
    return {
        "artist_name": "Helen Hu",
        "bank_code": "822 (中國信託)",
        "bank_user": "胡海倫",
        "bank_account": "123-456789-000",
        "artist_intro": "從事藝術創作多年，擅長壓克力複合媒材..."
    }

@app.route('/')
def index():
    return "藝廊前端頁面施工中，請訪問 /admin"

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # 這裡可以加上簡單的登入檢查，若未登入則 redirect 到 login
    service = get_sheets_service()

    if request.method == 'POST':
        action = request.form.get('action')

        # --- 功能 A：新增畫作 ---
        if action == 'add_painting':
            file = request.files.get('file')
            if file:
                # 1. 上傳到 ImgBB
                img_base64 = base64.b64encode(file.read())
                res = requests.post("https://api.imgbb.com/1/upload", 
                                    data={"key": IMGBB_API_KEY, "image": img_base64}).json()
                img_url = res['data']['url']

                # 2. 準備資料列 (對應你的 17 個欄位)
                new_id = f"painting_{int(time.time())}" # 產生簡單唯一 ID
                new_row = [
                    new_id,                             # id
                    request.form.get('name'),           # name
                    request.form.get('price'),          # price
                    request.form.get('size'),           # size
                    request.form.get('material'),       # material
                    img_url,                            # image_url
                    "（無框畫...）",                     # description_short (可設預設值)
                    request.form.get('poetic_text'),    # poetic_text
                    "1. 嚴禁碰觸酒精...",                # notices
                    "20工作天",                         # lead_time
                    "3-5工作天",                        # frame_time
                    "由於畫作都是手繪...",                # hand_painted_disclaimer
                    request.form.get('display_date'),   # display_date
                    request.form.get('finish'),         # finish (Y/N)
                    "", "", ""                          # other1, 2, 3
                ]

                # 3. 寫入 Google Sheets
                body = {'values': [new_row]}
                service.spreadsheets().values().append(
                    spreadsheetId=SHEET_ID, range=RANGE_NAME,
                    valueInputOption="USER_ENTERED", body=body).execute()
                
            return redirect(url_for('admin'))

        # --- 功能 B：刪除畫作 ---
        elif action == 'delete_painting':
            target_id = request.form.get('id')
            # 讀取所有資料找出哪一行要刪
            result = service.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=RANGE_NAME).execute()
            values = result.get('values', [])
            
            for index, row in enumerate(values):
                if row and row[0] == target_id:
                    # 執行刪除列動作 (index 是從 0 開始，Sheets 列號從 1 開始)
                    delete_request = {
                        "requests": [{
                            "deleteDimension": {
                                "range": {
                                    "sheetId": 0, # 通常第一個分頁 ID 是 0
                                    "dimension": "ROWS",
                                    "startIndex": index,
                                    "endIndex": index + 1
                                }
                            }
                        }]
                    }
                    service.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body=delete_request).execute()
                    break
            return redirect(url_for('admin'))

    # --- GET 請求：讀取並顯示列表 ---
    sheet_data = service.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=RANGE_NAME).execute()
    rows = sheet_data.get('values', [])
    
    paintings = []
    if len(rows) > 1: # 跳過第一列標題
        for r in rows[1:]:
            # 確保索引存在，避免空列報錯
            paintings.append({
                'id': r[0] if len(r) > 0 else '',
                'name': r[1] if len(r) > 1 else '未命名',
                'image_url': r[5] if len(r) > 5 else ''
            })

    return render_template('admin.html', paintings=paintings, info=get_artist_info())

if __name__ == '__main__':
    app.run(debug=True)