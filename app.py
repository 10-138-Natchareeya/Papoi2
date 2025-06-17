from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import json, os

app = Flask(__name__)

# === ตั้งค่า LINE BOT ===
CHANNEL_ACCESS_TOKEN = 'DDZrPqONwXOHWy4QbwBIM/8a41lHz7Vae3xjK+USMOhj5ZTJQ7nB6PZjQQbNygj+S6Ip0yT+FSdQ51NykepGg8doyxMzsFm2gsU/tlMshVlXHSesnKGk2P0fApYFtcAG0fDP74qu5GDR0IU9keeZ7wdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = 'aa4928521f1fd7b44d263005bc4aa406'

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

USER_IDS_FILE = 'user_ids.json'
LATEST_SENSOR_FILE = 'latest_sensor.json'

def load_user_ids():
    if os.path.exists(USER_IDS_FILE):
        with open(USER_IDS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_user_id(user_id):
    user_ids = load_user_ids()
    if user_id not in user_ids:
        user_ids.append(user_id)
        with open(USER_IDS_FILE, 'w') as f:
            json.dump(user_ids, f)

@app.route("/sensor", methods=["POST"])
def sensor_data():
    data = request.json
    sensor_value = data.get("value", 0)

    # บันทึกค่าสุดท้าย
    with open(LATEST_SENSOR_FILE, "w") as f:
        json.dump({"value": sensor_value}, f)

    # แจ้งเตือนทุก user ถ้าค่า > 200
    if sensor_value > 200:
        message = (
            f"🚨 พบการรั่วของแก๊ส!\n"
            f"ค่า: {sensor_value} ppm\n"
            f"ระบบได้ปิดวาล์วแก๊สแล้ว"
        )
        for uid in load_user_ids():
            try:
                line_bot_api.push_message(uid, TextSendMessage(text=message))
            except Exception as e:
                print(f"ส่งข้อความล้มเหลว: {e}")

    return {'status': 'received'}

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    save_user_id(user_id)

    text = event.message.text.strip()
    sensor_value = 0
    if os.path.exists(LATEST_SENSOR_FILE):
        with open(LATEST_SENSOR_FILE, 'r') as f:
            sensor_value = json.load(f).get("value", 0)

    if text == "📊 สถานะระบบ":
        if sensor_value > 200:
            reply_text = f"🚨 พบการรั่วของแก๊ส!\nค่า: {sensor_value} ppm"
        else:
            reply_text = f"✅ ปลอดภัย\nค่า: {sensor_value} ppm"
    else:
        reply_text = "พิมพ์ '📊 สถานะระบบ' เพื่อดูค่าเซ็นเซอร์"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
