import logging
import os
import json
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ========================
# НАСТРОЙКИ — заполни сам
# ========================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ВАШ_ТОКЕН_БОТА")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@ваш_канал")
READY_CHANNEL_ID = os.environ.get("READY_CHANNEL_ID", "@канал_руководителей")
# ========================

COUNTER_FILE = "counter.json"
START_NUMBER = 2233

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Шаги диалога
ПЛОЩАДКА, ИМЯ, СТЕЙДЖ, ГОРОД, ДАТА_РОЖДЕНИЯ, РУК, МЕДИА = range(7)

# Ники руководителей
РУКОВОДИТЕЛИ = ["@antrakt199404", "@EvgeniyGrecu", "@sonya_petrovaTL", "@Skorrrrik", "@Layt_qp", "@Tipple_1843", "@Simbaofficial01"]


def get_next_number() -> int:
    start = int(os.environ.get("START_COUNTER", "2233"))
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "r") as f:
            data = json.load(f)
            number = max(data.get("counter", start - 1), start - 1) + 1
    else:
        number = start

    with open(COUNTER_FILE, "w") as f:
        json.dump({"counter": number}, f)

    return number


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "👋 Привет! Давай оформим заказ.\n\n"
        "Шаг 1/7 — Напиши *площадку* на английском языке:\n"
        "(например: Mamba, TopFace, TikTok)",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return ПЛОЩАДКА


async def get_площадка(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["площадка"] = update.message.text.strip()
    await update.message.reply_text("Шаг 2/7 — Введи *имя девочки*:", parse_mode="Markdown")
    return ИМЯ


async def get_имя(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["имя"] = update.message.text.strip()
    await update.message.reply_text("Шаг 3/7 — Укажи *стейдж агента*:", parse_mode="Markdown")
    return СТЕЙДЖ


async def get_стейдж(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["стейдж"] = update.message.text.strip()
    await update.message.reply_text("Шаг 4/7 — Напиши *город*:", parse_mode="Markdown")
    return ГОРОД


async def get_город(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["город"] = update.message.text.strip()
    await update.message.reply_text(
        "Шаг 5/7 — Укажи *дату рождения* (например: 15.03.1995):",
        parse_mode="Markdown"
    )
    return ДАТА_РОЖДЕНИЯ


async def get_дата(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["дата"] = update.message.text.strip()
    keyboard = [РУКОВОДИТЕЛИ[i:i+2] for i in range(0, len(РУКОВОДИТЕЛИ), 2)]
    await update.message.reply_text(
        "Шаг 6/7 — Выбери *ник руководителя*:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return РУК


async def get_рук(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    рук = update.message.text.strip()
    if рук not in РУКОВОДИТЕЛИ:
        keyboard = [[ник] for ник in РУКОВОДИТЕЛИ]
        await update.message.reply_text(
            "⚠️ Пожалуйста, выбери ник из списка:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return РУК

    context.user_data["рук"] = рук
    await update.message.reply_text(
        "Шаг 7/7 — Прикрепи *фото* или отправь *ссылку*:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return МЕДИА


async def get_медиа(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    d = context.user_data

    # Получаем следующий номер заказа
    номер = get_next_number()

    строка = (
        f"{d['площадка']} {номер} // {d['имя']} // {d['стейдж']} // "
        f"{d['город']} // {d['дата']} // {d['рук']}"
    )

    try:
        if update.message.photo:
            photo_id = update.message.photo[-1].file_id
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo_id,
                caption=строка
            )
        elif update.message.text:
            ссылка = update.message.text.strip()
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"{строка}\n🔗 {ссылка}"
            )
        else:
            await update.message.reply_text(
                "⚠️ Пожалуйста, отправь фото или ссылку текстом."
            )
            return МЕДИА

        await update.message.reply_text(
            f"✅ Заказ №{номер} успешно отправлен!\n\nЧтобы оформить новый — напиши /start"
        )
    except Exception as e:
        logging.error(f"Ошибка отправки в канал: {e}")
        await update.message.reply_text("❌ Ошибка при отправке в канал. Проверь настройки бота.")

    return ConversationHandler.END


async def handle_channel_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.channel_post
    if not message or not message.reply_to_message:
        return

    text = message.text.strip() if message.text else ""
    text_lower = text.lower()

    original = message.reply_to_message.text or message.reply_to_message.caption
    if not original:
        return

    строка_заказа = original.split("\n")[0].strip()

    try:
        if text_lower == "готово":
            await context.bot.send_message(
                chat_id=READY_CHANNEL_ID,
                text=f"✅ Готово: {строка_заказа}"
            )
        elif text_lower.startswith("не выполнено"):
            причина = text[len("не выполнено"):].strip()
            if not причина:
                причина = "причина не указана"
            await context.bot.send_message(
                chat_id=READY_CHANNEL_ID,
                text=f"❌ Не выполнено: {строка_заказа} | Причина: {причина}"
            )
    except Exception as e:
        logging.error(f"Ошибка отправки в канал руководителей: {e}")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "❌ Оформление отменено. Напиши /start чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ПЛОЩАДКА:      [MessageHandler(filters.TEXT & ~filters.COMMAND, get_площадка)],
            ИМЯ:           [MessageHandler(filters.TEXT & ~filters.COMMAND, get_имя)],
            СТЕЙДЖ:        [MessageHandler(filters.TEXT & ~filters.COMMAND, get_стейдж)],
            ГОРОД:         [MessageHandler(filters.TEXT & ~filters.COMMAND, get_город)],
            ДАТА_РОЖДЕНИЯ: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_дата)],
            РУК:           [MessageHandler(filters.TEXT & ~filters.COMMAND, get_рук)],
            МЕДИА:         [MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, get_медиа)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL & filters.TEXT, handle_channel_reply))

    print("🤖 Бот запущен. Нажми Ctrl+C для остановки.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
