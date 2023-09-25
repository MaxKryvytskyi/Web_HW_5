import asyncio
import logging
import aiohttp
import platform
from rich.console import Console
from rich.table import Table
from datetime import datetime
import sys
import argparse

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

# Створіть парсер командного рядка
parser = argparse.ArgumentParser(description='Приклад програми з аргументами.')

# Додайте аргументи
parser.add_argument('-d', '--date', required=True, help='Дата у форматі DD.MM.YYYY')
parser.add_argument('-c', '--currencies', nargs='+', required=False, help='Валюти')
parser.add_argument('-m', '--money', type=float, required=False, help='Сума грошей в валюті')

# Розіберіть командний рядок
args = parser.parse_args()

# Отримайте значення аргументів
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
        date =now.date().strftime("%d.%m.%Y")
        return f"{ulr}{date}"
    else: 
        date = time.date().strftime("%d.%m.%Y")
        return f"{ulr}{date}"

def data_output(data):
    table = Table(title=f"Курс валют станом за {date}")
    table.add_column("Літерний код", justify="center", style="cyan", no_wrap=False)
    table.add_column("Назва валюти", justify="center", style="cyan", no_wrap=False)
    table.add_column("Курс продажу НБУ", justify="center", style="cyan", no_wrap=False)
    table.add_column("Курс продажу ПБ", justify="center", style="cyan", no_wrap=False)
    table.add_column("Курс купівлі ПБ", justify="center", style="cyan", no_wrap=False)
    if money:
        table.add_column(f"{money} Валюти по курсу НБУ в UAH", justify="center", style="cyan", no_wrap=True)

    for i in data:
        if i == "exchangeRate":
            for t in data["exchangeRate"]:
                if currencies:
                    for currency in currencies:
                        if currency.upper() == t['currency']:
                            try:
                                table.add_row(t['currency'], list_data[t['currency']], f"{t['saleRateNB']} {t['purchaseRateNB']}", str(t["saleRate"]), str(t["purchaseRate"]), f"{round(money * t['saleRateNB'], 2)}" if money else "")
                            except KeyError:
                                table.add_row(t['currency'], list_data[t['currency']], f"{t['saleRateNB']} {t['purchaseRateNB']}", "", "", f"{round(money * t['saleRateNB'], 2)}" if money else "")
                else:
                    try:
                        table.add_row(t['currency'], list_data[t['currency']], f"{t['saleRateNB']} {t['purchaseRateNB']}", str(t["saleRate"]), str(t["purchaseRate"]), f"{round(money * t['saleRateNB'], 2)}" if money else "")
                    except KeyError:
                        table.add_row(t['currency'], list_data[t['currency']], f"{t['saleRateNB']} {t['purchaseRateNB']}", "", "", f"{round(money * t['saleRateNB'], 2)}" if money else "") 
    console = Console()
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
