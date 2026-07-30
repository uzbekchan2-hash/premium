import os
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from pyrogram import Client, filters

# Logging
logging.basicConfig(level=logging.INFO)

# --- ENVIRONMENT VARIABLES (Render'dan olinadi) ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
API_ID = int(os.getenv("API_ID", 0)) if os.getenv("API_ID") else None
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}" if RENDER_EXTERNAL_URL else None

# Aiogram Bot
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Pyrogram Userbot (Shaxsiy akkaunt)
userbot = None
if API_ID and API_HASH and SESSION_STRING:
    userbot = Client(
        "userbot_session",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING
    )

# ----------------- USERBOT (SHAXSIY AKKAUNT) ----------------- #

autojavob_active = False

if userbot:
    @userbot.on_message(filters.private & ~filters.me)
    async def auto_reply(client, message):
        global autojavob_active
        if autojavob_active:
            await message.reply("Assalomu alaykum! Hozir bandman, tez orada javob beraman.")

# ----------------- BOT KLAVIATURALARI ----------------- #

def main_menu():
    kb = [
        [InlineKeyboardButton(text="🤖 AI Yordamchi", callback_data="ai_yordamchi")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def ai_menu():
    status = "🟢 Yoqilgan" if autojavob_active else "🔴 O'chirilgan"
    kb = [
        [InlineKeyboardButton(text=f"1️⃣ Autojavob ({status})", callback_data="toggle_autojavob")],
        [InlineKeyboardButton(text="2️⃣ Autoxabar (Yuborish)", callback_data="send_autoxabar")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def back_to_ai_menu():
    kb = [
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="ai_yordamchi")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ----------------- HANDLERLAR ----------------- #

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Xush kelibsiz! Kerakli bo'limni tanlang:", reply_markup=main_menu())

@dp.callback_query(F.data == "main_menu")
async def back_to_main(call: CallbackQuery):
    await call.message.edit_text("Bosh menyu:", reply_markup=main_menu())

@dp.callback_query(F.data == "ai_yordamchi")
async def ai_yordamchi_handler(call: CallbackQuery):
    await call.message.edit_text(
        "🤖 **AI Yordamchi / Akkaunt Boshqaruvi**\n\nKerakli funksiyani tanlang:",
        reply_markup=ai_menu(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "toggle_autojavob")
async def toggle_autojavob_handler(call: CallbackQuery):
    global autojavob_active
    autojavob_active = not autojavob_active
    st = "yoqildi 🟢" if autojavob_active else "o'chirildi 🔴"
    await call.answer(f"Autojavob {st}", show_alert=True)
    await call.message.edit_reply_markup(reply_markup=ai_menu())

@dp.callback_query(F.data == "send_autoxabar")
async def send_autoxabar_handler(call: CallbackQuery):
    if not userbot:
        await call.message.edit_text(
            "❌ Userbot sozlanmagan! API_ID, API_HASH va SESSION_STRING kiritilganini tekshiring.",
            reply_markup=back_to_ai_menu()
        )
        return

    try:
        await userbot.send_message("me", "📢 **Autoxabar:** AI Yordamchi sinov xabari!")
        await call.message.edit_text(
            "✅ Akkauntingiz (Saved Messages)ga autoxabar yuborildi!",
            reply_markup=back_to_ai_menu()
        )
    except Exception as e:
        await call.message.edit_text(
            f"❌ Xatolik yuz berdi: {e}",
            reply_markup=back_to_ai_menu()
        )

# ----------------- SERVER VA WEBHOOK ----------------- #

async def on_startup(app):
    if WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL)
    if userbot:
        await userbot.start()
        logging.info("Userbot ishga tushdi!")

async def on_shutdown(app):
    await bot.delete_webhook()
    if userbot:
        await userbot.stop()

app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
webhook_requests_handler.register(app, path=WEBHOOK_PATH)
setup_application(app, dp, bot=bot)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
