import logging
import os
import time
from typing import List, Optional

import pyotp
from bs4 import BeautifulSoup
from requests import Session
from selenium.common import exceptions as selenium_exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from base.base_browser import BaseBrowser
from g2g.exceptions import BadCookieError, ServerResponseError

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
AUTH_URL = "https://www.g2g.com/login"
BEAUTIFUL_SOUP_PARSER = "html.parser"


class BaseG2g(BaseBrowser):
    def get_totp(self) -> str:
        totp = pyotp.TOTP(os.environ["totp"])
        return totp.now()

    def mfa_auth(self) -> None:
        self.browser.implicitly_wait(10)
        code = self.get_totp()
        input_rows = self.browser.find_elements(by=By.CLASS_NAME, value="otp-input")
        for i, row in zip(range(1, 7), input_rows):
            char_code = code[i - 1] if i != 1 else code[0]
            row.send_keys(char_code)

    def login(self) -> None:
        self.browser.get(AUTH_URL)
        WebDriverWait(self.browser, 30).until(EC.presence_of_element_located((By.TAG_NAME, "form")))
        self.browser.find_elements(by=By.XPATH, value="//input[@*]")[0].send_keys(os.environ["g2g_login"])
        self.browser.find_elements(by=By.XPATH, value="//input[@*]")[1].send_keys(os.environ["g2g_password"])
        self.browser.find_elements(by=By.TAG_NAME, value="button")[1].click()
        self.mfa_auth()
        try:
            WebDriverWait(self.browser, 120).until(
                lambda x: x.find_element(by=By.CSS_SELECTOR, value=".antigate_solver.solved")
            )
        except selenium_exceptions.TimeoutException:
            while "https://www.g2g.com/login/mfa_otp" in self.browser.current_url:
                self.browser.refresh()
                self.browser.find_elements(by=By.XPATH, value="//input[@*]")[0].send_keys(os.environ["g2g_login"])
                self.browser.find_elements(by=By.XPATH, value="//input[@*]")[1].send_keys(os.environ["g2g_password"])
                WebDriverWait(self.browser, 120).until(
                    lambda x: x.find_element(by=By.CSS_SELECTOR, value=".antigate_solver.solved")
                )
        self.browser.find_elements(by=By.TAG_NAME, value="button")[1].click()
        time.sleep(5)
        self.state = "auth"
        logging.info("Sender authenticated")


class Page:
    def __init__(self, region: Optional[int], service: int, game: int, session: Session) -> None:
        self.url_page = "https://www.g2g.com/sell/manage"
        self.region = region
        self.service = service
        self.game = game
        self.sess = session
        self.listing_ids: List[str] = []

    def set_default(self) -> None:
        """Sets default url page"""
        self.url_page = "https://www.g2g.com/sell/manage"

    def get_html(self, page_number: int = 1) -> str:
        """Getting html markup of a page.

        Args:
            page_number: The page number value for markup greater or equal 1.

        Returns:
            Html page markup.

        Raises:
            BadCookieException: If cookie for website expired.
            ServerErrorResponseException: If the server return error code like 502 and etc.
        """
        self.url_page += f"?region={self.region}&service={self.service}&game={self.game}&page={page_number}"
        html = self.sess.get(self.url_page)
        if "sellButton" in html.url or "LOGIN REQUIRED" in html.text:
            raise BadCookieError("Bad cookie")
        if html.status_code != 200:
            raise ServerResponseError(html.status_code)
        self.set_default()
        return html.text

    def get_count_pages(self) -> int:
        """Getting the total number of pages of a section.

        Returns:
            Number of pages.
        """
        page_count = self.get_html()
        soup = BeautifulSoup(page_count, BEAUTIFUL_SOUP_PARSER)
        pagination = soup.find("li", {"class": "last"})
        if pagination is None:
            return 1
        number = int(pagination.find("a").get("href").split("=")[-1].split("&")[0])
        return number

    def get_listing_ids(self) -> List[str]:
        """Getting all listing numbers from a section.

        Returns:
            Listing numbers from a section.
        """
        number_pages = self.get_count_pages()
        for number_page in range(1, number_pages + 1):
            listing = self.get_html(number_page)
            soup = BeautifulSoup(listing, BEAUTIFUL_SOUP_PARSER)
            ids = list(map(str, soup.find("input", {"id": "c2c_listing_ids"}).get("value").split(",")))
            self.listing_ids.extend(ids)
        return self.listing_ids
