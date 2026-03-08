import os
import requests

def get_bot_details():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    return token, chat_id

def send_message(text: str) -> bool:
    token, chat_id = get_bot_details()
    if not token or not chat_id:
        print("[telegram] Not configured. Skipping alert.")
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "MarkdownV2"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"[telegram] Failed to send message: {e}")
        return False

def _esc(text):
    if not text:
        return ""
    # simple markdown v2 escaping
    reserved = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in reserved:
         text = str(text).replace(char, f"\\{char}")
    return text

def send_viral_alert(video: dict) -> bool:
    rate = video.get("rate", 0)
    if rate < 80:
        return False
        
    text = f"🔥 *VIRAL VIDEO OPPORTUNITY DETECTED* 🔥\n\n"
    text += f"*Title*: {_esc(video.get('title'))}\n"
    text += f"*Score*: {rate}/100\n"
    text += f"*Views*: {video.get('views', 0)}\n\n"
    text += f"*Hook*: {_esc(video.get('hook'))}\n\n"
    text += f"[Watch on YouTube]({_esc(video.get('link'))})"
    
    return send_message(text)
