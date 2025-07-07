import time
import requests
import random
import os

OWNER_ID = -231062776  # ID сообщества ВК (с минусом)
API_VERSION = '5.131'
INTERVAL_SECONDS = 3 * 3600 + 26 * 60  # 3 часа 26 минут

ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
if not ACCESS_TOKEN:
    raise RuntimeError("❌ Переменная окружения ACCESS_TOKEN не задана.")

def load_last_post_id():
    if os.path.exists("last_post.txt"):
        with open("last_post.txt", "r") as f:
            try:
                return int(f.read().strip())
            except:
                return 0
    return 0

def save_last_post_id(post_id):
    with open("last_post.txt", "w") as f:
        f.write(str(post_id))

def get_latest_post_id():
    response = requests.get("https://api.vk.com/method/wall.get", params={
        "owner_id": OWNER_ID,
        "count": 5,
        "access_token": ACCESS_TOKEN,
        "v": API_VERSION
    })
    data = response.json()
    try:
        for item in data['response']['items']:
            if not item.get('is_pinned', 0):  # игнорируем закреплённые посты
                return item['id']
    except Exception as e:
        print("Ошибка при получении поста:", data)
        return None

def get_random_comment():
    try:
        with open("comments.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            raise ValueError("Файл comments.txt пуст.")
        return random.choice(lines)
    except Exception as e:
        print("Ошибка чтения comments.txt:", e)
        return None

def post_exists(post_id):
    response = requests.get("https://api.vk.com/method/wall.getById", params={
        "posts": f"{OWNER_ID}_{post_id}",
        "access_token": ACCESS_TOKEN,
        "v": API_VERSION
    })
    data = response.json()
    if "response" in data and len(data["response"]) > 0:
        return True
    else:
        print("❌ Пост не найден или недоступен:", data)
        return False

def post_comment(post_id, message):
    response = requests.get("https://api.vk.com/method/wall.createComment", params={
        "owner_id": OWNER_ID,
        "post_id": post_id,
        "message": message,
        "access_token": ACCESS_TOKEN,
        "v": API_VERSION
    })
    print("Ответ VK на комментарий:", response.json())

def main_loop():
    while True:
        print("\n=== Проверка новых постов ===")
        last_post_id = load_last_post_id()
        latest_post_id = get_latest_post_id()

        if latest_post_id is None:
            print("❌ Не удалось получить ID последнего поста.")
        elif latest_post_id > last_post_id:
            print(f"🔔 Обнаружен новый пост: ID = {latest_post_id}")
            if post_exists(latest_post_id):
                comment = get_random_comment()
                if comment:
                    print(f"💬 Публикуем комментарий: {comment}")
                    post_comment(latest_post_id, comment)
                else:
                    print("⚠️ Комментарий не выбран.")
            else:
                print(f"⚠️ Пост {latest_post_id} не существует или недоступен.")
            save_last_post_id(latest_post_id)
        else:
            print("✅ Новых постов нет.")

        print(f"⏳ Ожидание {INTERVAL_SECONDS // 60} минут...")
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main_loop()
