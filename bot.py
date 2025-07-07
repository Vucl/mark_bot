import time
import requests
import random
import os

ACCESS_TOKEN = 'vk1.a.JeLPRJys1LhsI8v42TVYXz-TGsgjWOPPwMmw-YlVCUSF80_i4IL-E5CGUw8ThWeTLWD1XzZE4mMcoxhCiZTWlNEC4_o4SAwm7xMW2_nyyL-DROYOQeAuL4cQ2cSLE-xJ_rqtRmqphLO9iSRPLHHKqsd-hGsJoPmG1e9eZJ3QDxbetvpUR_c1eupB8SoYPkozG5SDQ04hkkkmtaq-PfTAbw'
OWNER_ID = -231062776  # группа
API_VERSION = '5.131'
INTERVAL_SECONDS = 3 * 3600 + 26 * 60  # 3 часа 26 минут

def load_last_post_id():
    if os.path.exists("last_post.txt"):
        with open("last_post.txt", "r") as f:
            return int(f.read())
    return 0

def save_last_post_id(post_id):
    with open("last_post.txt", "w") as f:
        f.write(str(post_id))

def get_latest_post_id():
    response = requests.get("https://api.vk.com/method/wall.get", params={
        "owner_id": OWNER_ID,
        "count": 1,
        "access_token": ACCESS_TOKEN,
        "v": API_VERSION
    })
    data = response.json()
    try:
        return data['response']['items'][0]['id']
    except:
        print("Ошибка при получении поста:", data)
        return None

def get_random_comment():
    with open("comments.txt", "r", encoding="utf-8") as f:
        return random.choice([line.strip() for line in f if line.strip()])

def post_comment(post_id, message):
    response = requests.get("https://api.vk.com/method/wall.createComment", params={
        "owner_id": OWNER_ID,
        "post_id": post_id,
        "message": message,
        "access_token": ACCESS_TOKEN,
        "v": API_VERSION
    })
    print("Комментарий отправлен:", response.json())

def main_loop():
    while True:
        print("Проверка новых постов...")
        last_post_id = load_last_post_id()
        latest_post_id = get_latest_post_id()

        if latest_post_id and latest_post_id > last_post_id:
            comment = get_random_comment()
            print(f"Новый пост {latest_post_id} → Комментируем: {comment}")
            post_comment(latest_post_id, comment)
            save_last_post_id(latest_post_id)
        else:
            print("Новых постов нет.")

        print(f"Ожидание {INTERVAL_SECONDS} секунд...")
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main_loop()
