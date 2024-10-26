import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os

def load_questions():
    with open("C://Users//YERO//Documents//Python projects//Questions.json", 'r', encoding='utf-8') as file:
        return json.load(file)

questions = load_questions()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['current_question'] = 0
    context.user_data['score'] = 0
    await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question_data = questions[context.user_data['current_question']]
    question_text = question_data['question']
    options = question_data['options']

    keyboard = [[InlineKeyboardButton(option, callback_data=option)] for option in options]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(question_text, reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    selected_option = query.data
    current_question_index = context.user_data['current_question']
    correct_answer = questions[current_question_index]['answer']

    if selected_option == correct_answer:
        response_text = f"Правильно! Ответ: {correct_answer}"
        context.user_data['score'] += 1
    else:
        response_text = f"Неправильно. Правильный ответ: {correct_answer}"

    await query.edit_message_text(text=response_text)

    context.user_data['current_question'] += 1
    if context.user_data['current_question'] < len(questions):
        await ask_question(query, context)
    else:
        user_id = str(update.effective_user.id)
        results[user_id] = context.user_data['score']
        save_results(results)
        await query.message.reply_text(f"Квиз завершен! Ваш результат: {results[user_id]}/{len(questions)}")

# Load results from JSON file
def load_results():
    if os.path.exists("results.json"):
        with open("results.json", 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

# Save user results to JSON file
def save_results(results):
    with open("results.json", 'w', encoding='utf-8') as file:
        json.dump(results, file, ensure_ascii=False, indent=4)

results = load_results()

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if user_id in results:
        await update.message.reply_text(f"Ваш последний результат: {results[user_id]}/{len(questions)}")
    else:
        await update.message.reply_text("Вы еще не проходили квиз.")

def main() -> None:
    application = Application.builder().token("6847241186:AAHVKq9G3nDnWIyjg9uMiZPEU4WMnZMXhFA").build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler('stats', stats))

    application.run_polling()

if __name__ == '__main__':
    main()
