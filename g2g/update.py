import json
import logging
import os
import time
from typing import Dict, List, Optional, Union

import gspread
import requests
from g2g.base_g2g import Page

from base import tinkoff
from g2g.exceptions import ServerResponseError, WrongResponseError

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)


class G2gUpdate:
    def __init__(self, game: int, service: int, cookie: Dict, region: List[Optional[int]]) -> None:
        self.game = game
        self.regions = region
        self.service = service
        self.sess = requests.Session()
        cookie_jar = requests.utils.cookiejar_from_dict(cookie)
        self.sess.cookies = cookie_jar
        self.last_exchange_rate = 0
        self.sess.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
                "x-requested-with": "XMLHttpRequest",
            }
        )
        self.url_raise = "https://www.g2g.com/sell/productAction"
        self.url_update = "https://www.g2g.com/sell/updateListing"

    def update_listings_time(self) -> str:
        if not self.regions:
            self.regions = [0]
        for region in self.regions:
            if self.regions[0] != region:
                time.sleep(60)
            pages = Page(region, self.service, self.game, self.sess)
            listing_ids = pages.get_listing_ids()
            if not listing_ids[0]:
                continue
            self.url_raise += f"?region={region}&service={self.service}&game={self.game}"
            self.sess.headers.update({"Content-Type": "application/x-www-form-urlencoded"})
            for _ in range(0, len(listing_ids), 50):
                data = {"listingId": "page", "ids": ",".join(listing_ids[:50]), "actionType": "extend"}
                update_listings = self.sess.post(self.url_raise, data=data)
                if update_listings.status_code != 200:
                    raise ServerResponseError(update_listings.status_code)
                result = update_listings.json()
                if result["result"] != 1:
                    raise WrongResponseError(result["infoMsg"])
                del listing_ids[:50]
            time.sleep(5)
        return f"Listings time updated for {self.game} and {self.service} service"

    def _calculating_price(self, exchange_rate: float) -> Union[bool, List]:
        prices_path = os.path.abspath(f"g2g/prices/price-{self.service}-{self.game}.json")
        if not os.path.isfile(prices_path):
            return False
        else:
            with open(prices_path, mode="r", encoding="utf-8-sig") as f:
                offers = json.load(f)
            listing_offers = []
            for offer in offers.items():
                offer_id = offer[1]["offer_id"]
                converted_price = round(offer[1]["price"] * exchange_rate, 10)
                listing_offers.append({"offer_id": offer_id, "price": converted_price})
            return listing_offers

    def _get_crown_price(self) -> Union[str, None]:
        credentials_path = os.path.abspath("./base/crownmanagment-aae66046428e.json")
        gc = gspread.service_account(credentials_path)
        config_sheet = gc.open("Кроны тесо").sheet1
        rub_crown_price = config_sheet.acell("N3").value
        return rub_crown_price

    def _set_default(self):
        self.url_raise = "https://www.g2g.com/sell/productAction"
        self.url_update = "https://www.g2g.com/sell/updateListing"

    def update_listing_prices(self) -> str:
        crown_price = float(self._get_crown_price().replace(",", "."))
        exchange_rate = tinkoff.calculating_price(price=crown_price, currency="USD")
        if exchange_rate == self.last_exchange_rate:
            return f"Exchange rate the same. Not need update prices for {self.game} and {self.service} service"
        self.last_exchange_rate = exchange_rate
        prices = self._calculating_price(exchange_rate)
        if not prices:
            logging.info("Not found file with prices for updating.")
            return f"No price update in {self.service} service at {self.game} game"
        self.last_exchange_rate = exchange_rate
        if not self.regions:
            self.regions = [0]
        for region in self.regions:
            logging.info(f"Start updating prices for {region} region in {self.game} game and {self.service} service")
            self.url_update += f"?region={region}&service={self.service}&game={self.game}"
            self.sess.headers.update({"Content-Type": "application/x-www-form-urlencoded"})
            for i in range(len(prices)):
                payload = {
                    "ids": "",
                    "name": "products_price",
                    "pk": f"{prices[i]['offer_id']}",
                    "scenario": "update",
                    "type": "single",
                    "value": f"{round(prices[i]['price'], 6)}",
                }
                resp = self.sess.post(self.url_update, data=payload)
                if resp.ok:
                    if resp.json()["success"] is False:
                        logging.info(f"{resp.text} pk: {payload['pk']}")
            self._set_default()
            logging.info(f"Updated prices for region {region}")
        return f"Prices updated for {self.game} and {self.service} service"

    def get_price(self, server_id, side) -> Union[float, None]:
        with open("prices.json", "r") as f:
            prices = json.load(f)
        for price in prices:
            if price["server_id"] != server_id and price["side"] != side:
                continue
            price = price["price"]
            return price
        return None

    def send_msg(self, text):
        pass

    def update_static_prices(self) -> str:
        with open("offers_ids.json", "r") as f:
            offers = json.load(f)

        for offer in offers:
            offer_id = offer["offer_id"]
            price = self.get_price(offer["server_id"], offer["side"])
            if price is None:
                self.send_msg(f"Price not found for {offer_id} offer.")
                continue
