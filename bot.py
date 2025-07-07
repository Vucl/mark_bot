import requests
import os
import time
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

OWNER_ID = -231062776
API_VERSION = '5.131'
CHECK_INTERVAL = 37 * 60  # 37 минут
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
COMMENTED_FILE = "commented.txt"

if not ACCESS_TOKEN:
    raise RuntimeError("❌ Переменная окружения ACCESS_TOKEN не задана.")

def load_commented_ids():
    if not os.path.exists(COMMENTED_FILE):
        return set()
    with open(COMMENTED_FILE, "r") as f:
        return set(int(line.strip()) for line in f if line.strip().isdigit())

def save_commented_id(post_id):
    with open(COMMENTED_FILE, "a") as f:
        f.write(f"{post_id}\n")

def get_all_post_ids():
    ids = []
    offset = 0
    while True:
        r = requests.get("https://api.vk.com/method/wall.get", params={
            "owner_id": OWNER_ID,
            "count": 100,
            "offset": offset,
            "access_token": ACCESS_TOKEN,
            "v": API_VERSION
        })
        data = r.json()
        if "error" in data:
            print("Ошибка VK:", data)
            break
        items = data.get("response", {}).get("items", [])
        for post in items:
            if not post.get("is_pinned", 0):
                ids.append(post["id"])
        if len(items) < 100:
            break
        offset += 100
    return ids

def get_random_comment():
    try:
        with open("comments.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        return random.choice(lines) if lines else None
    except:
        return None

def is_commented_by_bot(post_id):
    r = requests.get("https://api.vk.com/method/wall.getComments", params={
        "owner_id": OWNER_ID,
        "post_id": post_id,
        "count": 100,
        "extended": 1,
        "access_token": ACCESS_TOKEN,
        "v": API_VERSION
    })
    data = r.json()
    try:
        comments = data["response"]["items"]
        profiles = data["response"]["profiles"]
        my_id = next(p["id"] for p in profiles if p["id"] > 0 and "first_name" in p)
        for c in comments:
            if c["from_id"] == my_id:
                return True
    except:
        pass
    return False

def post_comment(post_id, msg):
    r = requests.get("https://api.vk.com/method/wall.createComment", params={
        "owner_id": OWNER_ID,
        "post_id": post_id,
        "message": msg,
        "access_token": ACCESS_TOKEN,
        "v": API_VERSION
    })
    print("Комментарий к посту", post_id, "->", r.json())

def run_bot_loop():
    while True:
        print("\n🔄 Проверка публикаций")
        commented_ids = load_commented_ids()
        post_ids = get_all_post_ids()

        for pid in post_ids:
            if pid in commented_ids:
                continue
            if is_commented_by_bot(pid):
                print(f"⚠️ Уже есть комментарий от бота под постом {pid}")
                save_commented_id(pid)
                continue
            msg = get_random_comment()
            if msg:
                print(f"💬 Комментируем пост {pid}: {msg}")
                post_comment(pid, msg)
                save_commented_id(pid)
            time.sleep(2)

        print(f"🕒 Ожидание {CHECK_INTERVAL // 60} минут...")
        time.sleep(CHECK_INTERVAL)

# HTTP-заглушка для Render (порт обязательный)
class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"VK bot running.")

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("", port), PingHandler)
    print(f"✅ HTTP сервер на порту {port}")
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    run_bot_loop()
