"""
EXCLUSIVE MUSIC BOT — Telegram-бот с музыкальным WebApp-плеером.
Канал: @exclusive_music_remix
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
    InputFile,
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
WEBAPP_URL = "https://nikolay21werner-del.github.io/exclusive-music-bot/index.html?v=1778842309"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    name = user.first_name or "друг"

    reply_kb = ReplyKeyboardMarkup(
        [[KeyboardButton("🎧 Открыть плеер", web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True,
        is_persistent=True,
    )

    text = (
        f"👋 Привет, <b>{name}</b>!\n\n"
        "🎵 <b>EXCLUSIVE MUSIC BOT</b> — твой личный плеер эксклюзивных ремиксов.\n\n"
        "📀 <b>170+ треков</b> прямо в приложении:\n"
        "• Remix, Love, Hip-Hop, Electronic и другие жанры\n"
        "• Поиск по исполнителю и названию\n"
        "• Лайки, перемешивание, повтор\n"
        "• Красивый плеер в стиле спорткара\n\n"
        f"📢 Все новинки в канале: <a href='https://t.me/exclusive_music_remix'>@exclusive_music_remix</a>\n\n"
        "👇 Нажми кнопку и слушай!"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=reply_kb,
        disable_web_page_preview=True,
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
        "<b>🎵 EXCLUSIVE MUSIC BOT — справка</b>\n\n"
        "<b>Команды:</b>\n"
        "/start — Запуск и кнопка плеера\n"
        "/music — Открыть плеер\n"
        "/tracks — Список треков\n"
        "/channel — Ссылка на канал\n"
        "/help — Эта справка\n\n"
        "<b>В плеере:</b>\n"
        "🔀 — Перемешать треки\n"
        "🔁 — Повторять трек\n"
        "❤️ — Добавить в любимые\n"
        "🔍 — Поиск по 90M+ трекам\n\n"
        f"📢 Канал: <a href='https://t.me/exclusive_music_remix'>@exclusive_music_remix</a>"
    )
    await update.message.reply_text(
        text, parse_mode="HTML", disable_web_page_preview=True
    )


# ===== /channel =====
async def channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("📢 Перейти в канал", url="https://t.me/exclusive_music_remix"),
        InlineKeyboardButton("🎵 Открыть плеер", web_app=WebAppInfo(url=WEBAPP_URL)),
    ]])
    await update.message.reply_text(
        "📢 <b>Exclusive Music Remix</b>\n\n"
        "Все эксклюзивные ремиксы, новинки и горячие треки — в нашем канале.",
        parse_mode="HTML",
        reply_markup=kb,
    )


# ===== /tracks — список треков =====
async def tracks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🎵 Открыть плеер", web_app=WebAppInfo(url=WEBAPP_URL))
        ]])
        await update.message.reply_text(
            "🎵 <b>170+ треков</b> доступны прямо в плеере!",
            parse_mode="HTML",
            reply_markup=kb,
        )


# ===== Новый пост в канале =====
async def channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cp = update.channel_post
    if not cp or cp.chat.username != "exclusive_music_remix":
        return
    audio = cp.audio
    if not audio:
        return
    title  = audio.title or "Новый трек"
    artist = audio.performer or "Unknown"
    logger.info("Новый трек в канале: %s — %s", title, artist)


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
                        f"🎵 <b>{title}</b>\n{artist}", parse_mode="HTML"
                    )
            else:
                await update.message.reply_text(
                    f"🎵 Сейчас играет:\n<b>{title}</b>\n{artist}", parse_mode="HTML"
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
                f"Слушай в @exclusive_music_remix_bot!",
                parse_mode="HTML",
            )
    except Exception as e:
        logger.error("WebApp data error: %s", e)


# ===== Menu button & Bot description =====
async def post_init(application: Application) -> None:
    bot = application.bot
    # Set menu button
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="🎵 Плеер",
                web_app=WebAppInfo(url=WEBAPP_URL),
            )
        )
        logger.info("Menu button установлена")
    except Exception as e:
        logger.warning("Menu button error: %s", e)

    # Set bot description
    try:
        await bot.set_my_description(
            description=(
                "🎵 EXCLUSIVE MUSIC BOT\n\n"
                "170+ эксклюзивных ремиксов прямо в Telegram!\n\n"
                "• Красивый плеер в стиле спорткара\n"
                "• Жанры: Remix, Love, Hip-Hop, Electronic\n"
                "• Поиск, лайки, перемешивание\n\n"
                "Канал: @exclusive_music_remix"
            )
        )
        logger.info("Bot description set")
    except Exception as e:
        logger.warning("Description error: %s", e)

    # Set short description
    try:
        await bot.set_my_short_description(
            short_description="🎵 170+ эксклюзивных ремиксов в красивом плеере"
        )
        logger.info("Short description set")
    except Exception as e:
        logger.warning("Short description error: %s", e)

    # Set commands
    from telegram import BotCommand
    try:
        await bot.set_my_commands([
            BotCommand("start",   "🚀 Запуск и кнопка плеера"),
            BotCommand("music",   "🎵 Открыть плеер"),
            BotCommand("tracks",  "📋 Список всех треков"),
            BotCommand("channel", "📢 Ссылка на канал"),
            BotCommand("help",    "❓ Справка"),
        ])
        logger.info("Commands set")
    except Exception as e:
        logger.warning("Commands error: %s", e)

    # Set avatar from existing logo file
    try:
        with open('/home/user/workspace/track_cover_default.png', 'rb') as f:
            await bot.set_user_profile_photo(photo=f)
        logger.info("Avatar set!")
    except Exception as e:
        logger.warning("Avatar error: %s", e)


# ===== MAIN =====
def main() -> None:
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("music",   music))
    app.add_handler(CommandHandler("help",    help_cmd))
    app.add_handler(CommandHandler("tracks",  tracks_cmd))
    app.add_handler(CommandHandler("channel", channel_cmd))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL & filters.AUDIO, channel_post_handler))

    print("🎵 EXCLUSIVE MUSIC BOT запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
