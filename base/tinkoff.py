import os
from typing import Union

import gspread
import requests

credentials_path = os.path.abspath("./base/crownmanagment-aae66046428e.json")
gc = gspread.service_account(credentials_path)
config_sheet = gc.open("Кроны тесо").sheet1


def exchange(frm: str, to: str) -> Union[float, str]:
    exchange_rate_sheet = config_sheet.acell("K3").value
    if exchange_rate_sheet:
        return float(exchange_rate_sheet)
    else:
        exchange_resp = requests.post("https://www.tinkoff.ru/api/trading/currency/get", json={"ticker": f"{frm}{to}"})
        if exchange_resp.status_code == 200:
            exchange_rate = exchange_resp.json()["payload"]["prices"]["last"]["value"]
            return exchange_rate
        else:
            return f"Error. Status code {exchange_resp.status_code}"


def calculating_price(price: float, currency: str) -> float:
    exchange_rate = exchange(currency, "RUB")
    if isinstance(exchange_rate, str):
        raise Exception("Error. Cannot get exchange rate")
    eur_convert = price / exchange_rate
    final_price = (eur_convert / 100 * (8.99)) + eur_convert
    return final_price


if __name__ == "__main__":
    print(calculating_price(0.15, "USD"))
