import matplotlib.pyplot as plt
import datetime as DT
import telebot
import requests
from time import time
import io
import os

bot = telebot.TeleBot(os.environ["TELEGRAM_TOKEN"])

storage = {}
last_invocated = {}


def cached(ttl_s: int):
    """
    Декоратор для кэширования
    """

    def cached_decorator(function):
        def cached_function(*args, **kwargs):
            key = f"{function.__name__}|{str(args)}|{str(kwargs)}"

            now = int(time())
            if key not in storage or last_invocated.get(key, 0) + ttl_s <= now:
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


@bot.message_handler(commands=["help"])
def help_list(message):
    """
    Команда /help для боллее детальной информации о командах
    """
    bot.send_message(
        message.chat.id,
        f"/list - Выводит список курса валют USD \n/exchange - /exchange 10 USD to RUB (конвертация валюты из доллара в руб по "
        f"курсу) \n/history - /history USD/RUB (График курса за последние 7 дней)",
    )


@bot.message_handler(commands=["list"])
def list_message(message):
    """
    Команда /list для списка курса валют USD
    """
    response = cached(ttl_s=600)(requests.get)("https://api.exchangeratesapi.io/latest?base=USD").json()["rates"]
    text = "\n".join(f"{currency}: {amount:.2f}" for currency, amount in response.items())
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["exchange"], content_types=["text"])
def list_exchange(message):
    """
    Команда /exchange (/exchange 10 USD to RUB), конвертация валюты из доллара
    """
    response = cached(ttl_s=600)(requests.get)("https://api.exchangeratesapi.io/latest?base=USD").json()["rates"]
    currency = message.text[-3:]
    if currency in response:
        amount = sum([int(s) for s in message.text.split() if s.isdigit()])
        bot.send_message(message.chat.id, f"{response[currency] * amount:.2f} {currency}")


@bot.message_handler(commands=["history"], content_types=["text"])
def list_exchange(message):
    """
    Команда /history (/history USD/RUB) для показа графика курса за последние 7 дней
    """
    today = DT.date.today()
    week_ago = today - DT.timedelta(days=7)
    currency = message.text[-3:]
    try:
        rates = requests.get(f"https://api.exchangeratesapi.io/history?start_at={week_ago}&end_at={today}&base=USD&symbols={currency}").json()["rates"].values()
    except KeyError:
        return
    coords = [exchange_rate for rate in rates for exchange_rate in rate.values()]
    fig = plt.figure()
    plt.plot(coords)
    fig.savefig(file := io.BytesIO())
    file.seek(0)
    bot.send_photo(message.chat.id, file)


bot.polling()
