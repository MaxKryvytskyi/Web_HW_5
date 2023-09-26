import asyncio
import logging
import aiofiles
import aiohttp
import websockets
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
import re 
import datetime
import sys
from decimal import Decimal

sys.stdout.reconfigure(encoding='utf-8')

date = None
currencies = None
money = None

now = datetime.datetime.now()
ulr = "https://api.privatbank.ua/p24api/exchange_rates?json&date="

new_ulr = ""

async def parser_string(message):
    global date, currencies, money
    currencies = ["EUR", "USD"]
    date = re.sub(r".*-d ([0-9]+\.[0-9]+\.[0-9]+).*", r"\1", message)
    try:
        currencies = re.search(r'-c (.+?) -m', message).group(1).split()
    except AttributeError:
        pass
    money = re.sub(r".*-m ([0-9]+).*", r"\1", message)

async def date_check():
    global date, new_ulr
    try:
        date = datetime.datetime.strptime(date, "%d.%m.%Y")
    except ValueError:
        date = now.replace(day=now.day - (now.day - int(date[-1])))
        
    time = now.replace(day=now.day - 10)
    if time <= date <= now:
        date = date.date().strftime("%d.%m.%Y")
    elif date > now:
        date = now.date().strftime("%d.%m.%Y")
    else: 
        date = time.date().strftime("%d.%m.%Y")
    new_ulr = f"{ulr}{date}"
async def request(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    r = await response.json()
                    return r
                logging.error(f"Error status {response.status} for {url}")
        except aiohttp.ClientConnectorError as e:
            logging.error(f"Connection error {url}: {e}")
        return None

async def get_exchange():
    res = await request(new_ulr)
    result = await data_output(res)
    return result 

async def data_output(datas):
    result = f"Курс валют на {date}-"
    for data in datas["exchangeRate"]:
        for currency in currencies:
            if currency.upper() == data['currency']:
                if money.isnumeric():
                    result += "{} {} = {} UAH-".format(money, data['currency'],  round(Decimal(money) * Decimal(data['saleRateNB']), 2))
                else:
                    result += "1 {}: buy {} sale {} UAH-".format(data['currency'], data['saleRateNB'], data['purchaseRateNB'])
    return str(result)

class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def send_to_client(self, message: str, ws: WebSocketServerProtocol):
        await ws.send(message)

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if re.search(r'exchange', message):
                if len(message) == 8:
                    await self.send_to_client(f"Невірна команда {message}", ws)
                else:
                    logging.info(f'{message}')
                    await parser_string(message)
                    await date_check()
                    r = await get_exchange()
                    text = r.split("-")
                    for t in text:
                        await self.send_to_client(t, ws)
                await self.log_exchange_to_file(ws.name, date)
            elif re.search(r'help', message):
                help_str = f"exchange -d 25.09.2023 -c eur usd -m 1232 | -d {now.date()} & 0-10| -c EUR USD| -m 100 |"
                for t2 in help_str.split("|"):
                    await self.send_to_client(t2, ws)
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


    async def log_exchange_to_file(self, username, days):
        date_str = datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")
        log_message = (
            f"{date_str} {username} executed 'exchange' command for {days} days."
        )
        async with aiofiles.open("exchange.log", mode="a") as log_file:
            await log_file.write(log_message + "\n")

async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future() 


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, handlers=[
    logging.FileHandler("sort_log.txt"),
    logging.StreamHandler()], format="%(asctime)s %(message)s")
    asyncio.run(main())