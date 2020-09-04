import requests
import time

token = "1338383686:AAHTzCQAg345W3nCl6GTy7n8mWN4IwLdxUE"

# https://api.telegram.org/bot1338383686:AAHTzCQAg345W3nCl6GTy7n8mWN4IwLdxUE/sendmessage?chat_id=943519774&text=hi
URL = "https://api.telegram.org/bot" + token + "/"


def get_updates():
    url = URL + "getupdates"
    r = requests.get(url)
    return r.json()


def get_message():
    data = get_updates()
    chat_id = data["result"][-1]["message"]["chat"]["id"]
    message_text = data["result"][-1]["message"]["text"]
    update_id = data["result"][-1]["update_id"]
    message = {"chat_id": chat_id, "text": message_text, "update_id": update_id}
    return message


def send_message(chat_id, text="Wait a second please..."):
    url = URL + "sendmessage?chat_id={}&text={}".format(chat_id, text)
    requests.get(url)


def main():
    # with open("updates.json", "w") as file:
    #     json.dump(updates, file, indent=2, ensure_ascii=False)
    prev_update_id = None
    while True:
        answer = get_message()
        current_update_id = answer["update_id"]
        print(current_update_id, prev_update_id)

        if prev_update_id != current_update_id:
            if answer["text"] == "pic":
                text_to_send = requests.get("https://loremflickr.com/320/240", allow_redirects=True).url
            else:
                text_to_send = "Type 'pic' to get a new picture"
            send_message(answer["chat_id"], text_to_send)
            prev_update_id = current_update_id

        time.sleep(1)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
