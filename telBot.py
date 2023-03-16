import datetime
from flask import Flask
from flask import request
from flask import Response
from info import bot_token
import requests
import json
import pytz
import pymongo
from pymongo import MongoClient
import os


app = Flask(__name__)
TOKEN = bot_token

# Connect to MongoDB
MONGODB_URI = os.environ['MONGODB_URI']
DB_NAME = os.environ['DB_NAME']

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
pools_collection = db['pools']


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':

        msg = request.get_json()
        print(msg)
        msgS = json.dumps(msg)  # convert to string

        if 'text' in msgS and 'callback_query' not in msgS:
            # retrieve chat_id and txt from msg
            chat_id, txt = parse_message(msg)
            print("ignore-->", getIgnore(chat_id))
            if txt == "/id":
                sendMsg(chat_id, "Your user id: " + str(chat_id))
            elif txt == "/start":
                start(chat_id)
            # handle após usuario selecionar o par e se flag ignore for false
            elif '-' in txt and getIgnore(chat_id) != 'true':
                handle_input(chat_id, txt)

            return Response('ok', status=200)

        elif 'callback_query' in msgS:
            handle_callback(msg)
            return Response('ok', status=200)

    else:
        return "<h1>Welcome!</h1>"


def start(chat_id):
    doc = {'ignore': 'false'}
    updateIgnore(chat_id, doc)
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
    queryS = json.dumps(query)
    chat_id = query['message']['chat']['id']

    print(query)

    choice = query['data']
    message_id = query['message']['message_id']

    # Perform action based on user choice
    if choice == '0xa374094527e1673a86de625aa59517c5de346d32':
        # Do something for MATIC/USDC pair
        message = "MATIC/USDC: Defina um intervalo separado por - (Ex: 1.2 - 2.0)"
    elif choice == '0x9b08288c3be4f62bbf8d1c20ac9c5e6f9467d8b7':
        # Do something for MATIC/USDT pair
        message = "MATIC/USDT: Defina um intervalo separado por - (Ex: 1.2 - 2.0)"

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
    print("response-->", response.json())

    # Insert the value into the 'values' collection
    doc = {'poolid': choice, 'chatid': chat_id}
    insertValue(doc)
    print(
        f"Pool ID '{doc['poolid']}' inserted successfully for chat ID '{doc['chatid']}'.")

    return response.json()


def insertValue(doc):
    doc = doc
    pools_collection.insert_one(doc)


def getPoolid(chat_id):
    # Filter for documents with a matching 'chatid'
    filter = {'chatid': chat_id}
    doc = pools_collection.find_one(filter)
    if doc:
        return doc['poolid']
    else:
        return f"No pool ID found for chat ID '{chat_id}'"


def getIgnore(chat_id):
    # Filter for documents with a matching 'chatid'
    filter = {'chatid': chat_id, 'ignore': 'true'}
    doc = pools_collection.find_one(filter)
    if doc:
        return doc['ignore']
    else:
        return f"No ignore found for chat ID '{chat_id}'"


def updateIgnore(chat_id, doc):

    # Update a value in the collection
    # filter to identify the document to update
    filter = {'chatid': chat_id}
    update = {'$set': doc}
    result = pools_collection.update_one(filter, update)

    # Check if the update was successful
    if result.modified_count > 0:
        print("Value updated successfully")
    else:
        print("Value not updated")


def handle_input(chat_id, txt):
    range = txt.split("-")
    lowPrice = float(range[0].strip())
    highPrice = float(range[1].strip())
    pool_id = getPoolid(chat_id)
    print('lowPrice-->', lowPrice)
    print('highPrice-->', highPrice)
    print('pool_id-->', pool_id)

    # Send request to subgraph API
    subgraph_url = 'https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-polygon'
    query = """
        {
        pool(id:\"""" + pool_id + """\"){
            token0 {
            id
            symbol
            }
            token0Price
            token1 {
            id
            symbol
            }
            token1Price
        }
        }
        """

    response = requests.post(subgraph_url, headers={
        'Content-Type': 'application/json'}, json={'query': query})
    data = response.json()
    print("Request--> " + query)
    print("Response--> " + json.dumps(data))
    pool = data['data']['pool']
    token0, token0_price, token1, token1_price = pool['token0'], pool[
        'token0Price'], pool['token1'], pool['token1Price']
    tPrice = float(token1_price)
    t0Symbol = token0['symbol']
    t1Symbol = token1['symbol']
    timestamp = datetime.datetime.now(pytz.timezone(
        'America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M:%S')

    pVariationlow = ((float(lowPrice) - tPrice) / float(lowPrice)) * 100
    pVariationhigh = ((tPrice - float(highPrice)) / float(highPrice)) * 100

    if (tPrice < lowPrice):
        txt = '⚠️⬇️ <b>[' + timestamp + ']</b> : ' + t0Symbol + '/' + t1Symbol + ' abaixo de ' + \
            str(lowPrice) + ': \n\n 👉 ' + str(tPrice) + \
            '(-' + str(round(pVariationlow, 2)) + '%)'
        print(txt)
        sendMsg(chat_id, txt)

    elif (tPrice > highPrice):
        txt = '⚠️⬆️ <b>[' + timestamp + ']</b> : ' + t0Symbol + '/' + t1Symbol + ' acima de ' + \
            str(highPrice) + ': \n\n 👉 ' + str(tPrice) + \
            '(+' + str(round(pVariationhigh, 2)) + '%)'
        print(txt)
        sendMsg(chat_id, txt)

    else:
        txt = '[' + timestamp + '] : ' + t0Symbol + '/' + t1Symbol + ' dentro intervalo de ' + \
            str(lowPrice) + ' a ' + str(highPrice) + \
            ': \n\n ' + str(tPrice)
        sendMsg(txt)
        print(txt)

    doc = {'ignore': 'true'}
    updateIgnore(chat_id, doc)


def sendMsg(chat_id, text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
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
