import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
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

# Инициализация бота и диспетчера
API_TOKEN = "6847241186:AAHVKq9G3nDnWIyjg9uMiZPEU4WMnZMXhFA"
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Синхронизация доступа к файлу результатов
results_lock = threading.Lock()

# Класс для хранения состояния квиза
class QuizStates(StatesGroup):
    question = State()
    score = State()

# Команда /start
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.set_data({"current_question": 0, "score": 0})
    await ask_question(message, state)

# Задание вопроса
async def ask_question(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    current_question_index = user_data['current_question']
    question_data = questions[current_question_index]
    question_text = question_data['question']
    options = question_data['options']

    keyboard = [[InlineKeyboardButton(text=option, callback_data=option)] for option in options]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.answer(question_text, reply_markup=reply_markup)
    await state.set_state(QuizStates.question)

# Обработка нажатия на кнопку
@dp.callback_query(lambda callback_query: True, QuizStates.question)
async def button(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()

    selected_option = callback_query.data
    user_data = await state.get_data()
    current_question_index = user_data['current_question']
    correct_answer = questions[current_question_index]['answer']

    if selected_option == correct_answer:
        response_text = f"Правильно! Ответ: {correct_answer}"
        new_score = user_data['score'] + 1
        await state.update_data(score=new_score)
    else:
        response_text = f"Неправильно. Правильный ответ: {correct_answer}"

    await bot.edit_message_text(
        text=response_text,
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )

    if current_question_index + 1 < len(questions):
        await state.update_data(current_question=current_question_index + 1)
        await ask_question(callback_query.message, state)
    else:
        user_id = str(callback_query.from_user.id)
        user_score = user_data['score']
        results[user_id] = user_score
        save_results(results)
        await bot.send_message(callback_query.message.chat.id, f"Квиз завершен! Ваш результат: {user_score}/{len(questions)}")
        await state.clear()

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
@dp.message(Command("stats"))
async def stats(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in results:
        await message.reply(f"Ваш последний результат: {results[user_id]}/{len(questions)}")
    else:
        await message.reply("Вы еще не проходили квиз.")

# Запуск бота
async def main():
    dp.include_router(dp.router)
    await bot.start_polling(dp)

if __name__ == '__main__':
    asyncio.run(main())
