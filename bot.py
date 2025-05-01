import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, MessageHandler, filters, ConversationHandler
from openai import OpenAI
import docx
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import logging
import json
import re

# Настройка API и токенов
TELEGRAM_BOT_TOKEN = "7860525094:AAGG6PHD1q728Fl5UIAybWFILWQgfvjDP8M"
DEEPSEEK_API_KEY = "sk-2fcca2e6cf50493ba7d67eb50e73516f"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Команда /start
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [["/order", "/subscribe"], ["/help", "/cancel"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👾 Добро пожаловать в *NinjaEssayAI*! 🥷\n\n"
        "⚡ Мы поможем вам создать идеальную работу за считанные минуты! ⚡\n\n"
        "🖋 Используйте меню ниже, чтобы выбрать действие:",
        reply_markup=reply_markup
    )

# Команда /help
async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "🆘 *Помощь* 🆘\n\n"
        "Вот список доступных команд:\n"
        "- 📋 /order - Оформить заказ\n"
        "- 💳 /subscribe - Подписка на премиум-функции\n"
        "- ❌ /cancel - Отменить текущий процесс\n"
        "- ℹ️ /help - Показать это сообщение помощи"
    )

# Состояния разговора
WORK_TYPE, SCIENCE_NAME, PAGE_NUMBER, WORK_THEME, PREFERENCES, PAYMENT = range(6)

# Начало заказа
async def order(update: Update, context: CallbackContext) -> int:
    keyboard = [
        ["📝 Эссе", "📜 Доклад"],
        ["📖 Реферат", "💼 Проект"],
        ["📚 Курсовая работа"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("🥷 *Выберите тип работы:* 🥷", reply_markup=reply_markup)
    return WORK_TYPE

# Обработчики этапов заказа
async def work_type_handler(update: Update, context: CallbackContext) -> int:
    context.user_data["work_type"] = update.message.text
    await update.message.reply_text("Пожалуйста, заполните анкету:\n1. Название дисциплины (например, Математика):")
    return SCIENCE_NAME

async def science_name_handler(update: Update, context: CallbackContext) -> int:
    context.user_data["science_name"] = update.message.text
    await update.message.reply_text("Введите количество страниц:")
    return PAGE_NUMBER

async def page_number_handler(update: Update, context: CallbackContext) -> int:
    try:
        context.user_data["page_number"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число:")
        return PAGE_NUMBER
    await update.message.reply_text("Введите тему работы:")
    return WORK_THEME

async def work_theme_handler(update: Update, context: CallbackContext) -> int:
    context.user_data["work_theme"] = update.message.text
    await update.message.reply_text("Введите ваши предпочтения:")
    return PREFERENCES

async def preferences_handler(update: Update, context: CallbackContext) -> int:
    context.user_data["preferences"] = update.message.text
    work_type = context.user_data["work_type"]
    price = 300 if work_type in ["📝 Эссе", "📜 Доклад"] else 400 if work_type in ["📖 Реферат", "💼 Проект"] else 500
    await update.message.reply_text(
        f"🎯 *Ваш заказ:* 🎯\n"
        f"📌 Тип работы: {work_type}\n"
        f"📌 Дисциплина: {context.user_data['science_name']}\n"
        f"📌 Тема: {context.user_data['work_theme']}\n"
        f"📌 Количество страниц: {context.user_data['page_number']}\n"
        f"💰 *Стоимость:* {price} рублей\n\n"
        "✅ Для подтверждения оплаты введите /pay или нажмите /cancel для отмены."
    )
    return PAYMENT

async def payment_invalid(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Пожалуйста, введите /pay для подтверждения оплаты или /cancel для отмены.")
    return PAYMENT

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Заказ отменен.")
    return ConversationHandler.END

# Обработка оплаты и генерация документа
async def pay(update: Update, context: CallbackContext) -> int:
    logging.info("Начало выполнения заказа после оплаты.")
    await update.message.reply_text("Оплата успешно проведена! Начинаем выполнение вашего заказа.")

    # Генерация плана
    logging.info("Генерация плана работы.")
    plan_array = await generate_plan(context)
    context.user_data["plan_array"] = plan_array
    logging.info(f"План работы сгенерирован: {plan_array}")

    # Генерация текста и создание документа
    logging.info("Генерация текста по плану и создание документа.")
    file_path = await generate_text(plan_array, context)
    logging.info(f"Документ создан: {file_path}")

    # Отправка документа пользователю
    with open(file_path, "rb") as file:
        await update.message.reply_document(file, filename=file_path)

    await update.message.reply_text("Ваш заказ выполнен. Спасибо за использование нашего сервиса!")
    logging.info("Заказ успешно выполнен и отправлен пользователю.")
    return ConversationHandler.END

# Генерация плана
async def generate_plan(context: CallbackContext) -> list:
    logging.info("Запрос на генерацию плана отправлен в DeepSeek API.")
    
    science_name = context.user_data["science_name"]
    work_type = context.user_data["work_type"]
    work_theme = context.user_data["work_theme"]
    preferences = context.user_data["preferences"]
    page_number = context.user_data["page_number"]
    calls_number = max(1, page_number // 2)  # Минимум 1 пункт

    prompt = (
        f"Действуй как специалист в области {science_name}. "
        f"Составь план из {calls_number} пунктов для {work_type} по теме: {work_theme}. "
        f"Учти предпочтения: {preferences}. "
        "Верни план в виде JSON-массива строк или в виде нумерованного списка."
    )

    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[
            {"role": "system", "content": "mode: plan_generation"},
            {"role": "user", "content": prompt}
        ],
        stream=False
    )
    logging.info("Ответ от DeepSeek API получен.")

    response_content = response.choices[0].message.content

    try:
        # Пытаемся распарсить как JSON
        plan_array = json.loads(response_content)
        if not isinstance(plan_array, list):
            raise ValueError("Ответ не является массивом.")
    except (json.JSONDecodeError, ValueError):
        # Если не JSON, обрабатываем как текст
        logging.info("Ответ не в формате JSON, обрабатываем как текст.")
        # Извлекаем пункты, предполагая, что они разделены по строкам
        lines = response_content.splitlines()
        plan_array = [line.strip() for line in lines if line.strip()]
        # Убираем возможные нумерации (например, "1. Введение" -> "Введение")
        plan_array = [re.sub(r'^\d+\.\s*', '', item) for item in plan_array]

    # Корректируем количество пунктов
    if len(plan_array) > calls_number:
        plan_array = plan_array[:calls_number]
    elif len(plan_array) < calls_number:
        plan_array.extend([f"Раздел {i+1}" for i in range(len(plan_array), calls_number)])

    logging.info(f"Итоговый план: {plan_array}")
    return plan_array

# Генерация текста и создание документа
async def generate_text(plan_array, context: CallbackContext) -> str:
    logging.info("Начало генерации текста по главам плана.")
    science_name = context.user_data["science_name"]
    work_type = context.user_data["work_type"]
    work_theme = context.user_data["work_theme"]
    preferences = context.user_data["preferences"]

    if not plan_array:
        logging.error("План пуст. Невозможно сгенерировать текст.")
        await context.bot.send_message(
            chat_id=context._chat_id,
            text="Ошибка: План пуст. Убедитесь, что DeepSeek вернул корректный массив."
        )
        return ""

    # Создание документа
    doc = docx.Document()
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

    heading = doc.add_heading(f"{work_type} по теме: {work_theme}", level=1)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Генерация текста для каждого пункта плана
    for chapter in plan_array:
        logging.info(f"Генерация текста для главы: {chapter}")
        prompt = (
            f"Действуй как специалист в области {science_name}, напиши, строго с опорой на авторитетные источники, "
            f"главу: {chapter} в контексте написания {work_type} по теме: {work_theme} (напиши не менее 600 слов) "
            f"(Напиши текст, в котором предложения будут иметь разную длину, а также будет избегаться нахождение однокоренных слов в соседних предложениях) "
            f"{preferences}"
        )
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        chapter_text = response.choices[0].message.content
        logging.info(f"Сгенерированный текст для главы: {chapter_text[:100]}...")

        # Добавление текста в документ
        doc.add_heading(chapter, level=2)
        doc.add_paragraph(chapter_text)

    # Сохранение документа
    file_path = f"{work_type}_{work_theme}.docx"
    doc.save(file_path)
    logging.info(f"Документ сохранен: {file_path}")
    return file_path

# Основная функция
def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("order", order)],
        states={
            WORK_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, work_type_handler)],
            SCIENCE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, science_name_handler)],
            PAGE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, page_number_handler)],
            WORK_THEME: [MessageHandler(filters.TEXT & ~filters.COMMAND, work_theme_handler)],
            PREFERENCES: [MessageHandler(filters.TEXT & ~filters.COMMAND, preferences_handler)],
            PAYMENT: [
                CommandHandler("pay", pay),
                CommandHandler("cancel", cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, payment_invalid)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == "__main__":
    main()