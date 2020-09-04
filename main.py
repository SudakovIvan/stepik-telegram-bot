import telebot
import requests

token = "1338383686:AAHTzCQAg345W3nCl6GTy7n8mWN4IwLdxUE"
# https://api.telegram.org/bot1338383686:AAHTzCQAg345W3nCl6GTy7n8mWN4IwLdxUE/sendmessage?chat_id=943519774&text=hi

bot = telebot.TeleBot(token)

question_counter = 0


@bot.message_handler(func=lambda message: True)
def echo(message):
    if message.text == "/start":
        bot.reply_to(message, "Напиши 'Дай вопрос' или 'Сколько вопросов'")
    elif message.text == "Привет":
        bot.reply_to(message, "Привет, " + message.from_user.first_name)
    elif message.text == "Дай вопрос":
        global question_counter
        original_reply = str(requests.get("https://engine.lifeis.porn/api/millionaire.php?q=2").json())
        # что за непонятные символы? Это потому, что бесплатно?
        corrected_reply = original_reply.replace(u"\\u2063","")
        bot.reply_to(message, corrected_reply)
        question_counter += 1
    elif message.text == "Сколько вопросов":
        bot.reply_to(message, "Вопросов выдано: {}".format(question_counter))
    else:
        bot.reply_to(message, "Я не знаю таких слов: '" + message.text + "'")


def main():
    bot.polling()


if __name__ == '__main__':
    main()