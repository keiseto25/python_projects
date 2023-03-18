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

TOKEN = os.environ['BOT_TOKEN']
MONGODB_URI = os.environ['MONGODB_URI']
DB_NAME = os.environ['DB_NAME']
CRON_API = '1uKTRpu7D5c0P6mEAJF4sPCxqSUGiiyfXdPpuK+EpR0='

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
pools_collection = db['pools']


def checkExist(doc):
    filter = doc
    doc = pools_collection.find_one(filter)
    if doc:
        return 'F'  # Found
    else:
        return 'NF'  # Not Found


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


def sendMsg(chat_id, text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }

    r = requests.post(url, json=payload)
    return r
