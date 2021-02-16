import matplotlib.pyplot as plt
import datetime as DT
import config
import telebot
import requests
from exchangeratesapi import Api
from time import time
import io

api = Api()
bot = telebot.TeleBot(config.token)

storage = {}
last_invocated = {}


# Декоратор для кэширования

def cached(ttl_s: int):
    def cached_decorator(function):

        def cached_function(*args, **kwargs):
            key = f"{function.__name__}|{str(args)}|{str(kwargs)}"

            now = int(time())
            if key not in last_invocated or last_invocated[key] + ttl_s <= now:
                if key not in last_invocated:
                    last_invocated[key] = now
                result = function(*args, **kwargs)
                storage[key] = result
            else:
                result = storage[key]
                last_invocated[key] = now

            return result

        return cached_function

    return cached_decorator


# Команда /help для боллее детальной информации о командах

@bot.message_handler(commands=['help'])
def help_list(message):
    bot.send_message(message.chat.id, f'/list - Выводит список курса валют USD \n /exchange - /exchange 10 USD to RUB (конвертация валюты из доллара в руб по '
                                      f'курсу) \n /history - /history USD/RUB (График курса за последние 7 дней)')


# Команда /list для списка курса валют USD

@bot.message_handler(commands=['list'])
def list_message(message):
    response = cached(ttl_s=600)(api.get_rates)('USD')['rates']
    text = ''
    for k, v in response.items():
        text += f'{k}: {round(v, 2)}\n'

    bot.send_message(message.chat.id, text)


# Команда /exchange (/exchange 10 USD to RUB), конвертация валюты из доллара

@bot.message_handler(commands=['exchange'], content_types=['text'])
def list_exchange(message):
    response = cached(ttl_s=600)(api.get_rates)('USD')['rates']
    user_message = message.text
    key_exchange = user_message[-3:]
    number_in_message = [int(s) for s in user_message.split() if s.isdigit()]
    i = sum(number_in_message)
    try:
        if response[key_exchange]:
            bot.send_message(message.chat.id, f'{round(response[key_exchange], 3) * i} {key_exchange}')
    except KeyError:
        pass


# Команда /history (/history USD/RUB) для показа графика курса за последние 7 дней

@bot.message_handler(commands=['history'], content_types=['text'])
def list_exchange(message):
    today = DT.date.today()
    week_ago = today - DT.timedelta(days=7)
    user_message = message.text
    key_exchange = user_message[-3:]
    url = f'https://api.exchangeratesapi.io/history?start_at={week_ago}&end_at={today}&base=USD&symbols={key_exchange}'
    try:
        res = requests.get(url).json()['rates'].values()
        coords = []
        for i in res:
            coords += i.values()
        week = coords
        plt.plot(week)
        fig = plt.figure()
        plt.plot(week)
        file = io.BytesIO()
        fig.savefig(file)
        file.seek(0)
        bot.send_photo(message.chat.id, file)

    except RuntimeError:
        pass
    except KeyError:
        pass


bot.polling()
