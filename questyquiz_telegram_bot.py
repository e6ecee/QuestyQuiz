import json
import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os
import threading
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загрузка вопросов из JSON файла
def load_questions():
    with open("questions.json", 'r', encoding='utf-8') as file:
        return json.load(file)

questions = load_questions()

# Инициализация бота и приложения
API_TOKEN = "6847241186:AAHVKq9G3nDnWIyjg9uMiZPEU4WMnZMXhFA"
bot = Bot(token=API_TOKEN)
app = Application.builder().token(API_TOKEN).build()

# Синхронизация доступа к файлу результатов
results_lock = threading.Lock()

# Глобальный словарь для хранения состояний
user_states = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = {"current_question": 0, "score": 0}
    await ask_question(update, context)

# Задание вопроса
async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = user_states[user_id]
    current_question_index = user_data['current_question']
    question_data = questions[current_question_index]
    question_text = question_data['question']
    options = question_data['options']

    keyboard = [[InlineKeyboardButton(text=option, callback_data=option)] for option in options]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.message.edit_text(question_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(question_text, reply_markup=reply_markup)

# Обработка нажатия на кнопку
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_option = query.data
    user_id = update.effective_user.id
    user_data = user_states[user_id]
    current_question_index = user_data['current_question']
    correct_answer = questions[current_question_index]['answer']

    if selected_option == correct_answer:
        response_text = f"Правильно! Ответ: {correct_answer}"
        user_data['score'] += 1
    else:
        response_text = f"Неправильно. Правильный ответ: {correct_answer}"

    await query.edit_message_text(response_text)

    if current_question_index + 1 < len(questions):
        user_states[user_id]['current_question'] += 1
        await ask_question(update, context)
    else:
        user_score = user_data['score']
        results[str(user_id)] = user_score
        save_results(results)
        await query.message.reply_text(f"Квиз завершен! Ваш результат: {user_score}/{len(questions)}")
        del user_states[user_id]

# Загрузка результатов из JSON файла
def load_results():
    if os.path.exists("results.json"):
        with open("results.json", 'r', encoding='utf-8') as file:
            try:
                return json.load(file)
            except json.decoder.JSONDecodeError:
                return {}
    else:
        with open("results.json", 'w', encoding='utf-8') as file:
            json.dump({}, file, ensure_ascii=False, indent=4)
        return {}

# Сохранение результатов в JSON файл с синхронизацией
def save_results(results):
    with results_lock:
        with open("results.json", 'w', encoding='utf-8') as file:
            json.dump(results, file, ensure_ascii=False, indent=4)

results = load_results()

# Команда /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in results:
        await update.message.reply_text(f"Ваш последний результат: {results[user_id]}/{len(questions)}")
    else:
        await update.message.reply_text("Вы еще не проходили квиз.")

# Запуск бота
def main():
    # Регистрация обработчиков команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button))

    # Запуск бота
    app.run_polling()

if __name__ == '__main__':
    main()
