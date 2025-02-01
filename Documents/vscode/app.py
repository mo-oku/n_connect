from flask import Flask, render_template, request, session
import requests
import base64
import json
import urllib.parse
from database import save_entry, get_entries  # データベース機能をインポート！


"""
htmlで入力→Notionに追加
"""

app = Flask(__name__)
app.secret_key = "super_secret_key"  # セッション管理用のキー（適当に変更）
DB_NAME = "/Users/kosari/Documents/vscode/notion_data.db"

"""
def hash_password(password):
    # パスワードをハッシュ化（セキュリティ強化）
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(email, password):
    # 新しいユーザーをデータベースに登録
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # メールアドレスが重複している場合
    finally:
        conn.close()
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



# Notion APIの設定
"""
NOTION_API_KEY = "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"
DATABASE_ID = "18aaf2e6ffba80289323d2f3402dfa47"

NOTION_API_KEY = n_api_key
DATABASE_ID = n_database_id
"""

def decode_base64(encoded_data):
    """Base64デコードしてJSONに変換"""
    try:
        decoded_bytes = base64.b64decode(encoded_data.removeprefix('{"kind":"encoded","data":"').removesuffix('"}'))
        decoded_str = decoded_bytes.decode("utf-8")
        decoded_str = urllib.parse.unquote(decoded_str)
        json_data = json.loads(decoded_str)
        return json_data
    except Exception as e:
        return {"error": str(e)}

def add_to_notion(n_api_key, n_database_id, character):
    """Notionにデータを送信"""
    Notion_url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {n_api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    data = {
        "parent": {"database_id": n_database_id},
        "properties": {
            "名前": {"title": [{"text": {"content": character["data"]["name"]}}]},
            "HP": {"number": character["data"]["status"][0]["value"]},
            "MP": {"number": character["data"]["status"][1]["value"]},
            "SAN": {"number": character["data"]["status"][2]["value"]},
            "アイコンURL": {"url": character["data"]["iconUrl"]}
        }
    }

    response = requests.post(Notion_url, headers=headers, json=data)
    return response.status_code == 200
"""
def verify_user(email, password):
    # ユーザーのログイン認証
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, password FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()

    if user and user[1] == hash_password(password):
        return user[0]  # ユーザーIDを返す
    return None

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if register_user(email, password):
            return redirect("/login")
        else:
            return "⚠️ このメールアドレスはすでに登録されています！"

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user_id = verify_user(email, password)
        if user_id:
            session["user_id"] = user_id  # ログイン成功
            return redirect("/")
        else:
            return "⚠️ メールアドレスまたはパスワードが間違っています！"

    return render_template("login.html")

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")  # ログインしていない場合はリダイレクト

    return render_template("index.html")
"""

@app.route("/", methods=["GET", "POST"])
def index():

    message = ""

    if request.method == "POST":
        encoded_data = request.form["encoded_data"]
        decoded_data = decode_base64(encoded_data)
        n_api_key = request.form["n_api_key"]
        n_database_id = request.form["n_database_id"]


        # データベースに保存
        save_entry(n_api_key, n_database_id, encoded_data)

        # デコード処理
        decoded_data = decode_base64(encoded_data)
        if "error" not in decoded_data:
            success = add_to_notion(n_api_key, n_database_id, decoded_data)
            if success : message = "✅ データ保存＆Notion送信成功！"
            else:
                return render_template("index.html", message="Notion追加失敗！")
        else:
            message = "⚠️ デコードエラー！"
            

    # 過去のデータを取得して表示
    entries = get_entries()
    return render_template("index.html", message=message, entries=entries)

    """
        if "error" not in decoded_data:
            success = add_to_notion(n_api_key, n_database_id, decoded_data)
            if success:
                return render_template("index.html", message="Notionに追加成功！")
            else:
                return render_template("index.html", message="Notion追加失敗！")
        else:
            return render_template("index.html", message="デコードエラー！")

    return render_template("index.html", message="")
    """

"""
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/login")
"""

if __name__ == "__main__":
    app.run(debug=True)
