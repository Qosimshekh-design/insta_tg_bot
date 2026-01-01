from instagrapi import Client
import os

clients = {}
SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

def login_and_check(username: str, password: str):
    ig = Client()
    session_path = f"{SESSIONS_DIR}/{username}.json"

    try:
        ig.login(username, password)
        if not ig.user_id:
            raise Exception("Login failed")

        ig.dump_settings(session_path)
        clients[username] = ig
        return True, "✅ Вход в Instagram успешный"

    except Exception as e:
        if os.path.exists(session_path):
            os.remove(session_path)
        return False, f"❌ Вход неуспешный: {e}"

def get_client(username: str, password: str):
    if username in clients:
        return clients[username]

    session_path = f"{SESSIONS_DIR}/{username}.json"
    if not os.path.exists(session_path):
        raise Exception("❌ Сессия не найдена")

    ig = Client()
    ig.load_settings(session_path)
    ig.login(username, password)

    if not ig.user_id:
        raise Exception("❌ Сессия недействительна")

    clients[username] = ig
    return ig
