import logging
import textwrap
import time

import requests
import telebot

from environs import Env


def get_notification(tg_user_id, dvmn_token, bot):
    url = 'https://dvmn.org/api/long_polling/'
    timestamp = ''
    headers = {
        'Authorization': f'Token {dvmn_token}'
    }
    bot.send_message(tg_user_id, text=textwrap.dedent(f'''
        Вас приветствует notification_dwmn_bot.
        Как только ваша работа будет проверена я отправлю уведомление 😉
        '''))
    logging.info('bot started')

    while True:
        try:
            payload = {
                'timestamp': timestamp
            }
            response = requests.get(url, headers=headers, params=payload, timeout=100)
            response.raise_for_status()
            notification = response.json()
            if notification['status'] == 'timeout':
                timestamp = notification['timestamp_to_request']
            else:
                timestamp = notification['last_attempt_timestamp']
                lesson_title = notification['new_attempts'][0]['lesson_title']
                lesson_url = notification['new_attempts'][0]['lesson_url']
                if notification['new_attempts'][0]['is_negative']:
                    text = 'К сожалению, в работе нашлись ошибки.'
                else:
                    text = 'Преподователю все понравилось, можно приступать к следующему уроку!'
                bot.send_message(tg_user_id, text=textwrap.dedent(f'''
                                У вас проверили работу "{lesson_title}"

                                {text}

                                {lesson_url}
                                '''))
        except requests.exceptions.ReadTimeout:
            pass
        except requests.exceptions.ConnectionError:
            logging.warning('ConnectionError')
            time.sleep(30)


if __name__ == "__main__":
    env = Env()
    env.read_env()
    logging.basicConfig(format='%(levelname)s %(message)s', level=logging.DEBUG)
    tg_bot_token_key = env.str('TG_BOT_TOKEN_KEY')
    dvmn_token = env.str('DVMN_TOKEN')
    tg_user_id = env.int('TG_USER_ID')
    bot = telebot.TeleBot(token=tg_bot_token_key)

    get_notification(tg_user_id, dvmn_token, bot)

