import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher.filters import Command
import os

# Загрузка вопросов из JSON файла
def load_questions():
    with open("questions.json", 'r', encoding='utf-8') as file:
        return json.load(file)

questions = load_questions()

# Инициализация бота и диспетчера
API_TOKEN = "6847241186:AAHVKq9G3nDnWIyjg9uMiZPEU4WMnZMXhFA"
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Команда /start
@dp.message_handler(Command("start"))
async def start(message: types.Message):
    message.conf['current_question'] = 0
    message.conf['score'] = 0
    await ask_question(message)

# Задание вопроса
async def ask_question(message: types.Message):
    question_data = questions[message.conf['current_question']]
    question_text = question_data['question']
    options = question_data['options']

    keyboard = [[InlineKeyboardButton(option, callback_data=option)] for option in options]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.reply(question_text, reply_markup=reply_markup)

# Обработка нажатия на кнопку
@dp.callback_query_handler(lambda c: True)
async def button(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    selected_option = callback_query.data
    current_question_index = callback_query.message.conf.get('current_question', 0)
    correct_answer = questions[current_question_index]['answer']

    if selected_option == correct_answer:
        response_text = f"Правильно! Ответ: {correct_answer}"
        callback_query.message.conf['score'] = callback_query.message.conf.get('score', 0) + 1
    else:
        response_text = f"Неправильно. Правильный ответ: {correct_answer}"

    await bot.edit_message_text(text=response_text, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)

    callback_query.message.conf['current_question'] = current_question_index + 1
    if callback_query.message.conf['current_question'] < len(questions):
        await ask_question(callback_query.message)
    else:
        user_id = str(callback_query.from_user.id)
        results[user_id] = callback_query.message.conf['score']
        save_results(results)
        await bot.send_message(callback_query.message.chat.id, f"Квиз завершен! Ваш результат: {results[user_id]}/{len(questions)}")

# Загрузка результатов из JSON файла
def load_results():
    if os.path.exists("results.json"):
        with open("results.json", 'r', encoding='utf-8') as file:
            try:
                return json.load(file)
            except json.decoder.JSONDecodeError:
                # Если файл пустой или содержит некорректные данные, возвращаем пустой словарь
                return {}
    else:
        # Создаем пустой файл results.json, если он не существует
        with open("results.json", 'w', encoding='utf-8') as file:
            json.dump({}, file, ensure_ascii=False, indent=4)
        return {}

# Сохранение результатов в JSON файл
def save_results(results):
    with open("results.json", 'w', encoding='utf-8') as file:
        json.dump(results, file, ensure_ascii=False, indent=4)

results = load_results()

# Команда /stats
@dp.message_handler(Command("stats"))
async def stats(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in results:
        await message.reply(f"Ваш последний результат: {results[user_id]}/{len(questions)}")
    else:
        await message.reply("Вы еще не проходили квиз.")

# Запуск бота
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
