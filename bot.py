import asyncio
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import BOT_TOKEN
from instagram import login_instagram

# ================== INIT ==================

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
ig = login_instagram()

os.makedirs("videos", exist_ok=True)

# ================== STATES ==================

class PublishState(StatesGroup):
    waiting_video = State()
    waiting_caption = State()

# ================== START ==================

@dp.message(Command("start"))
async def start(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "👋 Привет!\n\n"
        "📤 Отправь ВИДЕО\n"
        "✍️ Потом отправь ОПИСАНИЕ\n\n"
        "Я опубликую Reel в Instagram 🚀"
    )
    await state.set_state(PublishState.waiting_video)

# ================== GET VIDEO ==================

@dp.message(PublishState.waiting_video, F.video)
async def get_video(msg: types.Message, state: FSMContext):
    await msg.answer("⏳ Загружаю видео...")

    file = await bot.get_file(msg.video.file_id)
    video_path = f"videos/{msg.video.file_id}.mp4"

    # 🔹 СТАБИЛЬНЫЙ СПОСОБ (aiogram-way)
    await bot.download_file(file.file_path, video_path)

    await state.update_data(video_path=video_path)
    await msg.answer("✍️ Теперь отправь ОПИСАНИЕ")
    await state.set_state(PublishState.waiting_caption)

# ================== GET CAPTION & PUBLISH ==================

@dp.message(PublishState.waiting_caption, F.text)
async def get_caption(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    video_path = data.get("video_path")
    caption = msg.text

    if not video_path or not os.path.exists(video_path):
        await msg.answer("❌ Видео не найдено, попробуй снова")
        await state.clear()
        return

    await msg.answer("⏳ Публикую в Instagram...")

    try:
        ig.clip_upload(video_path, caption=caption)
        await msg.answer("✅ Видео опубликовано 🎉")

    except Exception as e:
        await msg.answer(f"❌ Ошибка публикации:\n{e}")

    finally:
        try:
            os.remove(video_path)
        except Exception:
            pass

        await state.clear()

# ================== MAIN ==================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
