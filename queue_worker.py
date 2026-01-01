import asyncio, time, os
from aiogram import Bot
from config import BOT_TOKEN
from storage import load_data, save_data, log_publish
from instagram_manager import get_client

bot = Bot(BOT_TOKEN)

def safe_remove(path):
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except:
            pass

async def queue_worker():
    while True:
        data = load_data()
        now = time.time()

        for task in data["queue"][:]:
            if task["publish_at"] <= now:
                try:
                    ig = get_client(task["username"], task["password"])

                    ig.clip_upload(task["video"], caption=task["caption"])

                    await bot.send_message(
                        task["chat_id"],
                        "✅ Видео опубликовано в Instagram 🎉"
                    )

                    log_publish(f"{task['username']} | OK")

                except Exception as e:
                    await bot.send_message(
                        task["chat_id"],
                        f"❌ Ошибка публикации:\n{e}"
                    )
                    log_publish(f"{task['username']} | ERROR | {e}")

                finally:
                    safe_remove(task["video"])
                    data["queue"].remove(task)
                    save_data(data)

        await asyncio.sleep(5)
