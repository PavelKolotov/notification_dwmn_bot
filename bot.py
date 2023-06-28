import logging

import requests
import telebot

from environs import Env


env = Env()
env.read_env()

tg_bot_token_key = env.str('TG_BOT_TOKEN_KEY')
dvmn_token = env.str('DVMN_TOKEN')
bot = telebot.TeleBot(token=tg_bot_token_key)

logging.basicConfig(filename="sample.log", level=logging.INFO)
log = logging.getLogger("ex")


@bot.message_handler(commands=['start'])
def get_notification(message):
    url = 'https://dvmn.org/api/long_polling/'
    timestamp = ''
    headers = {
        'Authorization': f'Token {dvmn_token}'
    }
    bot.send_message(message.chat.id, f'Здравствуйте, {message.from_user.first_name}\n\n'
                                      f'Вас приветствует notification_dwmn_bot. '
                                      f'Как только ваша работа будет проверена я отправлю уведомление 😉')
    while True:
        try:
            payload = {
                'timestamp': timestamp
            }
            response = requests.get(url, headers=headers, params=payload, timeout=(5, 5))
            response.raise_for_status()
            timestamp = response.json()['timestamp_to_request']
        except requests.exceptions.ReadTimeout:
            log.info('Oops. Read timeout occured')
        except requests.exceptions.ConnectionError:
            log.info('Oops. Connection timeout occured!')
        except KeyError:
            lesson_title = response.json()['new_attempts'][0]['lesson_title']
            lesson_url = response.json()['new_attempts'][0]['lesson_url']
            if response.json()['new_attempts'][0]['is_negative']:
                text = 'К сожалению, в работе нашлись ошибки.'
            else:
                text = 'Преподователю все понравилось, можно приступать к следующему уроку!'
            timestamp = response.json()['last_attempt_timestamp']
            bot.send_message(message.chat.id, f'У вас проверили работу \"{lesson_title}\"\n\n'
                                              f'{text}\n\n'
                                              f'{lesson_url}')


@bot.message_handler()
def delete_text(message):
    bot.delete_message(message.chat.id, message.message_id)


if __name__ == "__main__":
    bot.polling(none_stop=True, interval=1)