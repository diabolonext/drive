from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, abort
import os
import json
from werkzeug.utils import secure_filename
from urllib.parse import quote

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 使用 JSON 檔案儲存帳號密碼
USER_FILE = 'users.json'

# 確認使用者登入狀態
def check_login(username, password):
    if not os.path.exists(USER_FILE):
        return False
    with open(USER_FILE, 'r', encoding='utf-8') as f:
        users = json.load(f)
    return users.get(username) == password

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if check_login(username, password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='帳號或密碼錯誤')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # 處理多檔及資料夾上傳
        files = request.files.getlist('file')
        for f in files:
            if f.filename == '':
                continue
            # 把 Windows 路徑的反斜線轉成斜線
            raw_path = f.filename.replace('\\', '/')
            # 拆解路徑並建立資料夾
            parts = raw_path.split('/')
            filename = secure_filename(parts[-1])
            folder_path = os.path.join(UPLOAD_FOLDER, *parts[:-1])
            os.makedirs(folder_path, exist_ok=True)
            save_path = os.path.join(folder_path, filename)
            f.save(save_path)

    # 列出 uploads 目錄所有檔案
    file_list = []
    for root, dirs, files in os.walk(UPLOAD_FOLDER):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, UPLOAD_FOLDER).replace('\\', '/')
            size_kb = os.path.getsize(full_path) / 1024
            file_list.append({
                'name': rel_path,
                'size': f'{size_kb:.2f}'
            })

    return render_template('index.html', files=file_list)

@app.route('/download/<path:filename>')
def download(filename):
    if 'username' not in session:
        return redirect(url_for('login'))

    # 防止路徑穿越攻擊
    safe_path = os.path.normpath(filename).replace('\\', '/')
    full_path = os.path.join(UPLOAD_FOLDER, safe_path)
    if not os.path.isfile(full_path):
        abort(404)

    # 設定下載檔名編碼避免亂碼
    response = send_from_directory(UPLOAD_FOLDER, safe_path, as_attachment=True)
    response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(os.path.basename(safe_path))}"
    return response

@app.route('/delete/<path:filename>', methods=['POST'])
def delete(filename):
    if 'username' not in session:
        return redirect(url_for('login'))

    safe_path = os.path.normpath(filename).replace('\\', '/')
    full_path = os.path.join(UPLOAD_FOLDER, safe_path)
    if os.path.isfile(full_path):
        os.remove(full_path)
    return redirect(url_for('index'))

@app.route('/ping')
def ping():
    return 'pong', 200

# 🧠 定時 ping 自己保持活著
def keep_alive():
    while True:
        try:
            requests.get('https://your-app.onrender.com/ping')
        except:
            pass
        time.sleep(300)  # 每 10 分鐘 ping 一次


if __name__ == '__main__':
    app.run(debug=True)
