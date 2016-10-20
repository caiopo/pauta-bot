import logging

from os import environ
from telegram.ext import Updater, MessageHandler, Filters

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

TOKEN = environ['TOKEN']
APPNAME = environ['APPNAME']
PORT = int(environ.get('PORT', '5000'))
updater = Updater(TOKEN)

def echo(bot, update):
    bot.sendMessage(update.message.chat_id, text=update.message.text)

if __name__ == '__main__':
    updater.dispatcher.add_handler(MessageHandler([Filters.text], echo))

    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
    updater.bot.setWebhook("https://" + APPNAME + ".herokuapp.com/" + TOKEN)
    updater.idle()
