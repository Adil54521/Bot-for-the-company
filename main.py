from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ConversationHandler, ContextTypes
)
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import os

# Загрузить переменные окружения из .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GSHEET_CREDENTIALS_FILE = os.getenv("GSHEET_CREDENTIALS_FILE")
GSHEET_URL = os.getenv("GSHEET_URL")

# Этапы состояния
ASK_NAME, ASK_PHONE = range(2)

# Подключение к Google Sheets
def get_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(GSHEET_CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(GSHEET_URL).sheet1
    return sheet

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Здравствуйте! Ваше имя?")
    return ASK_NAME

# Спрашивает имя
async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Пожалуйста, отправьте ваш номер телефона.")
    return ASK_PHONE

# Получает телефон и сохраняет в Google Таблицу
async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    name = context.user_data.get('name')

    sheet = get_sheet()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sheet.append_row([name, phone, now])

    await update.message.reply_text("Спасибо! Мы скоро с вами свяжемся.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Команда /cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Основной запуск
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
