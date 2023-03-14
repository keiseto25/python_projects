import telegram
from flask import Flask, request

app = Flask(__name__)

# Define a function to handle the /id command

@app.route('/id', methods=['POST'])
def get_user_id(update, context):
    user_id = update.message.from_user.id
    print("get user id function")
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Your user ID is: " + str(user_id))


@app.route('/')
def index():
    return 'Hello, world!'


@app.route('/webhook', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    # Dispatch the update to the handlers
    dispatcher.process_update(update)
    return 'ok'


if __name__ == '__main__':
    bot_token = '6043717452:AAFkYEE7IMMuc_aYaTf9N3ZxXIcs4XLJrcQ'
    webhook_url = 'https://python-projects-khaki.vercel.app/webhook'
    bot = telegram.Bot(bot_token)
    bot.setWebhook(url=webhook_url)
    dispatcher = telegram.ext.Dispatcher(bot, None)
    dispatcher.add_handler(telegram.ext.CommandHandler('id', get_user_id))
    app.run()
