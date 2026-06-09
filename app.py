import os
import urllib.parse
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FollowEvent
)

app = Flask(__name__)

LINE_TOKEN  = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")

line_bot_api = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)

WELCOME_MSG = (
    "👋 嗨！歡迎來到柏君選物！\n\n"
    "🛍️ 直接在這裡「輸入商品關鍵字」，\n"
    "我馬上幫你搜尋蝦皮最便宜的商品！\n\n"
    "📌 使用說明：\n"
    "1️⃣ 直接打你想買的商品名稱\n"
    "   例如：無線耳機、氣炸鍋、運動鞋\n"
    "2️⃣ 我會回傳蝦皮搜尋連結\n"
    "3️⃣ 點連結 → 挑選商品 → 正常結帳\n\n"
    "✅ 透過我的連結購買，你「不會多付任何費用」！"
)

QUICK_KEYWORDS = {
    "3C 電子": "3C 電子",
    "美妝保養": "美妝保養",
    "居家生活": "居家生活",
    "服飾穿搭": "服飾穿搭",
    "運動健身": "運動健身",
}

def build_shopee_search_url(keyword: str) -> str:
    encoded = urllib.parse.quote(keyword)
    return f"https://shopee.tw/search?keyword={encoded}&smtt=1&sub_id=line_bot"

def build_reply(keyword: str) -> str:
    url = build_shopee_search_url(keyword)
    return (
        f"🔍 已幫你搜尋：「{keyword}」\n\n"
        f"👉 點以下連結查看蝦皮商品結果：\n"
        f"{url}\n\n"
        f"💡 小提醒：透過此連結購買價格完全相同，\n"
        f"還能順便支持我持續更新好物推薦！🙏"
    )

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK", 200

@handler.add(FollowEvent)
def handle_follow(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=WELCOME_MSG)
    )

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    keyword = event.message.text.strip()
    if not keyword:
        return
    if keyword in QUICK_KEYWORDS:
        keyword = QUICK_KEYWORDS[keyword]
    if keyword in ["使用說明", "說明", "help", "Help"]:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=WELCOME_MSG)
        )
        return
    reply_text = build_reply(keyword)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

@app.route("/", methods=["GET"])
def health():
    return "LINE Bot is running! 🚀", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
