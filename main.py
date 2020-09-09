import telebot
import requests
import pytrivia

token = "1338383686:AAHTzCQAg345W3nCl6GTy7n8mWN4IwLdxUE"
# https://api.telegram.org/bot1338383686:AAHTzCQAg345W3nCl6GTy7n8mWN4IwLdxUE/sendmessage?chat_id=943519774&text=hi

bot = telebot.TeleBot(token)
trivia_api = pytrivia.Trivia(with_token=True)

states = {}
MAIN_STATE = "main"
GAME_STATE = "game"
SETTINGS_STATE = "settings"

questions = []
question_counter = 1


def initialize_game():
    api_reply = trivia_api.request(3, None, None, pytrivia.Type.Multiple_Choice)
    for question_description in api_reply["results"]:
        questions.append(question_description["question"])


def send_next_question(user_id):
    global question_counter
    text = "Вопрос {0}:\n{1}".format(question_counter, questions.pop())
    bot.send_message(user_id, text)
    question_counter += 1


@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == MAIN_STATE)
def main_handler(message):
    text = message.text.lower()
    if text == "/start" or text == "привет":
        bot.reply_to(message, "Привет, {0}! Напиши 'играть' или 'настройки'".format(message.from_user.first_name))
    elif text == "играть":
        initialize_game()
        if not questions:
            bot.reply_to(message, "Не удалось получить ни одного вопроса")
        else:
            bot.reply_to(message, "Это беспроигрышная пока игра. Можно отвечать что угодно:)")
            send_next_question(message.from_user.id)
            states[message.from_user.id] = GAME_STATE
    elif text == "настройки":
        states[message.from_user.id] = SETTINGS_STATE
    else:
        bot.reply_to(message, "Я не понимаю таких слов: '" + message.text + "'")


@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == GAME_STATE)
def game_handler(message):
    user_id = message.from_user.id
    bot.reply_to(message, "Верно!")
    if not questions:
        bot.send_message(user_id, "Игра закончена!")
        states[user_id] = MAIN_STATE
    else:
        send_next_question(user_id)


@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == SETTINGS_STATE)
def game_handler(message):
    bot.reply_to(message, "в настройках")


def main():
    bot.polling()


if __name__ == '__main__':
    main()
