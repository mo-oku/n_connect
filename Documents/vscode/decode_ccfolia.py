import base64
import json
import urllib.parse

"""
とにかくデコードするだけ
"""


def decode_base64(encoded_data):
    """Base64でエンコードされた駒データをデコード"""
    # 駒データをフォーマット
    # encoded_data.removeprefix('{"kind":"encoded","data":"').removesuffix('"}')

    # Base64デコード
    decoded_bytes = base64.b64decode(encoded_data.removeprefix('{"kind":"encoded","data":"').removesuffix('"}'))
    decoded_str = decoded_bytes.decode("utf-8")  # バイト列を文字列に変換

    # URLデコード（もし必要なら）
    decoded_str = urllib.parse.unquote(decoded_str)

    # JSONとして読み込む
    json_data = json.loads(decoded_str)
    return json_data

# --- テストデータ（Base64でエンコードされた駒データ） ---
encoded_data = input()
# デコード処理
character_data = decode_base64(encoded_data)

# キャラ情報を取得
name = character_data["data"]["name"]
hp = character_data["data"]["status"][0]["value"]
mp = character_data["data"]["status"][1]["value"]
san = character_data["data"]["status"][2]["value"]
icon_url = character_data["data"]["iconUrl"]

# 結果を表示
print(f"名前: {name}")
print(f"HP: {hp}, MP: {mp}, SAN: {san}")
print(f"アイコンURL: {icon_url}")
