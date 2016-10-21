import logging

from pymongo import MongoClient
from os import environ
from telegram.ext import Updater, MessageHandler, Filters
from pprint import pprint

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

TOKEN = environ['TOKEN']
APPNAME = environ['APPNAME']
PORT = int(environ.get('PORT', '5000'))
MONGODB_URI = environ['MONGODB_URI']
MONGODB_NAME = environ['MONGODB_NAME']
updater = Updater(TOKEN)

client = MongoClient(MONGODB_URI)

db = client.get_default_database()

def echo(bot, update):
    result = db.pautas.insert_one(
        {
            'sender': update.message.from_user.username,
            'text': update.message.text,
        }
    )

    bot.sendMessage(update.message.chat_id,
        text='ack: {}, id: {}'.format(result.acknowledged, result.inserted_id))

if __name__ == '__main__':
    updater.dispatcher.add_handler(MessageHandler([Filters.text], echo))

    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
    updater.bot.setWebhook("https://" + APPNAME + ".herokuapp.com/" + TOKEN)
    updater.idle()
