"""Telegram bot script."""
import logging
from logging.handlers import RotatingFileHandler
from os import getenv

import requests
from bot_exceptions import TokenError
from dotenv import load_dotenv
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup)
from telegram.error import BadRequest
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)

load_dotenv()

TELEGRAM_TOKEN: str = getenv('TELEGRAM_BOT_TOKEN')
LOCATION_DISTANCE_URL: str = 'http://bustj.pythonanywhere.com/api/location/'
STOP_URL: str = 'http://bustj.pythonanywhere.com/api/stop/'
BUSES_URL: str = 'http://bustj.pythonanywhere.com/api/bus/'

logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formater: logging.Formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(message)s (def %(funcName)s:%(lineno)d)')
handler: RotatingFileHandler = RotatingFileHandler(
    'my_looger.log', maxBytes=5000000, backupCount=5)
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
        users[f'{chat_id}'] = {}
        send_stop_decisions(update, context)
        delete_message(update, context, update.message.message_id)
    except Exception:
        pass


def send_stop_decisions(update, context) -> None:
    """Send decision: 4 near stops or input stop id."""
    chat_id = update.effective_chat.id
    users[f'{chat_id}']['action'] = 'choose_way'
    """
    keyboard = [[InlineKeyboardButton(
        'Найти ближайшие', callback_data='choose'
    )]]
    markup = InlineKeyboardMarkup(keyboard)
    """
    keyboard = [[KeyboardButton(
        'Найти ближайшие', request_location=True)]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True,
                                 one_time_keyboard=True)

    with open('bot/logo.jpeg', 'rb') as photo:
        message = context.bot.send_photo(
            chat_id,
            photo,
            caption='Напишите id остановки',
            reply_markup=markup,
            parse_mode='HTML')
        try:
            delete_message(
                update, context, users[f'{chat_id}']['main_message_id'])
        except KeyError:
            pass
        users[f'{chat_id}']['main_message_id'] = message.message_id


def station_by_location(update, context):
    """Delete location message."""
    delete_message(update, context, update.message.message_id)
    send_near_stations(update, context)


def send_near_stations(update, context):
    """Send near stations choose-buttons."""
    chat_id = update.effective_chat.id
    users[f'{chat_id}']['action'] = 'choose_stop'
    users[f'{chat_id}']['way'] = 'near'
    keyboard = [[]]
    try:
        location = update.message.location
        users[f'{chat_id}']['latitude'] = location.latitude
        users[f'{chat_id}']['longitude'] = location.longitude
        params = {'latitude': location.latitude,
                  'longitude': location.longitude}
        data = requests.get(STOP_URL, params=params).json()
    except AttributeError:
        params = {'latitude': users[f'{chat_id}']['latitude'],
                  'longitude': users[f'{chat_id}']['longitude']}
        data = requests.get(STOP_URL, params=params).json()
    for stop in data['stops']:
        keyboard.append([InlineKeyboardButton(
            f'{stop[1]} - {stop[0]}', callback_data=f'stop {stop[1]}'
        )])
    keyboard.append([InlineKeyboardButton(
        '◀️ Назад', callback_data='back')])
    markup = InlineKeyboardMarkup(keyboard)
    with open('bot/logo.jpeg', 'rb') as photo:
        message = context.bot.send_photo(
            chat_id,
            photo,
            caption='Напишите id остановки',
            reply_markup=markup,
            parse_mode='HTML')
        delete_message(update, context, users[f'{chat_id}']['main_message_id'])
        users[f'{chat_id}']['main_message_id'] = message.message_id


def send_buses(update, context):
    """Send buses choose_buttons which pass the selected station."""
    chat_id = update.effective_chat.id
    users[f'{chat_id}']['action'] = 'choose_buses'
    keyboard = [[]]
    params = {'stop': users[f'{chat_id}']['stop']}
    data = requests.get(BUSES_URL, params=params).json()
    for bus in data['buses']:
        keyboard[0].append(InlineKeyboardButton(
            f'{bus[0]}', callback_data=f'bus {bus[1]}'
        ))
    keyboard.append([InlineKeyboardButton(
        '◀️ Назад', callback_data='back')])
    markup = InlineKeyboardMarkup(keyboard)
    if users[f'{chat_id}'].get('is_input', False):
        with open('bot/logo.jpeg', 'rb') as photo:
            message = context.bot.send_photo(
                chat_id,
                photo,
                caption='Выберите нужный вам автобус',
                reply_markup=markup,
                parse_mode='HTML')
        delete_message(update, context, users[f'{chat_id}']['main_message_id'])
        users[f'{chat_id}']['main_message_id'] = message.message_id
        users[f'{chat_id}']['is_input'] = False
    else:
        edit_message_caption(update, context, 'Выберите нужный вам автобус')
        edit_message_reply_markup(update, context, markup)


def stop_input(update, context):
    """Choose station by inputing id."""
    chat_id = update.effective_chat.id
    message = update.message.text
    if users[f'{chat_id}']['action'] == 'choose_way':
        try:
            id = int(message)
            users[f'{chat_id}']['stop'] = id
        except ValueError:
            pass
    delete_message(update, context, update.message.message_id)
    users[f'{chat_id}']['is_input'] = True
    users[f'{chat_id}']['way'] = 'input'
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
        'bus': bus_id,
        'stop': stop_id}
    data = requests.get(LOCATION_DISTANCE_URL, params=params).json()
    bus = requests.get(BUSES_URL + f'{bus_id}/').json()
    stop = requests.get(STOP_URL + f'{stop_id}/').json()
    distance = data['distance']
    message = (f'Остановка ({stop["id"]}): {stop["name"]}\nАвтобус:'
               f' {bus["name"]}\nРастояние: {distance}м'
               f'\nВремя прибытия: {round(distance/400)}мин')
    edit_message_caption(update, context, message)
    edit_message_reply_markup(update, context, markup)


def back(update, context):
    """Go back to the previous action."""
    chat_id = update.effective_chat.id
    action = users[f'{chat_id}']['action']
    if action == 'get_location':
        send_buses(update, context)
    elif action == 'choose_buses' and users[f'{chat_id}']['way'] == 'input':
        send_stop_decisions(update, context)
    elif action == 'choose_buses' and users[f'{chat_id}']['way'] == 'near':
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
            CallbackQueryHandler(back, pattern='back'))
        updater.dispatcher.add_handler(
            CallbackQueryHandler(send_near_stations, pattern='choose')
        )
        updater.dispatcher.add_handler(
            CallbackQueryHandler(undefined_button_click))
        updater.dispatcher.add_handler(
            MessageHandler(Filters.location, station_by_location))
        updater.dispatcher.add_handler(
            MessageHandler(Filters.text, stop_input))
    except Exception:
        logger.exception('Неизвестная ошибка.')
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
