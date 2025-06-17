from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import json
import os

app = Flask(__name__)

# ===== ใส่ Token และ Secret ของคุณ =====
CHANNEL_ACCESS_TOKEN = "ใส่ Channel Access Token ของคุณที่นี่"
CHANNEL_SECRET = "ใส่ Channel Secret ของคุณที่นี่"

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# ==== ใช้ path แบบสมบูรณ์เพื่อความชัวร์ ====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_ID_FILE = os.path.join(BASE_DIR, "user_ids.json")

def load_user_ids():
    try:
        with open(USER_ID_FILE, "r") as f:
            user_ids = json.load(f)
            print(f"[DEBUG] โหลด user_ids: {user_ids}")
            return user_ids
    except Exception as e:
        print(f"[ERROR] โหลด user_ids ไม่ได้: {e}")
        return []

def save_user_ids(user_ids):
    try:
        with open(USER_ID_FILE, "w") as f:
            json.dump(user_ids, f)
            print(f"[DEBUG] บันทึก user_ids แล้ว: {user_ids}")
    except Exception as e:
        print(f"[ERROR] บันทึก user_ids ไม่ได้: {e}")

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    print(f"[DEBUG] รับข้อความจาก user_id: {user_id}")

    user_ids = load_user_ids()

    if user_id not in user_ids:
        user_ids.append(user_id)
        save_user_ids(user_ids)
    else:
        print(f"[DEBUG] user_id นี้มีอยู่แล้ว: {user_id}")

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"สวัสดี! คุณคือ {user_id}")
    )

def notify_all_users(text):
    user_ids = load_user_ids()
    for uid in user_ids:
        try:
            line_bot_api.push_message(uid, TextSendMessage(text=text))
        except Exception as e:
            print(f"[ERROR] ส่งข้อความไปยัง {uid} ไม่สำเร็จ: {e}")

if __name__ == "__main__":
    app.run(port=5000)
