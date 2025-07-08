import requests
import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# === Настройки ===
OWNER_ID = -231062776               # ID группы
API_VERSION = '5.131'
CHECK_INTERVAL = 37 * 60            # 37 минут
ACCESS_TOKEN = "vk1.a."  
MY_ID = 1057444023                  # user_id

COMMENTED_FILE = "commented.txt"

# === Комментарии ===
def get_first_comment():
    try:
        with open("comments.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            print("⚠️ Файл comments.txt пуст.")
            return None
        return lines[0]
    except Exception as e:
        print("Ошибка чтения comments.txt:", e)
        return None

def remove_first_comment_line():
    try:
        with open("comments.txt", "r", encoding="utf-8") as f:
            lines = [line for line in f if line.strip()]
        if len(lines) <= 1:
            open("comments.txt", "w", encoding="utf-8").close()
        else:
            with open("comments.txt", "w", encoding="utf-8") as f:
                f.writelines(lines[1:])
    except Exception as e:
        print("Ошибка при удалении первой строки comments.txt:", e)

# === Работа с постами ===
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

def is_commented_by_bot(post_id):
    r = requests.get("https://api.vk.com/method/wall.getComments", params={
        "owner_id": OWNER_ID,
        "post_id": post_id,
        "count": 100,
        "access_token": ACCESS_TOKEN,
        "v": API_VERSION
    })
    data = r.json()
    try:
        comments = data["response"]["items"]
        for c in comments:
            if c["from_id"] == MY_ID:
                return True
    except Exception as e:
        print(f"Ошибка проверки комментариев к посту {post_id}:", e)
    return False

def post_comment(post_id, msg):
    r = requests.get("https://api.vk.com/method/wall.createComment", params={
        "owner_id": OWNER_ID,
        "post_id": post_id,
        "message": msg,
        "access_token": ACCESS_TOKEN,
        "v": API_VERSION
    })
    print(f"📩 Комментарий к посту {post_id} → {r.json()}")

# === Основной цикл ===
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
            msg = get_first_comment()
            if msg:
                print(f"💬 Комментируем пост {pid}: {msg}")
                post_comment(pid, msg)
                save_commented_id(pid)
                remove_first_comment_line()
            else:
                print("❌ Нет доступного комментария.")
            time.sleep(2)

        print(f"🕒 Ожидание {CHECK_INTERVAL // 60} минут...")
        time.sleep(CHECK_INTERVAL)

# === HTTP-заглушка для Render/Web ===
class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"VK bot is running.")

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("", port), PingHandler)
    print(f"✅ HTTP сервер на порту {port}")
    server.serve_forever()

# === Запуск ===
if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    run_bot_loop()
