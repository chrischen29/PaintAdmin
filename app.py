import os
import json
import base64
import time
import requests
from flask import Flask, render_template, request, redirect, url_for
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = 'helen_art_secret_key'

# --- 設定區 ---
IMGBB_API_KEY = "bebac0016394472c839f571f730b34e1"
# 已更新為你提供的新連結 ID
SHEET_ID = "1EPiV8x-LYpPA0loGib2Se69tsdhvHLrZ_pvLZW65USo"
RANGE_NAME = "工作表1!A:Q"

def get_sheets_service():
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    # 請確保 credentials.json 檔案在 GitHub 根目錄
    creds = service_account.Credentials.from_service_account_file('credentials.json', scopes=scope)
    return build('sheets', 'v4', credentials=creds)

def get_artist_info():
    return {
        "artist_name": "Helen Hu",
        "bank_code": "822 (中國信託)",
        "bank_user": "胡海倫",
        "bank_account": "123-456789-000",
        "artist_intro": "從事藝術創作多年..."
    }

@app.route('/')
def index():
    return "藝廊前端施工中，請訪問 /admin"

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    try:
        service = get_sheets_service()
    except Exception as e:
        return f"Google API 初始化失敗，請檢查 credentials.json 是否正確。錯誤訊息: {e}"

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_painting':
            file = request.files.get('file')
            if file:
                try:
                    # 1. 上傳至 ImgBB
                    img_base64 = base64.b64encode(file.read())
                    res = requests.post("https://api.imgbb.com/1/upload", 
                                        data={"key": IMGBB_API_KEY, "image": img_base64}).json()
                    img_url = res['data']['url']

                    # 2. 準備資料
                    new_id = f"painting_{int(time.time())}"
                    new_row = [
                        new_id, request.form.get('name'), request.form.get('price'),
                        request.form.get('size'), request.form.get('material'), img_url,
                        "", request.form.get('poetic_text'), "", "", "", "",
                        request.form.get('display_date'), request.form.get('finish'),
                        "", "", ""
                    ]

                    # 3. 寫入 Sheets
                    body = {'values': [new_row]}
                    service.spreadsheets().values().append(
                        spreadsheetId=SHEET_ID, range=RANGE_NAME,
                        valueInputOption="USER_ENTERED", body=body).execute()
                except Exception as e:
                    print(f"上傳或寫入失敗: {e}")
                
            return redirect(url_for('admin'))

        elif action == 'delete_painting':
            target_id = request.form.get('id')
            try:
                result = service.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=RANGE_NAME).execute()
                values = result.get('values', [])
                for index, row in enumerate(values):
                    if row and row[0] == target_id:
                        delete_req = {"requests": [{"deleteDimension": {"range": {"sheetId": 0, "dimension": "ROWS", "startIndex": index, "endIndex": index + 1}}}]}
                        service.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body=delete_req).execute()
                        break
            except Exception as e:
                print(f"刪除失敗: {e}")
            return redirect(url_for('admin'))

    # 讀取清單
    paintings = []
    try:
        sheet_data = service.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=RANGE_NAME).execute()
        rows = sheet_data.get('values', [])
        if len(rows) > 1:
            for r in rows[1:]:
                paintings.append({
                    'id': r[0] if len(r) > 0 else '',
                    'name': r[1] if len(r) > 1 else '未命名',
                    'image_url': r[5] if len(r) > 5 else ''
                })
    except Exception as e:
        # 如果發生權限錯誤，這裡會捕獲並顯示
        return f"讀取 Google Sheets 失敗。請確認是否已將試算表「共用」給服務帳號信箱。詳細錯誤: {e}"

    return render_template('admin.html', paintings=paintings, info=get_artist_info())

if __name__ == '__main__':
    app.run(debug=True)