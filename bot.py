
import logging
import re

from os import environ
from pymongo import MongoClient
from telegram.ext import Updater, CommandHandler
from telegram import ParseMode

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

TOKEN = environ['TOKEN']
APPNAME = environ['APPNAME']
PORT = int(environ.get('PORT', '5000'))
MONGODB_URI = environ['MONGODB_URI']

client = MongoClient(MONGODB_URI)

db = client.get_default_database()

HELP_STR = (
"""
Bot para gerenciar as pautas das reuniões do CALICO

/pauta - adiciona nova pauta
/ls - lista as pautas
/rm - remove todas as pautas

Feito por @caiopo
Repositório: https://github.com/caiopo/pauta-bot
"""
)

def add_pauta(bot, update):
    user = update.message.from_user

    try:
        re.search(r'^/pauta (.*)$', update.message.text).group(1)
    except AttributeError:
        bot.sendMessage(update.message.chat_id,
            text='Esperava por "/pauta <texto>"')
        return

    result = db.pautas.insert_one(
        {
            'sender': user.name,
            'text': text,
            'chat_id': update.message.chat_id,
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


def ls_pautas(bot, update):
    cursor = db.pautas.find(
        {
            'chat_id': update.message.chat_id,
        }
    )

    msg = '*Pauta:*\n'

    for index, pauta in enumerate(cursor):
        msg += '\u2022 {}: {} ({})\n\n'.format(
            index, pauta['text'], pauta['sender'])

    cursor.close()

    msg = msg.rstrip('\n')

    bot.sendMessage(update.message.chat_id,
        text=msg,
        parse_mode=ParseMode.MARKDOWN)


def rm_pautas(bot, update):
    try:
        text = re.search(r'^/rm (all|\d+)$', update.message.text).group(1)
    except AttributeError:
        bot.sendMessage(update.message.chat_id,
            text='Esperava por "^/rm (all|\d+)$"')
        return

    if text == 'all':
        result = db.pautas.delete_many(
            {
                'chat_id': update.message.chat_id,
            }
        )

        bot.sendMessage(update.message.chat_id,
            text='{} pautas removida(s)'.format(result.deleted_count))

    else:
        index = int(text)

        cursor = db.pautas.find(
            {
                'chat_id': update.message.chat_id,
            }
        )

        try:
            db.pautas.delete_one(cursor[index])

            bot.sendMessage(update.message.chat_id,
                text='Pauta removida')

        except IndexError:
            bot.sendMessage(update.message.chat_id,
                text='Pauta inexistente')

        finally:
            cursor.close()

def bot_help(bot, update):
    bot.sendMessage(update.message.chat_id,
        text=HELP_STR,
        disable_web_page_preview=True)

if __name__ == '__main__':
    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('pauta', add_pauta))
    dispatcher.add_handler(CommandHandler('ls', ls_pautas))
    dispatcher.add_handler(CommandHandler('rm', rm_pautas))
    dispatcher.add_handler(CommandHandler('start', bot_help))
    dispatcher.add_handler(CommandHandler('help', bot_help))

    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
    updater.bot.setWebhook("https://" + APPNAME + ".herokuapp.com/" + TOKEN)
    updater.idle()
