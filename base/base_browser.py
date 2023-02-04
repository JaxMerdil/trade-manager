import itertools
import json
import os
import time
from typing import Dict, List, Union
from ctypes import windll
from sys import platform

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from seleniumwire import webdriver as proxy_webdriver


class BaseBrowser:
    def acp_api_send_request(self, message_type, data={}):
        """Initialization anticaptcha plugin in Selenium with API key.

        Arguments:
            message_type: Type of message for plugin.
            data: options for plugin with anticaptcha API key.
        """
        message = {"receiver": "antiCaptchaPlugin", "type": message_type, **data}
        return self.browser.execute_script(f"return window.postMessage({json.dumps(message)});")

    def __init__(self, proxy: bool = False) -> None:
        """Initialization Selenium with anticaptcha plugin and if needed proxy.

        Arguments:
            proxy: bool value, whether to use a proxy.
        """
        self.cookie = ""
        self.error_count = 0
        self.state = "unauth"
        path = os.path.abspath("./base")
        options = webdriver.ChromeOptions()
        options.add_extension(f"{path}/anticaptcha-plugin_v0.61.crx")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        service = Service(f"{path}/chromedriver.exe")
        if proxy:
            options_seleniumWire = {
                "proxy": {
                    "https": f'https://{os.environ["fp_proxy"]}',
                }
            }
            self.browser = proxy_webdriver.Chrome(
                service=service, options=options, seleniumwire_options=options_seleniumWire
            )
        else:
            self.browser = webdriver.Chrome(service=service, options=options)
        if platform == "win32":
            width = windll.user32.GetSystemMetrics(0)
            height = windll.user32.GetSystemMetrics(1)
            self.browser.set_window_size(width, height)
        self.browser.get("https://antcpt.com/blank.html")
        self.acp_api_send_request("setOptions", {"options": {"antiCaptchaApiKey": os.environ["antiCaptchaApiKey"]}})
        time.sleep(5)

    def get_cookie(
        self, service: List, domain: str = "", is_all: bool = False, is_dict: bool = False
    ) -> Union[str, Dict]:
        """Return cookie string or dict in current browser for requested parameters.

        Arguments:
            service: List with needed cookie names. If need all cookies leave empty list.
            domain: domain name to fetch cookies.
            is_all: If need all cookies for this domain.
            is_dict: If need return dict with cookies instead string.

        Return:
            String or dict with cookies at depends passed parameters.
        """
        cookie_string = ""
        cookies_dict = {}
        cookies = self.browser.get_cookies()
        if not is_all:
            for cookie, requested_cookie in itertools.product(cookies, service):
                if cookie["name"] == requested_cookie:
                    if is_dict:
                        cookies_dict[cookie["name"]] = cookie["value"]
                    else:
                        cookie_string += f'{cookie["name"]}={cookie["value"]}; '
        else:
            for cookie in cookies:
                if is_dict and cookie["domain"] == domain:
                    cookies_dict[cookie["name"]] = cookie["value"]
                elif cookie["domain"] == domain:
                    cookie_string += f'{cookie["name"]}={cookie["value"]}; '
        if not is_dict:
            if cookie_string.endswith("; "):
                cookie_string = cookie_string[:-2]
            return cookie_string
        else:
            return cookies_dict
