from flask import Flask
from flask import request
from flask import Response
import requests
 
app = Flask(__name__)
 
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        msg = request.get_json()
        print(msg)
       
        return Response('ok', status=200)
    else:
        return "<h1>Welcome!</h1>"
 
 
if __name__ == '__main__':
   app.run(debug=True)