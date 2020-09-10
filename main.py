import telebot
import collections
import pytrivia

token = "1338383686:AAHTzCQAg345W3nCl6GTy7n8mWN4IwLdxUE"
# https://api.telegram.org/bot1338383686:AAHTzCQAg345W3nCl6GTy7n8mWN4IwLdxUE/sendmessage?chat_id=943519774&text=hi

bot = telebot.TeleBot(token)
trivia_api = pytrivia.Trivia(with_token=True)

states = {}
MAIN_STATE = "main_state"
GAME_STATE = "game_state"
SET_QUESTION_COUNT_STATE = "question_count_state"
SET_DIFFICULTY_STATE = "difficulty_state"

questions = {}
settings = {"question_count": 3,
            "difficulty": pytrivia.Diffculty.Easy,
            "category" : pytrivia.Category.Computers
            }


def initialize_game(user_id):
    api_reply = trivia_api.request(settings["question_count"],
                                   settings["category"],
                                   settings["difficulty"],
                                   pytrivia.Type.Multiple_Choice)

    questions[user_id] = collections.deque()
    counter = 1
    for question_description in api_reply["results"]:
        questions[user_id].append("Вопрос {0}:\n {1}".format(counter, question_description["question"]))
        counter += 1


def send_next_question(user_id):
    text = questions[user_id].popleft()
    bot.send_message(user_id, text)


@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == MAIN_STATE)
def main_handler(message):
    text = message.text.lower()
    user_id = message.from_user.id
    if text == "/start" or text == "привет":
        bot.reply_to(message, "Привет, {0}! Напиши 'играть' или 'настройки'".format(message.from_user.first_name))
    elif text == "играть":
        initialize_game(user_id)
        if not questions[user_id]:
            bot.reply_to(message, "Не удалось получить ни одного вопроса")
        else:
            start_game_message = "Это беспроигрышная пока игра. Можно отвечать что угодно:)\n" \
                                 "Количество вопросов: {0}\n" \
                                 "Сложность: {1}\n" \
                                 "Категория: {2}".format(settings["question_count"], settings["difficulty"], settings["category"])

            bot.reply_to(message, start_game_message)
            send_next_question(user_id)
            states[user_id] = GAME_STATE
    elif text == "настройки":
        bot.reply_to(message, "Введи количество вопросов (1-50)")
        states[user_id] = SET_QUESTION_COUNT_STATE
    else:
        bot.reply_to(message, "Я не понимаю таких слов: '" + message.text + "'")


@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == GAME_STATE)
def game_handler(message):
    user_id = message.from_user.id
    bot.reply_to(message, "Верно!")
    if not questions[user_id]:
        bot.send_message(user_id, "Игра закончена!")
        states[user_id] = MAIN_STATE
    else:
        send_next_question(user_id)


@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == SET_QUESTION_COUNT_STATE)
def set_question_count_handler(message):
    settings["question_count"] = int(message.text)
    bot.reply_to(message, "Принял")
    bot.send_message(message.from_user.id, "Выберем сложность вопросов ('легко', 'средне', 'сложно')")
    states[message.from_user.id] = SET_DIFFICULTY_STATE


@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == SET_DIFFICULTY_STATE)
def set_difficulty_handler(message):
    text = message.text.lower()
    reply_text = "Принял"
    new_state = MAIN_STATE

    if text == "легко":
        settings["difficulty"] = pytrivia.Diffculty.Easy
    elif text == "средне":
        settings["difficulty"] = pytrivia.Diffculty.Medium
    elif text == "сложно":
        settings["difficulty"] = pytrivia.Diffculty.Hard
    else:
        reply_text = "Надо выбрать из трех вариантов: 'легко', 'средне', 'сложно'"
        new_state = None

    bot.reply_to(message, reply_text)

    if new_state is not None:
        states[message.from_user.id] = new_state


def main():
    bot.polling()


if __name__ == '__main__':
    main()
