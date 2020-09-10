import telebot
import collections
import pytrivia

token = "1338383686:AAHTzCQAg345W3nCl6GTy7n8mWN4IwLdxUE"
# https://api.telegram.org/bot1338383686:AAHTzCQAg345W3nCl6GTy7n8mWN4IwLdxUE/sendmessage?chat_id=943519774&text=hi

bot = telebot.TeleBot(token)
trivia_api = pytrivia.Trivia(with_token=True)

MAIN_STATE = "main_state"
GAME_STATE = "game_state"
SET_QUESTION_COUNT_STATE = "question_count_state"
SET_DIFFICULTY_STATE = "difficulty_state"

DEFAULT_SETTINGS = {"question_count": 3,
                    "difficulty": pytrivia.Diffculty.Easy,
                    "category": pytrivia.Category.Computers
                    }

states = {}
questions = {}
settings = {}


def initialize_game(user_id):
    current_settings = get_current_settings(user_id)

    # Функция уходит в бесконечный цикл, если запросить вопросов больше, чем есть
    # ошибка внутри библиотеки
    # есть другая библиотека, можно попробовать ее
    api_reply = trivia_api.request(current_settings["question_count"],
                                   current_settings["category"],
                                   current_settings["difficulty"],
                                   pytrivia.Type.Multiple_Choice)

    questions[user_id] = collections.deque()
    counter = 1
    for question_description in api_reply["results"]:
        questions[user_id].append("Вопрос {0}:\n {1}".format(counter, question_description["question"]))
        counter += 1


def send_next_question(user_id):
    text = questions[user_id].popleft()
    bot.send_message(user_id, text)


def get_current_settings(user_id):
    if user_id not in settings:
        # тут же  я правильно скопировал это дело? Иначе будет один объект для всех пользователей?
        settings[user_id] = dict(DEFAULT_SETTINGS)
    return settings[user_id]


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
            current_settings = get_current_settings(user_id)
            start_game_message = "Это беспроигрышная пока игра. Можно отвечать что угодно:)\n" \
                                 "Количество вопросов: {0}\n" \
                                 "Сложность: {1}\n" \
                                 "Категория: {2}".format(current_settings["question_count"],
                                                         current_settings["difficulty"], current_settings["category"])

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
    user_id = message.from_user.id
    current_settings = get_current_settings(user_id)
    current_settings["question_count"] = int(message.text)
    bot.reply_to(message, "Принял")
    bot.send_message(user_id, "Выберем сложность вопросов ('легко', 'средне', 'сложно')")
    states[user_id] = SET_DIFFICULTY_STATE


@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == SET_DIFFICULTY_STATE)
def set_difficulty_handler(message):
    text = message.text.lower()
    reply_text = "Принял"
    new_state = MAIN_STATE
    user_id = message.from_user.id
    current_settings = get_current_settings(user_id)

    if text == "легко":
        current_settings["difficulty"] = pytrivia.Diffculty.Easy
    elif text == "средне":
        current_settings["difficulty"] = pytrivia.Diffculty.Medium
    elif text == "сложно":
        current_settings["difficulty"] = pytrivia.Diffculty.Hard
    else:
        reply_text = "Надо выбрать из трех вариантов: 'легко', 'средне', 'сложно'"
        new_state = None

    bot.reply_to(message, reply_text)

    if new_state is not None:
        states[user_id] = new_state


def main():
    bot.polling()


if __name__ == '__main__':
    main()
