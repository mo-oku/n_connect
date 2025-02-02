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

# Notion APIの設定

def decode_base64(encoded_data):
    if encoded_data.endswith('"}]}}') :
        """いあきゃらならそのままJSONに変換"""
        json_data = json.loads(encoded_data)
        return json_data 
    else :
        """ココフォならBase64デコードしてJSONに変換"""
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
            if success : message = "✅ データ保存＆Notion送信成功"
            else:
                return render_template("index.html", message="Notion追加失敗")
        else:
            message = "⚠️ デコードエラー"
            

    # 過去のデータを取得して表示
    entries = get_entries()
    return render_template("index.html", message=message, entries=entries)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)