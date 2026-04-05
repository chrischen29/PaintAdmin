import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory

# 1. 確保 Flask 知道靜態資料夾在哪裡AAA
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'helen_art_secret_key'

# 2. 使用「絕對路徑」來定位資料夾，避免 Render 找不到位置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 我們統一上傳到 static/images，這樣你比較好管理
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'images')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 自動建立資料夾（如果不存在）
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 這裡檢查密碼
        if request.form.get('password') == '123': 
            session['logged_in'] = True
            return redirect(url_for('admin'))
        return "密碼錯誤！"
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    message = ""
    if request.method == 'POST':
        if 'file' not in request.files:
            message = "沒有選擇檔案"
        else:
            file = request.files['file']
            if file.filename == '':
                message = "檔案名稱為空"
            else:
                # 儲存檔案到 static/images
                try:
                    filename = file.filename
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    message = f"✅ 上傳成功！網址請填：/static/images/{filename}"
                except Exception as e:
                    message = f"❌ 上傳失敗：{str(e)}"

    return f'''
        <div style="max-width:500px; margin:50px auto; font-family:sans-serif; line-height:1.6;">
            <h2>🎨 Helen Hu Art 後台管理</h2>
            <p style="color:blue; font-weight:bold;">{message}</p>
            <form method="post" enctype="multipart/form-data" style="border:1px solid #ccc; padding:20px; border-radius:10px;">
                <label>選擇畫作圖片：</label><br><br>
                <input type="file" name="file" accept="image/*" required><br><br>
                <button type="submit" style="padding:10px 20px; cursor:pointer;">開始上傳</button>
            </form>
            <hr>
            <p style="font-size:0.9em; color:#666;">提示：上傳後請複製藍色文字處的網址，填入 Google Sheets。</p>
            <a href="/">回首頁</a> | <a href="/logout">登出後台</a>
        </div>
    '''

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

# 強制開啟圖片讀取路由，確保 Render 一定能把圖丟出來
@app.route('/static/images/<path:filename>')
def serve_images(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)