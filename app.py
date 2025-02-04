from flask import Flask, render_template, request, session
from flask import Flask, render_template, redirect, url_for
import requests
import base64
import json
import urllib.parse
from database import save_entry, get_entries  # データベース機能をインポート！


"""
htmlで入力→Notionに追加
"""

app = Flask(__name__)
app.secret_key = "super_secret_key"  # セッション管理用のキー
DB_NAME = "/Users/kosari/Documents/vscode/notion_data.db"

# Notion APIの設定

def decode_base64(encoded_data):
    if encoded_data.endswith('"}]}}') :
        """いあきゃらならそのままJSONに変換"""
        json_data = json.loads(encoded_data[:-2] + ',"faces": [],"color":"#888888","memo":""' + encoded_data[-2:])
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

    # ステータス情報
    status_labels = ["HP", "MP", "SAN"]
    status_values = {
        label: {"number": int(character["data"].get("status", [{}])[i].get("value", 0))}
        for i, label in enumerate(status_labels)
    }

    # パラメータ情報
    params_labels = ["STR", "CON", "POW", "DEX", "APP", "SIZ", "INT", "EDU"]
    params_values = {
        label: {"number": int(character["data"].get("params", [{}])[i].get("value", 0))}
        for i, label in enumerate(params_labels)
    }

    data = {
        "parent": {"database_id": n_database_id},
        "properties": {
            "名前": {"title": [{"text": {"content": character["data"]["name"]}}]},
            **status_values,  # HP, MP, SAN
            **params_values,  # STR, CON, ...
            "差分": {
                "files": [
                    {"name": face["label"] or f"差分{i+1}", "external": {"url": face["iconUrl"]}}
                    for i, face in enumerate(character["data"].get("faces", []))
                ]
            },
            "アイコンURL": {"url": character["data"]["iconUrl"] or None},
            "ココフォリアに貼り付け": {
                "rich_text": [{"text": {"content": json.dumps(character, ensure_ascii=False)}}]
            },
            "チャットパレット": {
                "rich_text": [{"text": {"content": character["data"]["commands"]}}]
            },
            "参照URL": {
                "url": character["data"].get("externalUrl") or None
            },
            "カラーコード": {
                "rich_text": [{"text": {"content":  '$$\color{#FFFFFF}\colorbox{' + character["data"].get("color") + '}{\\textsf{' + character["data"].get("color")[1:] + '}}$$'}}]
            }
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

"""500エラー（Internal Server Error）発生時の処理"""
@app.errorhandler(500)
def internal_server_error(e):
    return redirect(url_for('error_500_page'))

"""500エラーのリダイレクト先ページ"""
@app.route("/error_500")
def error_500_page():
    return render_template("500.html"), 500

"""例：強制的にエラーを起こす（テスト用）"""
@app.route("/cause_error")
def cause_error():
    1 / 0  # これでゼロ除算エラーを発生させる


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)