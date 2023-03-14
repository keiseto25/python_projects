from flask import Flask
from flask import request
from flask import Response
import requests
 
app = Flask(__name__)
TOKEN= '6043717452:AAFkYEE7IMMuc_aYaTf9N3ZxXIcs4XLJrcQ'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        msg = request.get_json()
       
        chat_id,txt = parse_message(msg) # retrieve chat_id and txt from msg
        if txt == "/id":
            sendMsg(chat_id,"Your user id: " + str(chat_id))        
       
        return Response('ok', status=200)
    else:
        return "<h1>Welcome!</h1>"

def sendMsg(chat_id, text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {
                'chat_id': chat_id,
                'text': text
                }
   
    r = requests.post(url,json=payload)
    return r    

def parse_message(message):
    print("message-->",message)
    chat_id = message['message']['chat']['id']
    txt = message['message']['text']
    print("chat_id-->", chat_id)
    print("txt-->", txt)
    return chat_id,txt
 
 
if __name__ == '__main__':
   app.run(debug=True)