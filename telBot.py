from flask import Flask
from flask import request
from flask import Response
from info import bot_token
import requests
import telegram

app = Flask(__name__)
TOKEN = bot_token
bot = telegram.Bot(token=TOKEN)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        msg = request.get_json()

        chat_id, txt = parse_message(msg)  # retrieve chat_id and txt from msg
        if txt == "/id":
            sendMsg(chat_id, "Your user id: " + str(chat_id))
        elif txt == "/start":
            start(chat_id)

        return Response('ok', status=200)
    else:
        return "<h1>Welcome!</h1>"


def start(chat_id):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'

   # Create inline keyboard markup
    keyboard = [
        [
            telegram.InlineKeyboardButton(
                'MATIC/USDC', callback_data='0xa374094527e1673a86de625aa59517c5de346d32'),
            telegram.InlineKeyboardButton(
                'MATIC/USDT', callback_data='0x9b08288c3be4f62bbf8d1c20ac9c5e6f9467d8b7')
        ]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    # Send message with inline keyboard
    bot.send_message(chat_id=chat_id, text='Selecione o par:',
                     reply_markup=reply_markup)

    # Wait for the two inputs
    bot.send_message(chat_id=chat_id, text='Digite o valor mínimo da pool:')
    lowPrice = None
    while lowPrice is None:
        updates = bot.get_updates()
        for update in updates:
            if update.message:
                if update.message.chat_id == chat_id:
                    lowPrice = update.message.text

    bot.send_message(chat_id=chat_id, text='Digite o valor máximo da pool:')
    highPrice = None
    while highPrice is None:
        updates = bot.get_updates()
        for update in updates:
            if update.message:
                if update.message.chat_id == chat_id:
                    highPrice = update.message.text
    return r


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
