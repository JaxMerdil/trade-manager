import logging
import os
from typing import Union
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common import exceptions
import time

from base.base_browser import BaseBrowser


class BaseFunpay(BaseBrowser):
    def ip_challenge(self) -> None:
        content = self.browser.find_element(by=By.TAG_NAME, value="strong")
        if "номера" in content.text or "account number" in content.text:
            self.browser.find_element(by=By.TAG_NAME, value="input").send_keys(os.environ["secret_number"])
            self.browser.find_element(by=By.TAG_NAME, value="input").submit()
        else:
            self.browser.find_element(by=By.TAG_NAME, value="input").send_keys(os.environ["secret_card"])
            self.browser.find_element(by=By.TAG_NAME, value="input").submit()

    def login(self) -> Union[None, str]:
        self.browser.get("https://funpay.com/account/login")
        self.browser.find_element(by=By.NAME, value="login").send_keys(os.environ["fp_login"])
        self.browser.find_element(by=By.NAME, value="password").send_keys(os.environ["fp_password"])
        try:
            WebDriverWait(self.browser, 120).until(
                lambda x: x.find_element(by=By.CSS_SELECTOR, value=".antigate_solver.solved")
            )
        except exceptions.TimeoutException:
            timeout_count = 0
            while (
                self.browser.current_url == "https://funpay.com/account/login"
                or self.browser.current_url == "https://funpay.com/en/account/login"
            ):
                self.browser.refresh()
                self.browser.find_element(by=By.NAME, value="login").send_keys(os.environ["fp_login"])
                self.browser.find_element(by=By.NAME, value="password").send_keys(os.environ["fp_password"])
                WebDriverWait(self.browser, 120).until(
                    lambda x: x.find_element(by=By.CSS_SELECTOR, value=".antigate_solver.solved")
                )
                timeout_count += 1
                if timeout_count >= 3:
                    logging.error("Couldn't pass captcha test.")
                    self.browser.quit()
                    return "Couldn't pass captcha test."
        self.browser.find_element(by=By.NAME, value="password").submit()
        time.sleep(5)
        if (
            self.browser.current_url == "https://funpay.com/security/ipChallenge"
            or self.browser.current_url == "https://funpay.com/en/security/ipChallenge"
        ):
            self.ip_challenge()
        self.state = "auth"
