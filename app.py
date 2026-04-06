import os
import requests
import base64
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'helen_art_secret_key_2026'

# --- 已自動填入你的 ImgBB API Key ---
IMGBB_API_KEY = "bebac0016394472c839f571f730b34e1"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 預設管理密碼為 123
        if request.form.get('password') == '123':
            session['logged_in'] = True
            return redirect(url_for('admin'))
        return "密碼錯誤，請重新輸入。"
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    message = ""
    permanent_url = ""
    
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename != '':
            try:
                # 讀取圖片並轉換為 Base64 格式
                img_stream = file.read()
                img_base64 = base64.b64encode(img_stream)
                
                # 呼叫 ImgBB API 上傳
                response = requests.post(
                    "https://api.imgbb.com/1/upload",
                    data={
                        "key": IMGBB_API_KEY,
                        "image": img_base64
                    }
                )
                
                json_res = response.json()
                if json_res['success']:
                    # 取得永久圖片原始網址
                    permanent_url = json_res['data']['url']
                    message = "✅ 圖片已成功儲存至雲端！"
                else:
                    message = f"❌ 上傳失敗：{json_res['error']['message']}"
            except Exception as e:
                message = f"❌ 系統錯誤：{str(e)}"

    return f'''
        <div style="max-width:600px; margin:50px auto; font-family:'Noto Sans TC', sans-serif; border:1px solid #eee; padding:40px; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.05);">
            <h2 style="text-align:center; margin-bottom:30px;">🎨 Helen Hu Art 管理後台</h2>
            
            { f'<div style="background:#f4fdf9; padding:20px; border-radius:12px; border:1px solid #ccece0; margin-bottom:30px;">'
              f'<p style="color:#198754; font-weight:bold; margin-top:0;">{message}</p>'
              f'<p style="margin-bottom:5px; font-size:0.9em;">請複製下方網址填入 Google Sheets：</p>'
              f'<code style="word-break:break-all; color:#e83e8c; display:block; background:#white; padding:10px; border:1px solid #ddd; border-radius:5px;">{permanent_url}</code>'
              f'</div>' if permanent_url else f'<p style="text-align:center; color:#666;">{message}</p>' }
            
            <form method="post" enctype="multipart/form-data">
                <div style="margin-bottom:25px;">
                    <label style="display:block; margin-bottom:10px; font-weight:600;">選擇要新增的畫作圖片：</label>
                    <input type="file" name="file" accept="image/*" required style="width:100%; padding:10px; border:1px solid #ddd; border-radius:8px;">
                </div>
                <button type="submit" style="width:100%; background:#333; color:#fff; padding:15px; border:none; border-radius:10px; cursor:pointer; font-size:16px; font-weight:bold; transition:0.3s;">
                    立即上傳並產生永久網址
                </button>
            </form>
            
            <div style="text-align:center; margin-top:40px; border-top:1px solid #eee; padding-top:20px;">
                <a href="/" style="color:#888; text-decoration:none; font-size:0.9em; margin:0 15px;">回藝廊首頁</a>
                <a href="/logout" style="color:#888; text-decoration:none; font-size:0.9em; margin:0 15px;">登出系統</a>
            </div>
        </div>
    '''

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    # 這裡的 debug=True 僅供開發測試使用
    app.run()