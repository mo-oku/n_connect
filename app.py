# from flask import Flask, render_template, request, session
from flask import Flask, render_template, redirect, url_for
from flask import Flask, request, render_template
from flask import Flask, send_from_directory
from database import save_entry, get_entries
from flask import Flask, request
import requests
import base64
import json
import urllib.parse
import logging
import os


"""
htmlで入力→Notionに追加
"""

app = Flask(__name__)
app.secret_key = "super_secret_key"  # セッション管理用のキー

"""
ログ設定（ログをファイルに記録）
"""
LOG_FILE = "app.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
デコード処理
"""
def decode_base64(encoded_data):
    if encoded_data.endswith('"}]}}') :
        # いあきゃらならそのままJSONに変換
        json_data = json.loads(encoded_data[:-2] + ',"faces": [],"color":"#888888","memo":""' + encoded_data[-2:])
        return json_data
    
    else :
        # ココフォならBase64デコードしてJSONに変換
        try:
            decoded_bytes = base64.b64decode(encoded_data.removeprefix('{"kind":"encoded","data":"').removesuffix('"}'))
            decoded_str = decoded_bytes.decode("utf-8")
            decoded_str = urllib.parse.unquote(decoded_str)
            json_data = json.loads(decoded_str)
            return json_data
        
        except Exception as e:
            return {"error": str(e)}

"""
Notionにデータ送信
"""
def add_to_notion(n_api_key, n_database_id, character):
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
            "キャラクターメモ": {
                "rich_text": [{"text": {"content": character["data"].get("memo") or ""}}]
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

    # ページの作成とidの取得
    new_page = response.json()
    new_page_id = new_page["id"]

    # ページにカバー画像を追加
    add_content_url = f"https://api.notion.com/v1/pages/{new_page_id}"
    data_add = {
            "cover": {
                "type": "external",
                "external": {
                              "url": character["data"].get("iconUrl") or ""
                              }}
    }
    response = requests.patch(add_content_url, headers=headers, json=data_add)
    return response.status_code == 200


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
メイン
"""
@app.route("/", methods=["GET", "POST"])
def index():

    message = ""

    if request.method == "POST":
        encoded_data = request.form["encoded_data"]
        n_api_key = request.form["n_api_key"]
        n_database_id = request.form["n_database_id"]
        decoded_data = decode_base64(encoded_data)

        if n_api_key and n_database_id and encoded_data:

            # データベースに保存
            save_entry(n_api_key, n_database_id, encoded_data)

            # デコード処理
            decoded_data = decode_base64(encoded_data)
            if "error" not in decoded_data:
                success = add_to_notion(n_api_key, n_database_id, decoded_data)
                if success :
                    message = "✅ データ保存＆Notionに追加成功！"
                else:
                    return render_template("index.html", message="Notionへの追加失敗")
            else:
                message = "⚠️ デコードエラー"
        else:
            message = "⚠️ すべてのフィールドを入力してください"

        # ログに出力
        app.logger.info( message )
            
    # ログファイルを読み込む
    logs = []
    try:
        with open(LOG_FILE, "r") as log_file:
            logs = log_file.readlines()[-10:]  # 直近 10 件を取得
    except FileNotFoundError:
        logs = ["ログがありません。"]

    # 過去のデータを取得して表示
    entries = get_entries()
    return render_template("index.html", message=message, entries=entries, logs=logs)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
500エラー（Internal Server Error）発生時の処理
"""
@app.errorhandler(500)
def internal_server_error(e):
    # 500エラーが発生したらログをリセットする
    if os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w').close()  # ファイルの中身を空にする
    return redirect(url_for('error_500_page'))

# 500エラーのリダイレクト先ページ
@app.route("/error_500")
def error_500_page():
    return render_template("500.html"), 500


"""
1時間キャッシュ
"""
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename, cache_timeout=3600)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)