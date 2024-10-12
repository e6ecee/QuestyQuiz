import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Загрузка вопросов из файла
def load_questions():
    with open("C://Users//YERO//Documents//Python projects//Questions.json", 'r', encoding='utf-8') as file:
        return json.load(file)

questions = load_questions()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['current_question'] = 0
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
    else:
        response_text = f"Неправильно. Правильный ответ: {correct_answer}"

    await query.edit_message_text(text=response_text)

    context.user_data['current_question'] += 1
    if context.user_data['current_question'] < len(questions):
        await ask_question(query, context)
    else:
        await query.message.reply_text("Квиз завершен!")

def main() -> None:
    application = Application.builder().token("6847241186:AAHVKq9G3nDnWIyjg9uMiZPEU4WMnZMXhFA").build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == '__main__':
    main()