import requests
import time
import base64
import json
import urllib.parse

"""
PythoneとNotionだけでうごくやつ
Notionのデータベースを一定間隔で読み取るやつ
うまくいってない
"""

# Notion APIの設定
NOTION_API_KEY = "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"
DATABASE_ID = "18baf2e6ffba8030b751c7a442a16286"
NOTION_URL = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
NOTION_UPDATE_URL = "https://api.notion.com/v1/pages/"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def decode_base64(encoded_data):
    """Base64デコードしてJSONに変換"""
    decoded_bytes = base64.b64decode(encoded_data.removeprefix('{"kind":"encoded","data":"').removesuffix('"}'))
    decoded_str = decoded_bytes.decode("utf-8")
    decoded_str = urllib.parse.unquote(decoded_str)
    json_data = json.loads(decoded_str)
    return json_data

def get_pending_tasks():
    """Notionのデータベースから '処理待ち' のデータを取得"""
    response = requests.post(NOTION_URL, headers=HEADERS)
    data = response.json()

    pending_tasks = []
    for page in data["results"]:
        properties = page["properties"]
        status = properties["ステータス"]["select"]["name"]
        if status == "処理待ち":
            encoded_data = properties["エンコードデータ"]["rich_text"][0]["text"]["content"]
            page_id = page["id"]
            pending_tasks.append((page_id, encoded_data))

    return pending_tasks

def update_notion(page_id, decoded_data):
    """デコード結果をNotionにアップデート"""
    update_url = f"{NOTION_UPDATE_URL}{page_id}"
    properties = {
        "properties": {
            "デコード結果": {"rich_text": [{"text": {"content": json.dumps(decoded_data, indent=2, ensure_ascii=False)}}]},
            "ステータス": {"select": {"name": "完了"}}
        }
    }
    
    response = requests.patch(update_url, headers=HEADERS, json=properties)
    if response.status_code == 200:
        print(f"✅ Notionデータ更新成功: {page_id}")
    else:
        print(f"❌ 更新失敗: {response.text}")

def main():
    """定期的にNotionをチェックしてデータを処理"""
    while True:
        print("🔍 Notionのデータベースをチェック中...")
        tasks = get_pending_tasks()

        if tasks:
            for page_id, encoded_data in tasks:
                print(f"🎯 データ処理開始: {page_id}")
                decoded_data = decode_base64(encoded_data)
                update_notion(page_id, decoded_data)
        else:
            print("⏳ 処理待ちのデータなし")

        # 60秒ごとにチェック（自由に変更OK）
        time.sleep(60)

if __name__ == "__main__":
    main()
