import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from instagrapi import Client
from config import BOT_TOKEN

# ================== INIT ==================

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

VIDEO_DIR = "videos"
ACCOUNTS_FILE = "accounts.json"

os.makedirs(VIDEO_DIR, exist_ok=True)

# ================== HELPERS ==================

def load_accounts():
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_accounts(data):
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Опубликовать Reel")],
            [KeyboardButton(text="➕ Добавить аккаунт"), KeyboardButton(text="📂 Мои аккаунты")],
            [KeyboardButton(text="🗑 Удалить аккаунт")]
        ],
        resize_keyboard=True
    )

# ================== STATES ==================

class PublishState(StatesGroup):
    video = State()
    caption = State()
    account = State()

class AddAccountState(StatesGroup):
    credentials = State()

class DeleteAccountState(StatesGroup):
    choose = State()

# ================== START ==================

@dp.message(Command("start"))
async def start(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "👋 Привет!\n\n"
        "Я бот для публикации Reels в Instagram.\n"
        "Работаю только для тебя 🔐",
        reply_markup=get_keyboard()
    )

# ================== ADD ACCOUNT ==================

@dp.message(F.text == "➕ Добавить аккаунт")
async def add_account(msg: types.Message, state: FSMContext):
    data = load_accounts()
    if len(data["accounts"]) >= 5:
        await msg.answer("❌ Максимум 5 аккаунтов")
        return

    await msg.answer("🔐 Отправь логин и пароль:\n\nlogin password")
    await state.set_state(AddAccountState.credentials)

@dp.message(AddAccountState.credentials, F.text)
async def save_account(msg: types.Message, state: FSMContext):
    try:
        username, password = msg.text.strip().split(" ", 1)
    except ValueError:
        await msg.answer("❌ Формат неверный")
        return

    ig = Client()
    try:
        ig.login(username, password)
    except Exception as e:
        await msg.answer(f"❌ Вход не удался:\n{e}")
        return

    ig.dump_settings(f"sessions/{username}.json")

    data = load_accounts()
    data["accounts"][username] = {
        "password": password,
        "session": f"sessions/{username}.json"
    }
    save_accounts(data)

    await msg.answer(f"✅ Аккаунт @{username} добавлен")
    await state.clear()

# ================== LIST ACCOUNTS ==================

@dp.message(F.text == "📂 Мои аккаунты")
async def list_accounts(msg: types.Message):
    data = load_accounts()
    if not data["accounts"]:
        await msg.answer("❌ Аккаунтов нет")
        return

    text = "📂 Аккаунты:\n\n"
    for acc in data["accounts"]:
        text += f"• @{acc}\n"

    await msg.answer(text)

# ================== DELETE ACCOUNT ==================

@dp.message(F.text == "🗑 Удалить аккаунт")
async def delete_account(msg: types.Message, state: FSMContext):
    data = load_accounts()
    if not data["accounts"]:
        await msg.answer("❌ Аккаунтов нет")
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=acc)] for acc in data["accounts"]],
        resize_keyboard=True
    )
    await msg.answer("Выбери аккаунт для удаления", reply_markup=kb)
    await state.set_state(DeleteAccountState.choose)

@dp.message(DeleteAccountState.choose, F.text)
async def confirm_delete(msg: types.Message, state: FSMContext):
    data = load_accounts()
    username = msg.text

    if username not in data["accounts"]:
        await msg.answer("❌ Аккаунт не найден")
        return

    session_file = data["accounts"][username]["session"]
    if os.path.exists(session_file):
        os.remove(session_file)

    del data["accounts"][username]
    save_accounts(data)

    await msg.answer(f"🗑 Аккаунт @{username} удалён", reply_markup=get_keyboard())
    await state.clear()

# ================== PUBLISH FLOW ==================

@dp.message(F.text == "🚀 Опубликовать Reel")
async def start_publish(msg: types.Message, state: FSMContext):
    await msg.answer("🎬 Отправь видео")
    await state.set_state(PublishState.video)

@dp.message(PublishState.video, F.video)
async def get_video(msg: types.Message, state: FSMContext):
    file = await bot.get_file(msg.video.file_id)
    path = f"{VIDEO_DIR}/{msg.video.file_id}.mp4"
    await bot.download_file(file.file_path, path)

    await state.update_data(video=path)
    await msg.answer("✍️ Отправь описание")
    await state.set_state(PublishState.caption)

@dp.message(PublishState.caption, F.text)
async def get_caption(msg: types.Message, state: FSMContext):
    await state.update_data(caption=msg.text)

    data = load_accounts()
    if not data["accounts"]:
        await msg.answer("❌ Нет аккаунтов")
        await state.clear()
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=acc)] for acc in data["accounts"]],
        resize_keyboard=True
    )
    await msg.answer("👤 Выбери аккаунт", reply_markup=kb)
    await state.set_state(PublishState.account)

@dp.message(PublishState.account, F.text)
async def publish(msg: types.Message, state: FSMContext):
    data = load_accounts()
    username = msg.text

    if username not in data["accounts"]:
        await msg.answer("❌ Аккаунт не найден")
        return

    info = await state.get_data()
    video_path = info["video"]
    caption = info["caption"]

    await msg.answer("⏳ Публикую в Instagram...")

    ig = Client()
    ig.load_settings(data["accounts"][username]["session"])

    try:
        ig.clip_upload(video_path, caption=caption)
        await msg.answer(f"✅ Опубликовано в @{username}")
    except Exception as e:
        await msg.answer(f"❌ Ошибка публикации:\n{e}")
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
        await state.clear()

# ================== MAIN ==================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
