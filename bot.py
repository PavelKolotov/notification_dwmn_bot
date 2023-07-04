import logging
import textwrap
import time

import requests
import telebot

from environs import Env
from telegram_handler import TelegramLoggingHandler


def configure_logging(tg_bot_token_key, tg_user_id):
    telegram_log_handler = TelegramLoggingHandler(tg_bot_token_key, tg_user_id)
    logging.basicConfig(
        handlers=[telegram_log_handler],
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.info('bot started')
    return logger


def send_notification(bot, tg_user_id, lesson_title, lesson_url, is_negative):
    if is_negative:
        text = 'К сожалению, в работе нашлись ошибки.'
    else:
        text = 'Преподавателю все понравилось, можно приступать к следующему уроку!'
    message = textwrap.dedent(f'''
        У вас проверили работу "{lesson_title}"

        {text}

        {lesson_url}
    ''')
    bot.send_message(tg_user_id, text=message)


def get_notification(tg_user_id, dvmn_token, bot, tg_bot_token_key):
    url = 'https://dvmn.org/api/long_polling/'
    timestamp = ''
    headers = {
        'Authorization': f'Token {dvmn_token}'
    }
    logger = configure_logging(tg_bot_token_key, tg_user_id)

    while True:
        try:
            payload = {'timestamp': timestamp}
            response = requests.get(url, headers=headers, params=payload, timeout=100)
            response.raise_for_status()
            notification = response.json()
            if notification['status'] == 'timeout':
                timestamp = notification['timestamp_to_request']
            else:
                timestamp = notification['last_attempt_timestamp']
                new_attempt = notification['new_attempts'][0]
                send_notification(bot, tg_user_id, new_attempt['lesson_title'], new_attempt['lesson_url'], new_attempt['is_negative'])
        except requests.exceptions.ReadTimeout:
            pass
        except requests.exceptions.ConnectionError:
            logger.error('ConnectionError')
            time.sleep(30)


def main():
    env = Env()
    env.read_env()
    tg_bot_token_key = env.str('TG_BOT_TOKEN_KEY')
    dvmn_token = env.str('DVMN_TOKEN')
    tg_user_id = env.int('TG_USER_ID')
    bot = telebot.TeleBot(token=tg_bot_token_key)

    get_notification(tg_user_id, dvmn_token, bot, tg_bot_token_key)


if __name__ == "__main__":
    main()
