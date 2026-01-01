from instagrapi import Client
import os
import time
from config import IG_USERNAME, IG_PASSWORD, SESSION_FILE

ig = Client()

def login_instagram():
    if os.path.exists(SESSION_FILE):
        ig.load_settings(SESSION_FILE)
        ig.login(IG_USERNAME, IG_PASSWORD)
        print("✅ Instagram: сессия загружена")
    else:
        ig.login(IG_USERNAME, IG_PASSWORD)
        ig.dump_settings(SESSION_FILE)
        print("🆕 Instagram: первый вход, сессия сохранена")

    time.sleep(3)  # anti-ban задержка
    return ig
