import datetime
from flask import Flask
from flask import request
from flask import Response
import requests
import json
import pytz
import pymongo
from pymongo import MongoClient
import os


app = Flask(__name__)
# Enviroment variables
TOKEN = os.environ['BOT_TOKEN']
MONGODB_URI = os.environ['MONGODB_URI']
DB_NAME = os.environ['DB_NAME']
CRON_API = '1uKTRpu7D5c0P6mEAJF4sPCxqSUGiiyfXdPpuK+EpR0='

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
            elif txt == "/remove":
                remove(chat_id)
            # handle após usuario selecionar o par e se flag ignore for false
            elif '-' in txt and getIgnore(chat_id) != 'true':
                handle_input(chat_id, txt)

            return Response('ok', status=200)

        elif 'callback_query' in msgS:
            handle_callback(msg)
            return Response('ok', status=200)

    else:
        return "<h1>Welcome!</h1>"


def setIgnoreFalse(chat_id):
    doc = {'ignore': 'false'}
    flt = {'chatid': chat_id}
    updateIgnore(chat_id, flt, doc)


def remove(chat_id):
    setIgnoreFalse(chat_id)  # Update ignore flag

    # Currently remove all monitorings, but it's possible to add feature to remove for user selected pools in the future if needed
    removeCronjob(chat_id)
    sendMsg(chat_id, "Monitoramento removido com sucesso!")


def removeCronjob(chat_id):
    # Find all documents that match the chatId and retrieve the cronJob values
    cronJobs = pools_collection.find({"chatid": chat_id}, {"cronJob": 1})

    # Iterate over the cronJob values and call an API
    for cronJob in cronJobs:
        try:
            api_url = "https://api.cron-job.org/jobs/" + \
                str(cronJob['cronJob'])
            print(api_url)
            headers = {
                'Authorization': f'Bearer {CRON_API}',
                'Content-Type': 'application/json'
            }

            response = requests.delete(api_url, headers=headers)

            # Handle the response
            if response.status_code == 200:
                # Success
                print("Job delete successfully!")
            else:
                # Error
                print(f'Error updating job-->', response)
        except Exception as e:
            print(e)

    doc = {'cronJob': ''}
    flt = {'chatid': chat_id}
    update = {'$set': doc}
    result = pools_collection.update_one(
        flt, update)  # update the pools_collection with the update variable filtering by chatid

    # Check if the update was successful
    if result.modified_count > 0:
        print("Cronjob updated successfully")
    else:
        print("Cronjob not updated")


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
                },
                {
                    "text": "WETH/USDC",
                    "callback_data": "0x45dda9cb7c25131df268515131f647d726f50608"
                }]
            ]
        }
    }
    r = requests.post(url, json=payload)
    print("start-->", payload)

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
    elif choice == '0x45dda9cb7c25131df268515131f647d726f50608':
        # Do something for WETH/USDC pair
        message = "WETH/USDC: Defina um intervalo separado por - (Ex: 1700 - 1750)"

    checkDoc = {'poolid': choice, 'chatid': chat_id, 'ignore': 'true'}
    if (checkExist(checkDoc) != 'NF'):  # Check if there's existing monitoring before proceeding
        sendMsg(chat_id, "Já existe um monitoramento ativo para o par selecionado! Use o comando remove para remover monitoramentos atuais.")

    else:
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
        ts = datetime.datetime.now()
        doc = {'poolid': choice, 'chatid': chat_id, 'lastUpdate': ts}
        checkDoc = {'poolid': choice, 'chatid': chat_id}
        if (checkExist(checkDoc) == 'NF'):  # Check if exist before inserting
            insertValue(doc)
            print(
                f"Pool ID '{doc['poolid']}' inserted successfully for chat ID '{doc['chatid']}'.")
        else:
            print(
                f"Pool ID '{doc['poolid']}' for chat ID '{doc['chatid']}' already exists.")
            doc = {'lastUpdate': ts}
            # update timestamp even if the pool exists, so that it can pick the right pool when handling the range
            updateTimestamp(doc, checkDoc)

        return response.json()


def insertValue(doc):
    doc = doc
    pools_collection.insert_one(doc)


def getPoolid(chat_id):
    # Filter for documents with a matching 'chatid'
    flt = {'chatid': chat_id}
    collection_list = list(pools_collection.find(flt))
    sorted_collection = sorted(
        collection_list, key=lambda x: x["lastUpdate"], reverse=True)
    if sorted_collection:
        last_inserted_item = sorted_collection[0]

        # Get the last inserted item that matches the filter
        # Check if the last inserted item matches the filter
        if last_inserted_item.get('chatid') == chat_id and all(last_inserted_item.get(k) == v for k, v in flt.items()):
            return last_inserted_item['poolid']
        else:
            print("No matching item found")
    else:
        print("The collection is empty")
    # flt = {'chatid': chat_id}
    # doc = pools_collection.find_one(filter)
    # if doc:
    #    return doc['poolid']
    # else:
    #    return f"No pool ID found for chat ID '{chat_id}'"


def checkExist(doc):
    filter = doc
    doc = pools_collection.find_one(filter)
    if doc:
        return 'F'  # Found
    else:
        return 'NF'  # Not Found


def getIgnore(chat_id):
    # Filter for documents with a matching 'chatid'
    filter = {'chatid': chat_id}
    collection_list = list(pools_collection.find(filter))
    sorted_collection = sorted(
        collection_list, key=lambda x: x["lastUpdate"], reverse=True)

    if sorted_collection:
        last_inserted_item = sorted_collection[0]

        # Get the last inserted item that matches the filter
        # Check if the last inserted item matches the filter
        if last_inserted_item.get('chatid') == chat_id and all(last_inserted_item.get(k) == v for k, v in filter.items()):
            return last_inserted_item['ignore']
        else:
            return f"No ignore found for chat ID '{chat_id}'"
    else:
        print("The collection is empty")


def updateIgnore(chat_id, flt, doc):

    # Update a value in the collection
    # filter to identify the document to update
    filter = flt
    collection_list = list(pools_collection.find(flt))
    sorted_collection = sorted(
        collection_list, key=lambda x: x["lastUpdate"], reverse=True)
    if sorted_collection:
        last_inserted_item = sorted_collection[0]

        # Get the last inserted item that matches the filter
        # Check if the last inserted item matches the filter
        if last_inserted_item.get('chatid') == chat_id and all(last_inserted_item.get(k) == v for k, v in flt.items()):
            # Update the last inserted item
            update = {'$set': doc}
            result = pools_collection.update_one(
                {'_id': last_inserted_item['_id']}, update)

            # Check if the update was successful
            if result.modified_count > 0:
                print("Value updated successfully")
            else:
                print("Value not updated")
        else:
            print("No matching item found")
    else:
        print("The collection is empty")


def updateTimestamp(doc, flt):
    update = {'$set': doc}
    result = pools_collection.update_one(
        flt, update)  # update the pools_collection with the update variable filtering by chatid

    # Check if the update was successful
    if result.modified_count > 0:
        print("Value updated successfully")
    else:
        print("Value not updated")


def cronjob(data):

    pid = data['pool_id']
    cid = data['chat_id']
    ini = json.dumps(data['lowPrice'])
    end = json.dumps(data['highPrice'])
    jobname = 'Pool: ' + pid + " - Chatid: " + json.dumps(cid)

    # Define the job data to be updated, including the extended_data field
    json_data = {
        "job": {
            "title": jobname,
            "enabled": "true",
            "saveResponses": True,
            "requestMethod": 1,
            "url": "https://python-projects-keiseto25.vercel.app/getPrice",
            "extendedData": {
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "lowPrice": ini,
                    "highPrice": end,
                    "pool_id": pid,
                    "chat_id": cid
                })
            },
            "schedule": {
                "timezone": "America/Sao_Paulo",
                "hours": [-1],
                "mdays": [-1],
                "minutes": [0, 15, 30, 45],
                "months": [-1],
                "wdays": [-1]
            }
        }
    }

    # Define the API endpoint URL
    api_url = 'https://api.cron-job.org/jobs'

    # Set the headers and data for the API request
    headers = {
        'Authorization': f'Bearer {CRON_API}',
        'Content-Type': 'application/json'
    }

    data = json.dumps(json_data)

    # Send the API request using the requests library
    response = requests.put(api_url, headers=headers, data=data)
    jobId = response.json()['jobId']

    # Check the API response status code
    if response.status_code == 200:
        print('Job created successfully!')
        sendMsg(cid, "Monitoramento ativado com sucesso!")
        # Update cronJob value
        doc = {'cronJob': jobId}
        flt = {'poolid': pid, 'chatid': cid}
        setCronjob(flt, doc)

        # Update ignore flag to true
        doc = {'ignore': 'true'}
        flt = {'chatid': cid, 'poolid': pid}
        updateIgnore(cid, flt, doc)
        print("Monitoring added succesfully.")

    else:
        print(f'Payload-->', data)
        print(f'Error updating job-->', response)
        sendMsg(cid, "Erro ao incluir monitoramento!")
    return response.status_code


def setCronjob(flt, doc):
    update = {'$set': doc}
    result = pools_collection.update_one(
        flt, update)  # update the pools_collection with the update variable filtering by chatid

    # Check if the update was successful
    if result.modified_count > 0:
        print("Cronjob updated successfully")
    else:
        print("Cronjob not updated")


def handle_input(chat_id, txt):
    range = txt.split("-")
    lowPrice = float(range[0].strip())
    highPrice = float(range[1].strip())
    pool_id = getPoolid(chat_id)
    print('lowPrice-->', lowPrice)
    print('highPrice-->', highPrice)
    print('pool_id-->', pool_id)

    cronData = {
        'lowPrice': lowPrice,
        'highPrice': highPrice,
        'pool_id': pool_id,
        'chat_id': chat_id
    }
    # Check if already have monitoring
    checkDoc = {'poolid': pool_id, 'chatid': chat_id, 'ignore': 'true'}
    if (checkExist(checkDoc) == 'NF'):
        cronjob(cronData)
        # else -> when ignore is found for chatid and poolid
    else:
        print(
            f"Pool ID" + pool_id + " is already being monitored.")
        return Response('ok', status=200)


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
