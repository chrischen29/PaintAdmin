import os
import json
import time
from flask import Flask
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

# 試算表資訊
SHEET_ID = "1EPiV8x-LYpPA0loGib2Se69tsdhvHLrZ_pvLZW65USo"
RANGE_NAME = "工作表1!A:Q"

def get_sheets_service():
    # 從 Render 環境變數讀取
    creds_json = os.environ.get('GOOGLE_CREDS_JSON')
    if not creds_json:
        return None
    
    try:
        info = json.loads(creds_json)
        # 關鍵：自動修正私鑰中的換行符號，防止 Signature 錯誤
        if 'private_key' in info:
            info['private_key'] = info['private_key'].replace('\\n', '\n')
            
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        return build('sheets', 'v4', credentials=creds)
    except Exception as e:
        print(f"解析錯誤: {e}")
        return None

@app.route('/test_add')
def test_add():
    service = get_sheets_service()
    if not service:
        return "失敗：找不到環境變數或 JSON 格式錯誤。"

    try:
        # 準備一筆測試資料
        test_row = [
            f"test_{int(time.time())}", # ID
            "連線測試作品",              # 名稱
            "0",                        # 價格
            "測試規格",                  # 尺寸
            "數位測試",                  # 媒材
            "https://via.placeholder.com/150", # 假圖片路徑
            "", "", "", "", "", "", 
            "2026-04-07",               # 日期
            "已完成"                     # 狀態
        ]
        
        service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, 
            range=RANGE_NAME,
            valueInputOption="USER_ENTERED", 
            body={'values': [test_row]}
        ).execute()
        
        return "✅ 成功！請查看 Google Sheets，應該已經多了一列資料。"
    except Exception as e:
        return f"❌ 寫入失敗。錯誤訊息：{str(e)}"

if __name__ == '__main__':
    app.run(debug=True)