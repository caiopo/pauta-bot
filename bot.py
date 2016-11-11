import logging
import re

from os import environ
from pymongo import MongoClient
from telegram.ext import Updater, CommandHandler
from telegram import ParseMode

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

TOKEN = environ['TOKEN']
APPNAME = environ['APPNAME']
PORT = int(environ.get('PORT', '5000'))
MONGODB_URI = environ['MONGODB_URI']
MAINTAINER_ID = environ['MAINTAINER_ID']

client = MongoClient(MONGODB_URI)

db = client.get_default_database()

HELP_STR = (
"""
Bot para gerenciar as pautas das reuniões do CALICO

/pauta - adiciona nova pauta
/ls - lista as pautas
/rm - remove todas as pautas
/data - adiciona uma data para a próxima reunião
/local - adiciona um local para a próxima reunião

Feito por @caiopo
Repositório: https://github.com/caiopo/pauta-bot
"""
)

def report_errors(func):
    def decorated(bot, update):
        try:
            func(bot, update)
        except Exception as e:
            bot.sendMessage(MAINTAINER_ID,
                text='Error on @quibebot\nUpdate: {}\nError type: {}\nError: {}'
                    .format(update, type(e), e))
    return decorated


@report_errors
def add_pauta(bot, update):
    user = update.message.from_user

    try:
        text = re.search(r'^/pauta(@pauta_bot)? (.*)$', update.message.text).group(2)
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


@report_errors
def ls_pautas(bot, update):
    cursor = db.pautas.find(
        {
            'chat_id': update.message.chat_id,
        }
    )

    if not cursor.count():
        bot.sendMessage(update.message.chat_id,
            text='Nenhuma pauta registrada')
        return

    metadata = db.meta.find_one(
        {
            'chat_id': update.message.chat_id,
        }
    )

    if metadata:
        msg = '*Reunião*\nData e Hora: {}\nLocal: {}\n\n*Pauta:*\n'.format(
            metadata['data'], metadata['local'])
    else:
        msg = '*Pauta:*\n'

    for index, pauta in enumerate(cursor):
        msg += '\u2022 {}: {} ({})\n\n'.format(
            index, pauta['text'], pauta['sender'])

    cursor.close()

    msg = msg.rstrip('\n')

    bot.sendMessage(update.message.chat_id,
        text=msg,
        parse_mode=ParseMode.MARKDOWN)


@report_errors
def rm_pautas(bot, update):
    try:
        text = re.search(r'^/rm(@pauta_bot)? (all|\d+)$', update.message.text).group(2)
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
                text='Pauta removida',
                reply_to_message_id=update.message.message_id)

        except IndexError:
            bot.sendMessage(update.message.chat_id,
                text='Pauta inexistente',
                reply_to_message_id=update.message.message_id)

        finally:
            cursor.close()


@report_errors
def data(bot, update):
    try:
        text = re.search(r'^/data(@pauta_bot)? (.*)$', update.message.text).group(2)
    except AttributeError:
        bot.sendMessage(update.message.chat_id,
            text='Esperava por "/data <texto>"')
        return

    metadata = db.meta.find_one(
        {
            'chat_id': update.message.chat_id,
        }
    )

    if not metadata:
        db.meta.insert_one(
            {
                'chat_id': update.message.chat_id,
                'data': text,
                'local': 'Não informado',
            }
        )

    else:
        metadata['data'] = text

        db.meta.replace_one(
            {
                'chat_id': update.message.chat_id,
            },
            metadata)


    bot.sendMessage(update.message.chat_id,
        text='Data adicionada',
        reply_to_message_id=update.message.message_id)


@report_errors
def local(bot, update):
    try:
        text = re.search(r'^/local(@pauta_bot)? (.*)$', update.message.text).group(2)
    except AttributeError:
        bot.sendMessage(update.message.chat_id,
            text='Esperava por "/local <texto>"')
        return

    metadata = db.meta.find_one(
        {
            'chat_id': update.message.chat_id,
        }
    )

    if not metadata:
        db.meta.insert_one(
            {
                'chat_id': update.message.chat_id,
                'local': text,
                'data': 'Não informada',
            }
        )

    else:
        metadata['local'] = text

        db.meta.replace_one(
            {
                'chat_id': update.message.chat_id,
            },
            metadata)


    bot.sendMessage(update.message.chat_id,
        text='Local adicionado',
        reply_to_message_id=update.message.message_id)


@report_errors
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

    dispatcher.add_handler(CommandHandler('data', data))
    dispatcher.add_handler(CommandHandler('local', local))

    dispatcher.add_handler(CommandHandler('start', bot_help))
    dispatcher.add_handler(CommandHandler('help', bot_help))

    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
    updater.bot.setWebhook("https://" + APPNAME + ".herokuapp.com/" + TOKEN)
    updater.idle()
