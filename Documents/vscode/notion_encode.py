import requests

"""
Notionのエンコードデータ読み取り用だったけどうまくいかず
"""


NOTION_API_KEY = "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"
DATABASE_ID = "18baf2e6ffba8030b751c7a442a16286"

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

notion_url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

# Notion API からデータ取得
response = requests.post(notion_url, headers=headers)
data = response.json()

# 取得したデータを確認
for page in data["results"]:
    properties = page["properties"]
    encoded_data = properties["エンコードデータ"]["rich_text"][0]["text"]["content"]
    print("エンコードデータ:", encoded_data)
    print(notion_url)