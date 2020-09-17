import telebot
import collections
import pytrivia
import random

token = "1338383686:AAHTzCQAg345W3nCl6GTy7n8mWN4IwLdxUE"
# https://api.telegram.org/bot1338383686:AAHTzCQAg345W3nCl6GTy7n8mWN4IwLdxUE/sendmessage?chat_id=943519774&text=hi

bot = telebot.TeleBot(token, num_threads=1)
trivia_api = pytrivia.Trivia(with_token=False)

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


class QuestionsAPIError(Exception):
    def __init__(self, description):
        self._description = "Произошла ошибка при формировании списка вопросов: {}".format(description)
        if not description.strip():
            self._description += "неизвестная ошибка"

    def __str__(self):
        return self._description


def initialize_game(user_id):
    current_settings = get_current_settings(user_id)

    # Функция уходит в бесконечный цикл, если запросить вопросов больше, чем есть в данной категории при использовании токена
    # ошибка в самом api - по документации в этом случае должен быть код возврата 1, а он - 4
    # так как мы инициализируем игру каждый раз, то повторяющихся вопросов быть не должно, и токен можно не использовать
    # без токена работает ожидаемо
    try:
        api_reply = trivia_api.request(current_settings["question_count"],
                                       current_settings["category"],
                                       current_settings["difficulty"],
                                       pytrivia.Type.Multiple_Choice)
    except ValueError:
        raise QuestionsAPIError(
            "Число вопросов должно быть в интервале [1,50], а оно равно {}".format(current_settings["question_count"]))
    except Exception as error:
        raise QuestionsAPIError(str(error))

    questions[user_id] = collections.deque()
    counter = 1
    for question_description in api_reply["results"]:
        questions[user_id].append("Вопрос {0}:\n {1}".format(counter, question_description["question"]))
        counter += 1

    if not questions[user_id]:
        raise QuestionsAPIError(
            "не удалось получить ни одного вопроса. Попробуйте уменьшить число вопросов в настройках")


def send_next_question(user_id):
    text = questions[user_id].popleft()
    bot.send_message(user_id, text)


def get_current_settings(user_id):
    if user_id not in settings:
        settings[user_id] = DEFAULT_SETTINGS.copy()
    return settings[user_id]


def gen_main_menu_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(telebot.types.InlineKeyboardButton("Играть", callback_data="play"),
               telebot.types.InlineKeyboardButton("Настройки", callback_data="settings"))
    return markup


@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == MAIN_STATE)
def main_handler(message):
    text = message.text.lower()
    if text == "/start" or text == "привет":
        bot.reply_to(message, "Привет, {0}! Меню:".format(message.from_user.first_name),
                     reply_markup=gen_main_menu_markup())
    else:
        bot.reply_to(message, "Я вас не понял: '" + message.text + "'", reply_markup=gen_main_menu_markup())


@bot.callback_query_handler(func=lambda call: states.get(call.from_user.id, MAIN_STATE) == MAIN_STATE)
def main_menu_handler(call):
    user_id = call.from_user.id
    if call.data == "play":
        bot.send_chat_action(user_id, "typing")
        try:
            initialize_game(user_id)
        except QuestionsAPIError as error:
            bot.send_message(user_id, str(error))
            return

        current_settings = get_current_settings(user_id)
        start_game_message = "Это беспроигрышная пока игра. Можно отвечать что угодно:)\n" \
                             "Количество вопросов: {0}\n" \
                             "Сложность: {1}\n" \
                             "Категория: {2}".format(current_settings["question_count"],
                                                     current_settings["difficulty"], current_settings["category"])

        bot.send_message(user_id, start_game_message)
        send_next_question(user_id)
        states[user_id] = GAME_STATE
        bot.answer_callback_query(call.id)
    elif call.data == "settings":
        get_current_settings(user_id)["category"] = random.choice(list(pytrivia.Category))
        bot.send_message(user_id, "Введи количество вопросов (1-50)")
        states[user_id] = SET_QUESTION_COUNT_STATE
        bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == GAME_STATE)
def game_handler(message):
    user_id = message.from_user.id
    bot.reply_to(message, "Верно!")
    if not questions[user_id]:
        bot.send_message(user_id, "Игра закончена!",reply_markup=gen_main_menu_markup())
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
