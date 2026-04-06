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

# --- 1. 基礎設定 ---
IMGBB_API_KEY = "bebac0016394472c839f571f730b34e1"
SHEET_ID = "1EPiV8x-LYpPA0loGib2Se69tsdhvHLrZ_pvLZW65USo"
RANGE_NAME = "工作表1!A:Q"

# --- 2. Google Sheets 服務初始化邏輯 ---
def get_sheets_service():
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    
    # 從 Render 環境變數讀取 JSON 字串
    creds_json = os.environ.get('GOOGLE_CREDS_JSON')
    
    if not creds_json:
        # 如果環境變數沒設定，嘗試讀取本地檔案 (開發測試用)
        creds_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
        if os.path.exists(creds_path):
            creds = service_account.Credentials.from_service_account_file(creds_path, scopes=scope)
            return build('sheets', 'v4', credentials=creds)
        raise ValueError("錯誤：找不到 GOOGLE_CREDS_JSON 環境變數或 credentials.json 檔案")

    try:
        # 使用 json.loads 解析，能自動處理私鑰中的 \n 換行符號，解決 Signature 錯誤
        info = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(info, scopes=scope)
        return build('sheets', 'v4', credentials=creds)
    except Exception as e:
        print(f"憑證解析失敗: {e}")
        raise e

def get_artist_info():
    return {
        "artist_name": "Helen Hu",
        "bank_code": "822 (中國信託)",
        "bank_user": "胡海倫",
        "bank_account": "123-456789-000",
        "artist_intro": "從事藝術創作多年，擅長壓克力複合媒材，捕捉生活中的寧靜與詩意。"
    }

@app.route('/')
def index():
    return redirect(url_for('admin'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error_msg = None
    paintings = []
    
    try:
        service = get_sheets_service()
    except Exception as e:
        return f"系統連線失敗：{str(e)}。請檢查 Render 環境變數設定。"

    if request.method == 'POST':
        action = request.form.get('action')
        
        # --- 新增畫作 ---
        if action == 'add_painting':
            file = request.files.get('file')
            if file:
                try:
                    img_base64 = base64.b64encode(file.read())
                    res = requests.post("https://api.imgbb.com/1/upload", 
                                        data={"key": IMGBB_API_KEY, "image": img_base64}).json()
                    img_url = res['data']['url']
                    
                    new_id = f"p{int(time.time())}"
                    new_row = [
                        new_id, request.form.get('name'), request.form.get('price'),
                        request.form.get('size'), request.form.get('material'), img_url,
                        "", request.form.get('poetic_text'), "", "", "", "",
                        request.form.get('display_date'), request.form.get('finish'),
                        "", "", ""
                    ]
                    
                    service.spreadsheets().values().append(
                        spreadsheetId=SHEET_ID, range=RANGE_NAME,
                        valueInputOption="USER_ENTERED", body={'values': [new_row]}).execute()
                    return redirect(url_for('admin'))
                except Exception as e:
                    error_msg = f"操作失敗: {str(e)}"

    # --- 讀取畫作清單 ---
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
        error_msg = f"資料讀取失敗: {str(e)}"

    return render_template('admin.html', paintings=paintings, info=get_artist_info(), error_msg=error_msg)

if __name__ == '__main__':
    app.run(debug=True)