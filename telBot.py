import telegram
from telegram.ext import Updater, CommandHandler

# Define a function to get the user ID
def get_user_id(update, context):
    user_id = update.message.from_user.id
    context.bot.send_message(chat_id=update.effective_chat.id, text="Your user ID is: " + str(user_id))

# Create an Updater object with your bot token
updater = Updater('6043717452:AAFkYEE7IMMuc_aYaTf9N3ZxXIcs4XLJrcQ', use_context=True)

# Get the Dispatcher object from the Updater object
dp = updater.dispatcher

# Define the /id command handler
dp.add_handler(CommandHandler('id', get_user_id))

# Start polling for updates
updater.start_polling()

# Run the bot until the user presses Ctrl-C
updater.idle()
