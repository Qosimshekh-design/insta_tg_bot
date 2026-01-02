import asyncio
import os
import time

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config import BOT_TOKEN
from storage import load_data, save_data
from queue_worker import queue_worker
from instagram_manager import login_and_check
from video_unique_hard import uniquify_video_hard
from universal_watermark import add_text_watermark

# ================= INIT =================

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
os.makedirs("videos", exist_ok=True)

# ================= STATES =================

class AddAccountState(StatesGroup):
    waiting_credentials = State()

class PublishState(StatesGroup):
    video = State()
    caption = State()
    account = State()

# ================= START =================

@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer(
        "👋 Бот готов\n\n"
        "/add_account — добавить Instagram\n"
        "/publish — опубликовать видео"
    )

# ================= ADD ACCOUNT =================

@dp.message(Command("add_account"))
async def add_account(msg: types.Message, state: FSMContext):
    await msg.answer("Отправь логин и пароль:\n\nlogin password")
    await state.set_state(AddAccountState.waiting_credentials)

@dp.message(AddAccountState.waiting_credentials, F.text)
async def save_account(msg: types.Message, state: FSMContext):
    try:
        login, password = msg.text.strip().split(" ", 1)
    except ValueError:
        await msg.answer("❌ Формат неверный\nНужно: login password")
        return

    ok, result = login_and_check(login, password)
    await msg.answer(result)

    if ok:
        data = load_data()
        data["accounts"][login] = password
        save_data(data)

    await state.clear()

# ================= PUBLISH FLOW =================

@dp.message(Command("publish"))
async def publish(msg: types.Message, state: FSMContext):
    await msg.answer("🎬 Отправь видео")
    await state.set_state(PublishState.video)

@dp.message(PublishState.video, F.video)
async def get_video(msg: types.Message, state: FSMContext):
    file = await bot.get_file(msg.video.file_id)
    path = f"videos/{msg.video.file_id}.mp4"
    await bot.download(
    msg.video,
    destination=path
)

    await msg.answer("🔥 Уникализация + watermark...")
    #path = await asyncio.to_thread(uniquify_video_hard, path)
    path = await asyncio.to_thread(
        add_text_watermark,
        path,
        "@my_inst | t.me/mychannel"
    )

    await state.update_data(video=path)
    await msg.answer("✍️ Отправь описание")
    await state.set_state(PublishState.caption)

@dp.message(PublishState.caption, F.text)
async def get_caption(msg: types.Message, state: FSMContext):
    await state.update_data(caption=msg.text)

    data = load_data()
    if not data["accounts"]:
        await msg.answer("❌ Нет аккаунтов. Сначала /add_account")
        await state.clear()
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=acc)] for acc in data["accounts"]],
        resize_keyboard=True
    )

    await msg.answer("👤 Выбери аккаунт", reply_markup=kb)
    await state.set_state(PublishState.account)

@dp.message(PublishState.account, F.text)
async def finish_publish(msg: types.Message, state: FSMContext):
    data_state = await state.get_data()
    data = load_data()

    if msg.text not in data["accounts"]:
        await msg.answer("❌ Аккаунт не найден")
        return

    task = {
        "chat_id": msg.chat.id,
        "username": msg.text,
        "password": data["accounts"][msg.text],
        "video": data_state["video"],
        "caption": data_state["caption"],
        "publish_at": time.time()
    }

    data["queue"].append(task)
    save_data(data)

    await msg.answer("⏳ Видео добавлено в очередь")
    await state.clear()

# ================= MAIN =================

async def main():
    asyncio.create_task(queue_worker())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
