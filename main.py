import telebot
import collections
import pytrivia
import random
import datetime
import os
import redis

REDDIS_URL = os.environ.get("REDDIS_URL")

dict_db = {}


def save(key, value):
    if REDDIS_URL:
        redis_db = redis.from_url(REDDIS_URL)
        redis_db.set(key, value)
    else:
        dict_db[key] = value


def load(key):
    if REDDIS_URL:
        redis_db = redis.from_url(REDDIS_URL)
        return redis_db.get(key)
    return dict_db.get(key)


token = os.environ["TELEGRAM_TOKEN"]

bot = telebot.TeleBot(token, num_threads=1)
trivia_api = pytrivia.Trivia(with_token=False)

MAIN_STATE = "main_state"
GAME_STATE = "game_state"
SET_QUESTION_COUNT_STATE = "question_count_state"
SET_DIFFICULTY_STATE = "difficulty_state"
SET_CATEGORY_STATE = "category_state"

DEFAULT_SETTINGS = {"question_count": 3,
                    "difficulty": pytrivia.Diffculty.Easy,
                    "category": pytrivia.Category.Computers
                    }

states = {}
questions = {}
settings = {}
current_correct_answer = {}
current_game_statistic = {}


class QuestionsAPIError(Exception):
    def __init__(self, description):
        self._description = "Произошла ошибка при формировании списка вопросов: {}".format(description)
        if not description.strip():
            self._description += "неизвестная ошибка"

    def __str__(self):
        return self._description


def print_game_statistic(user_id, stat):
    time_delta = datetime.datetime.now() - stat["time"]
    stat_message = "Статистика игры:\n" \
                   "Потраченное время: {0}\n" \
                   "Результат: {1}/{2}\n".format(time_delta,
                                                 stat["correct_answers_count"],
                                                 stat["correct_answers_count"] + stat["incorrect_answers_count"])
    bot.send_message(user_id, stat_message, reply_markup=gen_main_menu_markup())


def initialize_game(user_id):
    current_game_statistic[user_id] = dict()
    current_game_statistic[user_id]["time"] = datetime.datetime.now()
    current_game_statistic[user_id]["correct_answers_count"] = 0
    current_game_statistic[user_id]["incorrect_answers_count"] = 0
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
        question_with_answers = dict()
        question_with_answers["question"] = "Вопрос {0}:\n {1}".format(counter, question_description["question"])
        question_with_answers["correct_answer"] = question_description["correct_answer"]
        question_with_answers["incorrect_answers"] = question_description["incorrect_answers"]
        questions[user_id].append(question_with_answers)
        counter += 1

    if not questions[user_id]:
        raise QuestionsAPIError(
            "не удалось получить ни одного вопроса. Попробуйте уменьшить число вопросов в настройках")


def send_next_question(user_id):
    question_with_answers = questions[user_id].popleft()
    bot.send_message(user_id, question_with_answers["question"],
                     reply_markup=gen_answers_markup(question_with_answers["correct_answer"],
                                                     question_with_answers["incorrect_answers"]))
    current_correct_answer[user_id] = question_with_answers["correct_answer"]


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


def gen_difficulty_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(telebot.types.InlineKeyboardButton("Легко", callback_data="easy"),
               telebot.types.InlineKeyboardButton("Средне", callback_data="medium"),
               telebot.types.InlineKeyboardButton("Сложно", callback_data="hard"))
    return markup


def gen_category_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row_width = 3

    buttons = []
    for category in list(pytrivia.Category):
        buttons.append(telebot.types.InlineKeyboardButton(category.name, callback_data=category.value))

    markup.add(*buttons)
    return markup


def gen_answers_markup(correct_answer, incorrect_answers):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row_width = 1
    buttons = list()
    buttons.append(telebot.types.InlineKeyboardButton(correct_answer, callback_data="correct"))

    for incorrect_answer in incorrect_answers:
        buttons.append(telebot.types.InlineKeyboardButton(incorrect_answer, callback_data="incorrect"))

    random.shuffle(buttons)
    markup.add(*buttons)
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
            bot.send_message(user_id, str(error), reply_markup=gen_main_menu_markup())
        else:
            current_settings = get_current_settings(user_id)
            start_game_message = "Начинаем!\n" \
                                 "Количество вопросов: {0}\n" \
                                 "Сложность: {1}\n" \
                                 "Категория: {2}".format(current_settings["question_count"],
                                                         current_settings["difficulty"], current_settings["category"])

            bot.send_message(user_id, start_game_message)
            send_next_question(user_id)
            states[user_id] = GAME_STATE

    elif call.data == "settings":
        bot.send_message(user_id, "Введите количество вопросов (1-50)")
        states[user_id] = SET_QUESTION_COUNT_STATE

    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == GAME_STATE)
def game_handler(message):
    user_id = message.from_user.id
    bot.reply_to(message, "Игра прервана! Возвращаемся в главное меню")
    print_game_statistic(user_id, current_game_statistic[user_id])
    states[user_id] = MAIN_STATE


@bot.callback_query_handler(func=lambda call: states.get(call.from_user.id, MAIN_STATE) == GAME_STATE)
def game_handler(call):
    user_id = call.from_user.id
    data = call.data
    if data == "correct":
        bot.send_message(user_id, "Верно!")
        current_game_statistic[user_id]["correct_answers_count"] += 1
    elif data == "incorrect":
        bot.send_message(user_id, "Неверно! Правильный ответ: {}".format(current_correct_answer[user_id]))
        current_game_statistic[user_id]["incorrect_answers_count"] += 1
    else:
        assert False, "Invalid call.data {}".format(data)

    if not questions[user_id]:
        bot.send_message(user_id, "Игра закончена!")
        print_game_statistic(user_id, current_game_statistic[user_id])
        states[user_id] = MAIN_STATE
    else:
        send_next_question(user_id)

    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == SET_QUESTION_COUNT_STATE)
def set_question_count_handler(message):
    user_id = message.from_user.id
    current_settings = get_current_settings(user_id)
    try:
        current_settings["question_count"] = int(message.text)
    except ValueError:
        bot.reply_to(message, "Пожалуйста, введите целое число от 1 до 50 включительно")
    else:
        bot.reply_to(message, "Принял")
        bot.send_message(user_id, "Выберем сложность вопросов",
                         reply_markup=gen_difficulty_markup())
        states[user_id] = SET_DIFFICULTY_STATE


@bot.callback_query_handler(func=lambda call: states.get(call.from_user.id, MAIN_STATE) == SET_DIFFICULTY_STATE)
def set_difficulty_handler(call):
    user_id = call.from_user.id
    current_settings = get_current_settings(user_id)
    data = call.data

    if data == "easy":
        current_settings["difficulty"] = pytrivia.Diffculty.Easy
    elif data == "medium":
        current_settings["difficulty"] = pytrivia.Diffculty.Medium
    elif data == "hard":
        current_settings["difficulty"] = pytrivia.Diffculty.Hard
    else:
        assert False, "Invalid call.data={}".format(data)

    bot.send_message(user_id, "Выберем категорию",
                     reply_markup=gen_category_markup())
    states[user_id] = SET_CATEGORY_STATE
    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == SET_DIFFICULTY_STATE)
def set_question_count_handler(message):
    bot.reply_to(message, "Я вас не понял: '" + message.text + "'. " + "Выберем сложность игры:",
                 reply_markup=gen_difficulty_markup())


@bot.callback_query_handler(func=lambda call: states.get(call.from_user.id, MAIN_STATE) == SET_CATEGORY_STATE)
def set_category_handler(call):
    user_id = call.from_user.id
    current_settings = get_current_settings(user_id)
    data = call.data
    category = pytrivia.Category(int(data))
    current_settings["category"] = category
    bot.send_message(user_id, "Настройки приняты", reply_markup=gen_main_menu_markup())
    states[user_id] = MAIN_STATE
    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == SET_CATEGORY_STATE)
def set_question_count_handler(message):
    bot.reply_to(message, "Я вас не понял: '" + message.text + "'. " + "Выберем категорию:",
                 reply_markup=gen_category_markup())


def main():
    bot.polling(none_stop=True)


if __name__ == '__main__':
    main()
