import os
from flask import Flask, render_template, request, Response, send_from_directory
from functools import wraps

app = Flask(__name__, static_folder='static', template_folder='.')

# ==========================================
# 1. 安全設定：管理後台帳號密碼
# ==========================================
ADMIN_USER = "admin"
ADMIN_PASSWORD = "你的密碼"  # <--- 請在此修改您的管理密碼

def check_auth(username, password):
    """檢查帳號密碼是否正確"""
    return username == ADMIN_USER and password == ADMIN_PASSWORD

def authenticate():
    """傳送 401 回應，觸發瀏覽器跳出登入視窗"""
    return Response(
        '管理員認證失敗，請輸入正確的帳號密碼。', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    """認證裝飾器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ==========================================
# 2. 路由設定 (Routes)
# ==========================================

# 首頁：藝廊展示頁
@app.route('/')
def index():
    # 確保您的 index.html 放在與 app.py 同層級或 templates 資料夾中
    return render_template('index.html')

# 管理後台：需要密碼認證
@app.route('/admin')
@requires_auth
def admin_page():
    # 確保您的 admin.html 檔案存在
    return render_template('admin.html')

# 解決 Favicon 找不到的問題
@app.route('/favicon.ico')
def favicon():
    # 假設您的 favicon 放在 static/images/favicon.ico
    return send_from_directory(os.path.join(app.root_path, 'static', 'images'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# ==========================================
# 3. 啟動程式
# ==========================================
if __name__ == '__main__':
    # 在 Render 部署時，通常會由 gunicorn 啟動，此處為本地測試用
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)