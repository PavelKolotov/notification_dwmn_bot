import json
import telebot
import requests

from environs import Env


env = Env()
env.read_env()

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
    while True:
        try:
            payload = {
                'timestamp': timestamp
            }
            response = requests.get(url, headers=headers, params=payload, timeout=(5, 5))
            response.raise_for_status()
            timestamp = response.json()['timestamp_to_request']
            print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        except requests.exceptions.ReadTimeout:
            print('Oops. Read timeout occured')
        except requests.exceptions.ConnectionError:
            print('Oops. Connection timeout occured!')
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
def get_text(message):
    bot.delete_message(message.chat.id, message.message_id)


bot.polling(none_stop=True, interval=1)