from flask import Flask
from flask import request
from flask import Response
from info import bot_token
import requests
import json

app = Flask(__name__)
TOKEN = bot_token


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        msg = request.get_json()
        msgS = json.dumps(msg)  # convert to string

        if 'text' in msgS and 'callback_query' not in msgS and 'edited_message' not in msgS:
            # retrieve chat_id and txt from msg
            chat_id, txt = parse_message(msg)
            if txt == "/id":
                sendMsg(chat_id, "Your user id: " + str(chat_id))
            elif txt == "/start":
                start(chat_id)
            return Response('ok', status=200)
        elif 'callback_query' in msgS:
            handle_callback(msg)
            return Response('ok', status=200)

    else:
        return "<h1>Welcome!</h1>"


def start(chat_id):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'

    payload = {
        'chat_id': chat_id,
        'text': "   Selecione o par:",
        'reply_markup': {
            "inline_keyboard": [[
                {
                    "text": "MATIC/USDC",
                    "callback_data": "0xa374094527e1673a86de625aa59517c5de346d32"
                },
                {
                    "text": "MATIC/USDT",
                    "callback_data": "0x9b08288c3be4f62bbf8d1c20ac9c5e6f9467d8b7"
                }]
            ]
        }
    }
    r = requests.post(url, json=payload)
    print("start-->", payload)
    # sendMsg(chat_id,"Digite o valor mínimo da pool:")
    # lowPrice = request.json['message']['text']
    # sendMsg(chat_id,"Digite o valor máximo da pool:")
    # highPrice = request.json['message']['text']

    return r.json()


def handle_callback(update):
    query = update['callback_query']
    chat_id = query['message']['chat']['id']
    choice = query['data']
    message_id = query['message']['message_id']

    # Perform action based on user choice
    if choice == '0xa374094527e1673a86de625aa59517c5de346d32':
        # Do something for MATIC/USDC pair
        message = "You selected MATIC/USDC."
    elif choice == '0x9b08288c3be4f62bbf8d1c20ac9c5e6f9467d8b7':
        # Do something for MATIC/USDT pair
        message = "You selected MATIC/USDT."

    # Send message to user to confirm their choice
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    response = requests.post(url, json=payload)
    print("handle_callback-->", payload)

    # Hide the reply_markup
    url = f'https://api.telegram.org/bot{TOKEN}/editMessageReplyMarkup'
    payload = {
        'chat_id': chat_id,
        'message_id': message_id,
        'reply_markup': {'inline_keyboard': []}
    }
    response = requests.post(url, json=payload)

    # Hide the text above the buttons
    url = f'https://api.telegram.org/bot{TOKEN}/editMessageText'
    payload = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': ""
    }
    response = requests.post(url, json=payload)

    return response.json()


def sendMsg(chat_id, text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text
    }

    r = requests.post(url, json=payload)
    return r


def parse_message(message):

    print("message-->", message)
    chat_id = message['message']['chat']['id']
    txt = message['message']['text']

    print("chat_id-->", chat_id)
    print("txt-->", txt)

    return chat_id, txt


if __name__ == '__main__':
    app.run(debug=True)
