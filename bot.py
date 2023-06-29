import logging
import textwrap

import requests
import telebot

from environs import Env


env = Env()
env.read_env()

log = logging.getLogger("ex")

tg_bot_token_key = env.str('TG_BOT_TOKEN_KEY')
dvmn_token = env.str('DVMN_TOKEN')
bot = telebot.TeleBot(token=tg_bot_token_key)



@bot.message_handler(commands=['start'])
def get_notification(message):
    url = 'https://dvmn.org/api/long_polling/'
    timestamp = ''
    headers = {
        'Authorization': f'Token {dvmn_token}'
    }

    bot.send_message(message.chat.id, text=textwrap.dedent(f'''
        Здравствуйте, {message.from_user.first_name}
        Вас приветствует notification_dwmn_bot.
        Как только ваша работа будет проверена я отправлю уведомление 😉
        '''))
    while True:
        try:
            payload = {
                'timestamp': timestamp
            }
            response = requests.get(url, headers=headers, params=payload, timeout=(5, 240))
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
                bot.send_message(message.chat.id, text=textwrap.dedent(f'''
                                У вас проверили работу "{lesson_title}"

                                {text}

                                {lesson_url}
                                '''))

        except requests.exceptions.ReadTimeout:
            log.info('Oops. Read timeout occured')
        except requests.exceptions.ConnectionError:
            log.info('Oops. Connection timeout occured!')


@bot.message_handler()
def delete_text(message):
    bot.delete_message(message.chat.id, message.message_id)


if __name__ == "__main__":
    logging.basicConfig(filename="sample.log", level=logging.INFO)
    bot.infinity_polling()
