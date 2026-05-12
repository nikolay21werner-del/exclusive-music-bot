"""
EXCLUSIVE MUSIC BOT — Telegram-бот с интерактивным музыкальным WebApp-плеером.
Подключён к каналу @exclusive_music_remix.

Требования:
  pip install python-telegram-bot>=20.0

Запуск:
  BOT_TOKEN=your_token python bot.py
"""

import os
import json
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
    MenuButtonWebApp,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ===== НАСТРОЙКИ =====
BOT_TOKEN  = os.environ.get("BOT_TOKEN", "7611594840:AAEAh5xvmWnMIpybzkIHPNPKKvWlEbozJ_E")
CHANNEL_ID = "@exclusive_music_remix"
WEBAPP_URL = "https://nikolay21werner-del.github.io/exclusive-music-bot/?v=13"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    name = user.first_name or "друг"

    inline_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🎵 Открыть плеер", web_app=WebAppInfo(url=WEBAPP_URL))
    ]])
    reply_kb = ReplyKeyboardMarkup(
        [[KeyboardButton("🎧 EXCLUSIVE MUSIC BOT", web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True,
    )

    text = (
        f"Привет, {name}! 🔥\n\n"
        "Я — <b>EXCLUSIVE MUSIC BOT</b>.\n"
        "Здесь собраны все эксклюзивные ремиксы с канала "
        f"<a href='https://t.me/exclusive_music_remix'>@exclusive_music_remix</a>.\n\n"
        "🎵 Все треки прямо в плеере — поиск, лайки, очередь, перемешивание.\n\n"
        "Жми кнопку и слушай! 👇"
    )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=inline_kb)
    await update.message.reply_text(
        "Или кнопка внизу 👇", reply_markup=reply_kb
    )


# ===== /music =====
async def music(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🎵 Открыть плеер", web_app=WebAppInfo(url=WEBAPP_URL))
    ]])
    await update.message.reply_text("🎶 Открой плеер:", reply_markup=kb)


# ===== /help =====
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "<b>EXCLUSIVE MUSIC BOT — команды:</b>\n\n"
        "/start — Запуск + кнопки плеера\n"
        "/music — Открыть плеер\n"
        "/tracks — Список всех треков\n"
        "/help — Справка\n\n"
        f"Канал: <a href='https://t.me/exclusive_music_remix'>@exclusive_music_remix</a>\n"
        "Все новые треки автоматически появляются в плеере."
    )
    await update.message.reply_text(text, parse_mode="HTML")


# ===== /tracks — список треков =====
async def tracks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать список треков из channel_tracks.json"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_dir, "channel_tracks.json")
        with open(path, encoding="utf-8") as f:
            tracks = json.load(f)

        lines = [f"<b>🎵 Треки EXCLUSIVE MUSIC REMIX ({len(tracks)} шт.):</b>\n"]
        for i, t in enumerate(tracks, 1):
            dur = t.get("duration", 0)
            m, s = divmod(dur, 60)
            lines.append(f"{i}. {t['title']} — {t['artist']} ({m}:{s:02d})")
            if i % 30 == 0:
                await update.message.reply_text("\n".join(lines), parse_mode="HTML")
                lines = []

        if lines:
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("🎵 Слушать в плеере", web_app=WebAppInfo(url=WEBAPP_URL))
            ]])
            await update.message.reply_text(
                "\n".join(lines), parse_mode="HTML", reply_markup=kb
            )
    except FileNotFoundError:
        await update.message.reply_text("⚠️ Список треков не найден. Запусти sync_channel.py")


# ===== Новый пост в канале → уведомление =====
async def channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Когда в канале появляется новый аудиотрек — бот это замечает."""
    cp = update.channel_post
    if not cp or cp.chat.username != "exclusive_music_remix":
        return

    audio = cp.audio
    if not audio:
        return

    title  = audio.title or "Новый трек"
    artist = audio.performer or "Unknown"
    file_id = audio.file_id
    dur = audio.duration or 0
    m, s = divmod(dur, 60)

    logger.info("Новый трек в канале: %s — %s (file_id: %s)", title, artist, file_id[:30])

    # Можно здесь рассылать уведомления подписчикам бота
    # или сохранять в JSON для обновления плеера


# ===== WebApp data =====
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        action = data.get("action", "")

        if action == "track_selected":
            title   = data.get("title", "?")
            artist  = data.get("artist", "?")
            file_id = data.get("file_id", "")

            if file_id:
                # Отправляем аудиофайл прямо в чат — Telegram воспроизведёт его
                try:
                    await update.message.reply_audio(
                        audio=file_id,
                        title=title,
                        performer=artist,
                        caption=f"🎵 <b>{title}</b> — {artist}\n\n🔥 EXCLUSIVE MUSIC BOT",
                        parse_mode="HTML",
                    )
                except Exception as audio_err:
                    logger.error("Ошибка отправки аудио: %s", audio_err)
                    await update.message.reply_text(
                        f"🎵 Сейчас играет:\n<b>{title}</b>\n{artist}",
                        parse_mode="HTML",
                    )
            else:
                await update.message.reply_text(
                    f"🎵 Сейчас играет:\n<b>{title}</b>\n{artist}",
                    parse_mode="HTML",
                )
        elif action == "liked":
            title = data.get("title", "?")
            await update.message.reply_text(
                f"❤️ Добавлено в любимые: <b>{title}</b>", parse_mode="HTML"
            )
        elif action == "share":
            title  = data.get("title", "")
            artist = data.get("artist", "")
            await update.message.reply_text(
                f"📤 Поделиться:\n🎵 <b>{title}</b> — {artist}\n\n"
                f"Слушай в EXCLUSIVE MUSIC BOT!",
                parse_mode="HTML",
            )
    except Exception as e:
        logger.error("WebApp data error: %s", e)


# ===== Menu button =====
async def post_init(application: Application) -> None:
    try:
        await application.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="🎵 EXCLUSIVE",
                web_app=WebAppInfo(url=WEBAPP_URL),
            )
        )
        logger.info("Menu button установлена: 🎵 EXCLUSIVE MUSIC BOT")
    except Exception as e:
        logger.warning("Не удалось установить menu button: %s", e)


# ===== MAIN =====
def main() -> None:
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("music",  music))
    app.add_handler(CommandHandler("help",   help_cmd))
    app.add_handler(CommandHandler("tracks", tracks_cmd))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL & filters.AUDIO, channel_post_handler))

    print("🎵 EXCLUSIVE MUSIC BOT запущен! Нажмите Ctrl+C для остановки.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
