import logging

from os import environ
from pymongo import MongoClient
from telegram.ext import Updater, CommandHandler
from telegram import ParseMode

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

TOKEN = environ['TOKEN']
APPNAME = environ['APPNAME']
PORT = int(environ.get('PORT', '5000'))
MONGODB_URI = environ['MONGODB_URI']
CHAT_ID = environ['CHAT_ID']

client = MongoClient(MONGODB_URI)

db = client.get_default_database()

def only_in_chat(func):
    def decorated(bot, update):
        if str(update.message.chat_id) == CHAT_ID:
            func(bot, update)
        else:
            bot.sendMessage(update.message.chat_id,
                text='Comando não disponível')

    return decorated


@only_in_chat
def add_pauta(bot, update):
    user = update.message.from_user
    text = ' '.join(update.message.text.split()[1:])

    if not text:
        bot.sendMessage(update.message.chat_id,
            text='Esperava por "/pauta <texto>"')
        return

    result = db.pautas.insert_one(
        {
            'sender': user.name,
            'text': text,
        }
    )

    if result.acknowledged:
        bot.sendMessage(update.message.chat_id,
            text='Pauta registrada',
            reply_to_message_id=update.message.message_id)
    else:
        bot.sendMessage(update.message.chat_id,
            text='Pauta não registrada, algo de errado aconteceu',
            reply_to_message_id=update.message.message_id)


@only_in_chat
def ls_pautas(bot, update):
    if not db.pautas.count():
        bot.sendMessage(update.message.chat_id,
            text='Nenhuma pauta registrada')
        return

    cursor = db.pautas.find()

    msg = '*Pauta:*\n'

    for pauta in cursor:
        msg += '\u2022 {} ({})\n\n'.format(pauta['text'], pauta['sender'])

    cursor.close()

    msg = msg.rstrip('\n')

    bot.sendMessage(update.message.chat_id,
        text=msg,
        parse_mode=ParseMode.MARKDOWN)


@only_in_chat
def rm_pautas(bot, update):
    result = db.pautas.delete_many({})

    bot.sendMessage(update.message.chat_id,
        text='{} pautas removida(s)'.format(result.deleted_count))


if __name__ == '__main__':
    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('pauta', add_pauta))
    dispatcher.add_handler(CommandHandler('ls', ls_pautas))
    dispatcher.add_handler(CommandHandler('rm', rm_pautas))

    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
    updater.bot.setWebhook("https://" + APPNAME + ".herokuapp.com/" + TOKEN)
    updater.idle()
