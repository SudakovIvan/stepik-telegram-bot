import pytrivia
import telebot
import random


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