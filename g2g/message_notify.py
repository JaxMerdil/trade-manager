import json
import logging
import os
import time
from typing import Union

import requests
from selenium.webdriver.common.by import By
from aiohttp.web_response import Response
from aiohttp import web

from g2g.base_g2g import BaseG2g

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

COUNT_NOTICE_URL = "https://www.g2g.com/userBar/countNotice"
UNREAD_CHAT_URL = "https://www.g2g.com/userBar/UnreadChat"
TG_BOT_URL = f'https://api.telegram.org/bot{os.environ["bot_token"]}/sendMessage?'
TG_CHAT_IDS = ["1424451073", "1138118284"]


class G2gNotify(BaseG2g):
    def notify_loop(self) -> str:
        """Infinity loop for check whether exist unread messages or new orders.

        Returns:
           If return error more then 2 times or any exceptions from check func then thread with this loop is restarted.
        """
        while True:
            if self.state == "unauth":
                self.login()
                self.browser.implicitly_wait(10)
            resp = self.get_unread_message()
            if resp == "Error":
                return "Error"
            self.browser.get("https://www.g2g.com/sfqboost")
            time.sleep(170)

    def get_count_messages(self, method: str) -> int:
        """Getting count new messages or new orders.

        Arguments:
            method: Counting the number of messages or orders.

        Return:
            count_messages: Number of messages or orders.

        """
        url = UNREAD_CHAT_URL if method == "message" else COUNT_NOTICE_URL
        self.browser.get(url)
        response = self.browser.find_element(by=By.TAG_NAME, value="body").text
        data = json.loads(response)
        if method == "message":
            count_messages = data["payload"]["unread_count"]
        if method == "order":
            count_messages = data["t_order"]
        text = "Непрочитанных сообщений" if method == "message" else "Новых заказов"
        if count_messages != 0:
            self.send_tg_msg(f"{text}: {count_messages}", is_all=True)
        return count_messages

    def get_unread_message(self) -> Union[str, None]:
        """Getting unread messages or new orders.

        Return:
            If except error return string "Error" else None.
        """
        logging.info("Checking Messages")
        try:
            count_messages = self.get_count_messages("message")
            logging.info(f"Unread Messages: {count_messages}")
            self.get_count_messages("order")
        except:  # noqa E722
            if self.error_count > 2:
                self.browser.quit()
                logging.error("Number of errors exceeded. Restarting webdriver.")
                return "Error"
            self.error_count += 1
            self.browser.refresh()
            logging.info(f"Error. Can`t check message. Delay start. Attempt №{self.error_count}")
        return None

    def infinity_online_status(self) -> None:
        """Constantly updating online status in chat. If any error occurs then restarted webdriver thread."""
        try:
            while True:
                if self.state == "unauth":
                    self.login()
                    self.browser.implicitly_wait(10)
                    self.browser.get("https://www.g2g.com/chat/#/")
                if "chat" in self.browser.current_url:
                    self.browser.refresh()
                else:
                    self.browser.get("https://www.g2g.com/chat/#/")
                time.sleep(420)
        except:  # noqa: E722
            print("Chat online Error. Restarting driver.")
            self.browser.quit()

    async def send_cookie(self, request) -> Response:
        """Return web response with requested cookie for this site.

        Arguments:
            request: request from web with passing GET parameters.

        Return:
            Response: Json response with cookie data.

        """
        cookie = self.get_cookie([], is_all=True, is_dict=True, domain=".www.g2g.com")
        return web.json_response(data=cookie)

    def send_tg_msg(self, text: str, is_all: bool = False, chat_id: int = None) -> None:
        """Sending message in telegram with required text. With number new messages in chat or number new orders.

        Arguments:
            text: text for sending in telegram.
            is_all: Include all recipients or not. If not need include all then pass chat_id parameter.
            chat_id: If not included all recipients, message will be sent only on passed chat_id.

        """
        with requests.Session() as session:
            if not is_all:
                session.get(f"{TG_BOT_URL}chat_id={chat_id}&text={text}")
            else:
                for chat_id in TG_CHAT_IDS:
                    session.get(f"{TG_BOT_URL}chat_id={chat_id}&text={text}")
