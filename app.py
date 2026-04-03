import os
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'helen_art_secret_key'  # 安全加密用

# 設定
ADMIN_PASSWORD = '123'  # 這是你的後台預設密碼，可以自己改
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 自動建立上傳資料夾
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    # 這裡會讀取你原本的畫廊 HTML
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        return "密碼錯誤，請重試。"
    return '''
        <form method="post" style="text-align:center; margin-top:100px;">
            <h2>Helen Hu Art 管理登入</h2>
            <input type="password" name="password" placeholder="請輸入密碼">
            <button type="submit">登入</button>
        </form>
    '''

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    message = ""
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)
            message = f"成功！圖片網址為: /static/uploads/{file.filename}"

    return f'''
        <div style="max-width:500px; margin:50px auto; font-family:sans-serif;">
            <h1>畫廊後台管理</h1>
            <p style="color:green;">{message}</p>
            <form method="post" enctype="multipart/form-data">
                <input type="file" name="file" required>
                <button type="submit">上傳圖片</button>
            </form>
            <hr>
            <p>上傳後，請將網址複製到 Google Sheets 的 image_url 欄位。</p>
            <a href="/">回首頁</a> | <a href="/logout">登出</a>
        </div>
    '''

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)