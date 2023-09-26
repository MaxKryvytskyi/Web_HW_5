import argparse
import asyncio
import sys
import logging
import re
from datetime import datetime
from decimal import Decimal
import platform

import aiohttp
from rich.console import Console
from rich.table import Table

console = Console()

sys.stdout.reconfigure(encoding='utf-8')
list_data = {
"AUD": "Австралийский Доллар",
"AZN": "Азербайджанский Ман",
"BYN": "Білоруський Рубль",
"CAD": "Канадський Доллар",
"CHF": "Швейцарський Франк",
"CNY": "Юань Женьміньбі",
"CZK": "Чеська Крона",
"DKK": "Данська Крона",
"EUR": "Євро",
"GBP": "Фунт Стерлінгів",
"GEL": "Грузинський Ларі",
"HUF": "Угорський Форинт",
"ILS": "Новий Ізраїльський Шекель",
"JPY": "Японська Єна",
"KZT": "Казахстанський Теньге",
"MDL": "Молдовський Лей",
"NOK": "Норвезька крона",
"PLN": "Злотий",
"SEK": "Шведська Крона",
"SGD": "Сінгапурський Долар",
"TMT": "Туркменський Манат",
"TRY": "Турецька Ліра",
"UAH": "Українська Гривня",
"USD": "Долар США",
"UZS": "Узбецький Сум",
"XAU": "Золото"
}

parser = argparse.ArgumentParser(description='Приклад програми з аргументами.')

parser.add_argument('-d', '--date', required=True, help='Дата у форматі DD.MM.YYYY')
parser.add_argument('-c', '--currencies', nargs='+', required=False, help='Валюти')
parser.add_argument('-m', '--money', type=float, required=False, help='Сума грошей в валюті')

args = parser.parse_args()
date = args.date
currencies = args.currencies
money = args.money

now = datetime.now()
ulr = "https://api.privatbank.ua/p24api/exchange_rates?json&date="

def date_check():
    global date
    date = datetime.strptime(date, "%d.%m.%Y")
    time = now.replace(day=now.day - 10)
    if time <= date <= now:
        date = date.date().strftime("%d.%m.%Y")
        return f"{ulr}{date}"
    elif date > now:
        date = now.date().strftime("%d.%m.%Y")
        return f"{ulr}{date}"
    else: 
        date = time.date().strftime("%d.%m.%Y")
        return f"{ulr}{date}"

def data_output(datas):
    
    table = Table(title=f"Курс валют станом за {date}")
    table.add_column("Літерний код", justify="center", style="color(5)", no_wrap=False)
    table.add_column("Назва валюти", justify="center", style="rgb(255,136,0)", no_wrap=False)
    table.add_column("Курс продажу НБУ", justify="center", style="Yellow", no_wrap=False)
    table.add_column("Курс продажу ПБ", justify="center", style="green", no_wrap=False)
    table.add_column("Курс купівлі ПБ", justify="center", style="red", no_wrap=False)
    if money:
        table.add_column(f"{money} Валюти по курсу НБУ в UAH", justify="center", style="color(12)", no_wrap=True)

    for data in datas["exchangeRate"]:
        cache = []
        if currencies:
            for currency in currencies:
                if currency.upper() == data['currency']:
                    
                    cache.append(data['currency'])
                    cache.append(list_data[data['currency']])
                    cache.append(f"{data['saleRateNB']} {data['purchaseRateNB']}")

                    try:
                        cache.append(str(data["saleRate"]))
                        cache.append(str(data["purchaseRate"]))
                    except KeyError:
                        cache.append("")
                        cache.append("")

                    if money:
                        cache.append(f"{round(Decimal(money) * Decimal(data['saleRateNB']), 2)}")
        else:
            cache.append(data['currency'])
            cache.append(list_data[data['currency']])
            cache.append(f"{round(Decimal(money) * Decimal(data['saleRateNB']), 2)}")

            try:
                cache.append(str(data["saleRate"]))
                cache.append(str(data["purchaseRate"]))
            except KeyError:
                cache.append("")
                cache.append("")

            if money:
                cache.append(f"{round(money * data['saleRateNB'], 2)}")
        if cache:
            table.add_row(*cache)
    
    console.print(table)

async def main():
    async with aiohttp.ClientSession() as session:
        logging.info(f"Starting: {ulr}")
        try:
            async with session.get(ulr) as response:
                if response.status == 200:
                    data = await response.json()
                    data_output(data)
                else:
                    logging.error(f'Error status {response.status} for {ulr}')
        except aiohttp.ClientConnectorError as e:
            logging.error(f'Connection error {ulr}: {e}')

if __name__ == '__main__':
    ulr = date_check()

    logging.basicConfig(level=logging.INFO, handlers=[
    logging.FileHandler("sort_log.txt"),
    logging.StreamHandler()], format="%(asctime)s %(message)s")

    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
