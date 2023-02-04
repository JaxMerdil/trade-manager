import os
from typing import Union

import requests


class Error(Exception):
    """Base class for Exceptions"""

    def __init__(self, error: Union[int, str]) -> None:
        self.error = error
        self.error_url = f'https://api.telegram.org/bot{os.environ["bot_token"]}/sendMessage?chat_id=353178156&text='


class BadCookieError(Error):
    """Bad Cookie Exception."""

    def send_error(self) -> None:
        requests.get(f"{self.error_url}{self.error}")


class WrongResponseError(Error):
    """Received wrong response from server"""

    def send_error(self) -> None:
        requests.get(f"{self.error_url}{self.error}")


class ServerResponseError(Error):
    """Any error on serverside"""

    def send_error(self) -> None:
        requests.get(f"{self.error_url}Ошибка сервера: {self.error}")
