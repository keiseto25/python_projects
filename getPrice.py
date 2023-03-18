from flask import Flask, Response
from flask import request
from utils import checkExist, updateIgnore, sendMsg
import requests
import datetime
import json
import pytz

app = Flask(__name__)


@app.errorhandler(400)
def handle_bad_request(e):
    app.logger.error('Bad request: %s', request)
    return 'Bad request', 400


@app.route('/getPrice', methods=['POST'])
def getPrice():
    data = request
    msg = data.get_json()
    pool_id = msg['pool_id']
    chat_id = msg['chat_id']
    lowPrice = float(msg['lowPrice'])
    highPrice = float(msg['highPrice'])

    # Check if already have monitoring
    checkDoc = {'poolid': pool_id, 'chatid': chat_id, 'ignore': 'true'}
    if (checkExist(checkDoc) == 'NF'):  # Check if exist before inserting
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

        # handling for 0
        if (lowPrice == 0.0 or highPrice == 0.0):
            txt = 'Favor informar valor maior que zero!'
            print(txt)
            sendMsg(chat_id, txt)
            return
        else:
            pVariationlow = ((float(lowPrice) - tPrice) /
                             float(lowPrice)) * 100
            pVariationhigh = ((tPrice - float(highPrice)) /
                              float(highPrice)) * 100

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
            txt = '✅➡️<b>[' + timestamp + ']</b> : ' + t0Symbol + '/' + t1Symbol + ' dentro intervalo de ' + \
                str(lowPrice) + ' a ' + str(highPrice) + \
                ': \n\n 👉 ' + str(tPrice)
            sendMsg(chat_id, txt)
            print(txt)

        doc = {'ignore': 'true'}
        flt = {'chatid': chat_id, 'poolid': pool_id}
        updateIgnore(chat_id, flt, doc)
        print("Monitoring added succesfully.")
        return Response('ok', status=200)

    # else -> when ignore is found for chatid and poolid
    else:
        print(
            f"Pool ID" + pool_id + " is already being monitored.")
        return Response('ok', status=200)


if __name__ == '__main__':
    app.run()
