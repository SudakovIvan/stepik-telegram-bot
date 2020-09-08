import telebot
import requests

token = "1338383686:AAHTzCQAg345W3nCl6GTy7n8mWN4IwLdxUE"
# https://api.telegram.org/bot1338383686:AAHTzCQAg345W3nCl6GTy7n8mWN4IwLdxUE/sendmessage?chat_id=943519774&text=hi

bot = telebot.TeleBot(token)

states = {}
MAIN_STATE = "main"
GAME_STATE = "game"
SETTINGS_STATE = "settings"


@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == MAIN_STATE)
def main_handler(message):
    text = message.text.lower()
    if text == "/start" or text == "привет":
        bot.reply_to(message, "Привет, {0}! Напиши 'играть' или 'настройки'".format(message.from_user.first_name))
    elif text == "играть":
        original_reply = str(requests.get("https://engine.lifeis.porn/api/millionaire.php?q=2").json())
        # что за непонятные символы? Это потому, что бесплатно?
        corrected_reply = original_reply.replace(u"\\u2063", "")
        bot.reply_to(message, corrected_reply)
        states[message.from_user.id] = GAME_STATE
    elif text == "настройки":
        states[message.from_user.id] = SETTINGS_STATE
    else:
        bot.reply_to(message, "Я не понимаю таких слов: '" + message.text + "'")


@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == GAME_STATE)
def game_handler(message):
    bot.reply_to(message, "в игре")


@bot.message_handler(func=lambda message: states.get(message.from_user.id, MAIN_STATE) == SETTINGS_STATE)
def game_handler(message):
    bot.reply_to(message, "в настройках")


def main():
    bot.polling()


if __name__ == '__main__':
    main()
