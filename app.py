import os
from flask import Flask, render_template, request, Response, send_from_directory
from functools import wraps

# 因為你的檔案在 templates 資料夾，這裡維持預設即可
app = Flask(__name__)

# ==========================================
# 1. 帳號密碼設定 (依照你的需求設定為 123)
# ==========================================
ADMIN_USER = "admin"
ADMIN_PASSWORD = "123" 

def check_auth(username, password):
    return username == ADMIN_USER and password == ADMIN_PASSWORD

def authenticate():
    return Response(
        '管理員認證失敗，請輸入正確的帳號密碼。', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ==========================================
# 2. 路由設定
# ==========================================

# 首頁 (藝廊展示)
@app.route('/')
def index():
    # Flask 會自動去 templates/ 找 index.html
    return render_template('index.html')

# 管理後台 (密碼保護)
@app.route('/admin')
@requires_auth
def admin_page():
    # 這裡假設你的後台邏輯需要傳入 paintings 資料
    # 如果你目前只是純轉發頁面，可以先這樣寫：
    paintings = [] # 這裡應串接你讀取 CSV 的邏輯，或先給空陣列避免報錯
    return render_template('admin.html', paintings=paintings)

# 強制修復 Favicon 顯示問題
@app.route('/favicon.ico')
def favicon():
    # 從你的 GitHub 截圖看，favicon.ico 放在根目錄
    return send_from_directory(app.root_path,
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# ==========================================
# 3. 啟動 (Render 專用)
# ==========================================
if __name__ == '__main__':
    # Render 會透過環境變數指定 PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)