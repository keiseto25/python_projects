import telegram
from flask import Flask, request

# Create a Flask app instance
app = Flask(__name__)

# Define a function to handle the /id command
@app.route('/id', methods=['POST'])
def get_user_id():
    # Get the user ID from the request
    user_id = request.json['message']['from']['id']
    # Send a message back to the user with their ID
    bot = telegram.Bot('6043717452:AAFkYEE7IMMuc_aYaTf9N3ZxXIcs4XLJrcQ')
    webhook_url='https://python-projects-keiseto25.vercel.app//id'
    bot.setWebhook(url=webhook_url)
    bot.send_message(chat_id=request.json['message']['chat']['id'], text="Your user ID is: " + str(user_id))
    return ''

if __name__ == '__main__':    
    app.run()

