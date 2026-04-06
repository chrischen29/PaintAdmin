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

# --- 1. 設定區 ---
IMGBB_API_KEY = "bebac0016394472c839f571f730b34e1"
SHEET_ID = "1EPiV8x-LYpPA0loGib2Se69tsdhvHLrZ_pvLZW65USo"
RANGE_NAME = "工作表1!A:Q"

# --- 2. 直接嵌入新產生的金鑰 (Service Account Info) ---
SERVICE_ACCOUNT_INFO = {
  "type": "service_account",
  "project_id": "mcsa2-1251",
  "private_key_id": "f001dfc2893c6bb97fb54d2b9846ab5e970ec52c",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC/NZjEaJ2vmO6a\noT4J64VYlDvzElSDkbHnJqgT3/X31jdl8f+g12Rf8SmTLqlclc9+S4gBgVh/T+Nb\nmzDGkBegaNOEg0yDxwZJCeK1f9ld+E7YU2uRKfOO28xDnbndzMngK554ixW2vFF9\nHKD4MnJXV0pPVArD1ovU9kNDLVnY/D2ejF7VtHWO8my4H6n6wrPIz2rdaT/PH3IJ\nU+QbylfY3UhJtAXn4Nu5e4RyFsWCVxi+uPqXFjLSpOgQ/jZXfiatkUo+lIMBsqj+\nLsu0Fi23af0EzNNd7w/AilDkVFD2vNALSBarvXPufbCep/fZkPdUHJDCrdz8Xzpz\nBQYF086hAgMBAAECggEALuzE2oLAHA2AlRM4KfAScAwk8EDR294gFlW+zu3aK+H3\nA35R2VOy7va82MGNT8r2OoznylLHeKsO5XbfEAPhwHypWC5u0zI/QSJ7cEZ5fl3H\nX8CNN/lfK/KWHQvyxtOQwYKC6BteD1QE/ZrOiEq9E+E4u+IoqCoZdAChvjU9hQnp\nIyHDc1pHP04gvsYJTl690ax9HpIP2o4ZfoZDt1V6eXfP3XpCTscr0WO9T1pprJnw\nSjCf+1cXgOPBceKJGOmYPsuH8vpai3e3WIv92oZV5p+Rp3wpY7E0q9R93Qfj/j+3\nVzTm5spO8VUDZSvJDDbsPFwx/PBIQzbDjgDOEa1xDwKBgQD0nN7KpcVKJ9lNBpFp\ntTmUyMkR7ruSKtfdmPqgi29twE4A6Zl58nhlH4wJhq5NiLyfy1NgFHKOcEcvLMYg\n96ALrqmH8Ug0LUBFm1wySXZs0w0N5ZDEdxTsFaZllE0sMn53ZRKVHFXsnMpuaoai\nQ2fIY64brgSqqERZAy70LSdFRwKBgQDIHEz6SNk8Ar5tpfi77H7cEBJ2pfeMy5ZT\n/T3Deo/POJaEBbOVX3aCKfuZBFq1QUaLUR39k+6Kr8gtZKtGTdCS0/8vUR8MOnJD\njEfonnBITE0TjhVDPzaki9+ia6//fq7mxdUEE3KsuMFPRLyVqQHKLCs3+z7H3kFv\nY0WjaDJg1wKBgQDb9riteDYaQg05I5/dc9bMwWV2V7yaayZkoe02M0zHX7eFQIr/\nyxeSr7So2FCjbkNYWmmmK5z8E2Efvd6IxMRJ3Q2cLk+kg9CZB2T333G72GmTxozQ\n7tiEl89i5uIizWFGEk8eAl1m9wtNA1OZdn61wPKL7p4aWmLM/Zd87fwKBgFW3\nCaILokF6S2dcOHcGjjBlEgOQg8DjU7kWOGaLER6J9q8GYi4RfgmzQfoBS3loRHdY\nf6gmvX7aXLxU6qhqnHTIKf5ymQH75wXYCNUzSJUvWbSOn7z2TsmcwGYqCnE+Klzf\nUKc2TWB+ow75Om5AvmuDD+Ai1nl2UkEMHMAp2apxAoGBAOmXN999lNoq93BldBa6\n7ez22S1vJmSvWguf1hb2vCOLIR50rv/8UK+pHimjWOQst28wPhHuuiopwUVrXH1f\nPF9I8Hr2QQ3CUNqtCgI+sxOvUi+kNV7VNj2EdU3AlMob+UjdcAFln4AxB7vxJiw2\nFcA6YgmTiZwuzRGqoXqeWcmN\n-----END PRIVATE KEY-----\n",
  "client_email": "paintadmin@mcsa2-1251.iam.gserviceaccount.com",
  "client_id": "117010667496967706837",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/paintadmin%40mcsa2-1251.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

def get_sheets_service():
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scope)
    return build('sheets', 'v4', credentials=creds)

def get_artist_info():
    # 這裡顯示畫家的基本資訊
    return {
        "artist_name": "Helen Hu",
        "bank_code": "822 (中國信託)",
        "bank_user": "胡海倫",
        "bank_account": "123-456789-000",
        "artist_intro": "從事藝術創作多年，擅長壓克力複合媒材，捕捉生活中的寧靜與詩意。"
    }

@app.route('/')
def index():
    return "藝廊前端施工中，請訪問 /admin"

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    service = get_sheets_service()
    error_msg = None

    if request.method == 'POST':
        action = request.form.get('action')

        # --- 新增畫作邏輯 ---
        if action == 'add_painting':
            file = request.files.get('file')
            if file:
                try:
                    # 1. 上傳至 ImgBB
                    img_base64 = base64.b64encode(file.read())
                    res = requests.post("https://api.imgbb.com/1/upload", 
                                        data={"key": IMGBB_API_KEY, "image": img_base64}).json()
                    img_url = res['data']['url']

                    # 2. 準備 17 個欄位的資料
                    new_id = f"p{int(time.time())}"
                    new_row = [
                        new_id, request.form.get('name'), request.form.get('price'),
                        request.form.get('size'), request.form.get('material'), img_url,
                        "", request.form.get('poetic_text'), "", "", "", "",
                        request.form.get('display_date'), request.form.get('finish'),
                        "", "", ""
                    ]

                    # 3. 寫入 Google Sheets
                    body = {'values': [new_row]}
                    service.spreadsheets().values().append(
                        spreadsheetId=SHEET_ID, range=RANGE_NAME,
                        valueInputOption="USER_ENTERED", body=body).execute()
                    return redirect(url_for('admin'))
                except Exception as e:
                    error_msg = f"操作失敗: {str(e)}"

        # --- 刪除畫作邏輯 ---
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
                return redirect(url_for('admin'))
            except Exception as e:
                error_msg = f"刪除失敗: {str(e)}"

    # 讀取畫作清單
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
        error_msg = f"連線失敗: {str(e)}"

    return render_template('admin.html', paintings=paintings, info=get_artist_info(), error_msg=error_msg)

if __name__ == '__main__':
    app.run(debug=True)