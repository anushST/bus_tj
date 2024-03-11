"""Telegram bot script."""
import logging
import requests
from logging.handlers import RotatingFileHandler
from os import getenv
from dotenv import load_dotenv
from bot_exceptions import TokenError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import (
    CallbackQueryHandler, CommandHandler, Filters, MessageHandler, Updater)

load_dotenv()

TELEGRAM_TOKEN: str = getenv('TELEGRAM_BOT_TOKEN')
LOCATION_DISTANCE_URL = 'http://127.0.0.1:8000/api/location/'
NEAR_STOP_URL = 'http://127.0.0.1:8000/api/stop/'
BUSES_LIST_URL = 'http://127.0.0.1:8000/api/bus/'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formater = logging.Formatter('%(asctime)s %(levelname)s %(message)s '
                             '(def %(funcName)s:%(lineno)d)')
handler = RotatingFileHandler('my_looger.log', maxBytes=5000000, backupCount=5)
handler.setFormatter(formater)
logger.addHandler(logger)

users: dict = {}


def check_tokens() -> None:
    """Check tokens for None."""
    if TELEGRAM_TOKEN is None:
        message: str = 'Required token is None.'
        logger.critical(message)
        raise TokenError(message)


def send_error_message(update, context):
    """Send error message."""
    chat_id = update.effective_chat.id
    context.bot.send_message(
        chat_id,
        '❗️ Произошла ошибка ❗️ пожалуйста перезапустите бот 👉 /start')


def edit_message_reply_markup(update, context, markup):
    """Edit main message markup."""
    try:
        chat_id = update.effective_chat.id
        message_id = users[f'{chat_id}']['main_message_id']
        context.bot.edit_message_reply_markup(
            chat_id, message_id,
            reply_markup=markup
        )
    except BadRequest:
        pass
    except KeyError:
        send_error_message(update, context)


def edit_message_caption(update, context, text):
    """Edit main message text."""
    try:
        chat_id = update.effective_chat.id
        message_id = users[f'{chat_id}']['main_message_id']
        context.bot.edit_message_caption(
            chat_id, message_id, caption=text
        )
    except BadRequest:
        pass
    except KeyError:
        send_error_message(update, context)


def delete_message(update, context, message_id):
    """Delete message."""
    chat_id = update.effective_chat.id
    try:
        context.bot.delete_message(chat_id, message_id)
    except BadRequest:
        pass


def start(update, context) -> None:
    """Register user and send stop decision."""
    try:
        chat_id = update.effective_chat.id
        users[f'{chat_id}'] = {'message_sent': False}
        send_stop_decisions(update, context)
    except Exception:
        pass


def send_stop_decisions(update, context) -> None:
    """Send decision: 4 near stops or input stop id."""
    try:
        chat_id = update.effective_chat.id
        users[f'{chat_id}']['action'] = 'choose_way'
        keyboard = [[InlineKeyboardButton(
            'Найти ближайшие', callback_data='send_near_stations')]]
        markup = InlineKeyboardMarkup(keyboard)
        if not users[f'{chat_id}']['message_sent']:
            with open('bot/_7f60c46f-a38b-4eb3-8ad6'
                      '-7175790b244d.jpeg', 'rb') as photo:
                message = context.bot.send_photo(
                    chat_id,
                    photo,
                    caption='Напишите id остановки',
                    reply_markup=markup,
                    parse_mode='HTML')
            users[f'{chat_id}']['main_message_id'] = message.message_id
            users[f'{chat_id}']['message_sent'] = True
            delete_message(update, context, message.message_id-1)
        else:
            edit_message_caption(update, context, 'Напишите id остановки')
            edit_message_reply_markup(update, context, markup)
    except Exception:
        pass


def send_near_stations(update, context):
    """Send near stations choose-buttons."""
    chat_id = update.effective_chat.id
    users[f'{chat_id}']['action'] = 'choose_stop'
    keyboard = [[]]
    params = {'latitude': 38.573739, 'longitude': 68.78696}
    data = requests.get(NEAR_STOP_URL, params=params).json()
    for stop in data['stops']:
        keyboard.append([InlineKeyboardButton(
            f'{stop[0]} - Исмоили сомони', callback_data=f'stop {stop[1]}'
        )])
    keyboard.append([InlineKeyboardButton(
        '◀️ Назад', callback_data='back')])
    markup = InlineKeyboardMarkup(keyboard)
    edit_message_caption(update, context, 'Ближайшие остановки:')
    edit_message_reply_markup(update, context, markup)


def send_buses(update, context):
    """Send buses choose_buttons which pass the selected station."""
    chat_id = update.effective_chat.id
    users[f'{chat_id}']['action'] = 'choose_buses'
    keyboard = [[]]
    params = {'stop': users[f'{chat_id}']['stop']}
    data = requests.get(BUSES_LIST_URL, params=params).json()
    for bus in data['buses']:
        keyboard[0].append(InlineKeyboardButton(
            f'{bus[0]}', callback_data=f'bus {bus[1]}'
        ))
    keyboard.append([InlineKeyboardButton(
        '◀️ Назад', callback_data='back')])
    markup = InlineKeyboardMarkup(keyboard)
    edit_message_caption(update, context, 'Выберите нужный вам автобус')
    edit_message_reply_markup(update, context, markup)


def stop_by_input(update, context):
    """Choose station by inputing id."""
    chat_id = update.effective_chat.id
    if users[f'{chat_id}']['action'] == 'choose_way':
        try:
            id = int(update.message.text)
            users[f'{chat_id}']['stop'] = id
        except ValueError:
            pass
    delete_message(update, context, update.message.message_id)
    send_buses(update, context)


def send_bus_data(update, context):
    """Send bus data."""
    chat_id = update.effective_chat.id
    users[f'{chat_id}']['action'] = 'get_location'
    keyboard = [
        [InlineKeyboardButton('Обновить', callback_data='update')],
        [InlineKeyboardButton('Заново', callback_data='again')],
        [InlineKeyboardButton('◀️ Назад', callback_data='back')]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    bus_id = users[f'{chat_id}']['bus']
    stop_id = users[f'{chat_id}']['stop']
    params = {
        'bus': users[f'{chat_id}']['bus'],
        'stop': users[f'{chat_id}']['stop']}
    data = requests.get(LOCATION_DISTANCE_URL, params=params).json()
    distance = data['distance']
    message = ('Остановка(id): (name)\nАвтобус:'
               f'(name)\nРастояние: {distance}м'
               '\nВремя прибытия: 2мин')
    edit_message_caption(update, context, message)
    edit_message_reply_markup(update, context, markup)


def back(update, context):
    """Go back to the previous action."""
    chat_id = update.effective_chat.id
    action = users[f'{chat_id}']['action']
    if action == 'get_location':
        send_buses(update, context)
    elif action == 'choose_buses':
        send_near_stations(update, context)
    elif action == 'choose_stop':
        send_stop_decisions(update, context)


def undefined_button_click(update, context):
    """Determine button's action and execute."""
    chat_id = update.effective_chat.id
    data: str = update.callback_query.data.split()
    if data[0] == 'stop':
        users[f'{chat_id}']['stop'] = int(data[1])
        send_buses(update, context)
    elif data[0] == 'bus':
        users[f'{chat_id}']['bus'] = int(data[1])
        send_bus_data(update, context)
    elif data[0] == 'update':
        send_bus_data(update, context)
    elif data[0] == 'again':
        users[f'{chat_id}']['stop'] = None
        users[f'{chat_id}']['bus'] = None
        send_stop_decisions(update, context)


def main():
    """Call to start the bot."""
    updater: Updater = Updater(token=TELEGRAM_TOKEN)
    try:
        updater.dispatcher.add_handler(
            CommandHandler('start', start))
        updater.dispatcher.add_handler(
            CallbackQueryHandler(send_near_stations,
                                 pattern='send_near_stations'))
        updater.dispatcher.add_handler(
            CallbackQueryHandler(back, pattern='back'))
        updater.dispatcher.add_handler(
            CallbackQueryHandler(undefined_button_click))
        updater.dispatcher.add_handler(
            MessageHandler(Filters.text, stop_by_input))
    except Exception:
        logger.exception('Неизвестная ошибка.')
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
