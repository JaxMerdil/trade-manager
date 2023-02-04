import logging
import time
from selenium.webdriver.common.by import By
from funpay.base_funpay import BaseFunpay
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

FUNPAY_PROFILE = "https://funpay.com/users/1457203/"
FUNPAY_CHECKBOXES = "//div[contains(@class,'checkbox')]/label"
LOAD_DELAY = 2.5
MAINTENCE_RESTART = 10


class FunpayUpdate(BaseFunpay):
    def _click_update_btn(self):
        raise_offers_btn = self.browser.find_element(
            by=By.CSS_SELECTOR, value="button.btn.btn-default.btn-block.js-lot-raise"
        )
        raise_offers_btn.click()

    def check_time(self):
        restart_counter = 0
        while True:
            if self.state != "auth":
                status = self.login()
                if status is not None:
                    break
            offers_info = self.get_offers_link()
            for link in offers_info:
                self.browser.get(link)
                time.sleep(LOAD_DELAY)
                self.check_modal()
                id = link.split("/")[-2]
                logging.info(f"Был проверен раздел: {id}")
            logging.info("Были проверены все предложения.")
            restart_counter += 1
            if restart_counter >= MAINTENCE_RESTART:
                self.browser.quit()
                break
            time.sleep(600)

    def _click_modal(self):
        checkbox_inputs = self.browser.find_elements(
            by=By.XPATH,
            value=FUNPAY_CHECKBOXES,
        )
        for label in checkbox_inputs:
            checkbox = label.find_element(by=By.TAG_NAME, value="input")
            if checkbox.is_selected():
                continue
            try:
                label.click()
            except ElementNotInteractableException:
                continue
        self.browser.find_element(by=By.CSS_SELECTOR, value="button.btn.btn-primary.btn-block.js-lot-raise-ex").click()

    def get_offers_link(self):
        self.browser.get(FUNPAY_PROFILE)
        link_elements = self.browser.find_elements(by=By.CSS_SELECTOR, value="a.btn.btn-default.btn-plus")
        offer_links = [elem.get_attribute("href") for elem in link_elements]
        return offer_links

    def check_modal(self) -> bool:
        is_currency_offer = self.browser.find_elements(
            by=By.XPATH, value="//*[@id='content']/div/div/div[2]/div/form/div/div[2]/div/div[3]/div[1]/div[1]"
        )
        if is_currency_offer:
            return False
        self._click_update_btn()
        time.sleep(LOAD_DELAY)
        is_modal_exist = self.browser.find_elements(
            by=By.CSS_SELECTOR, value="body > div.modal.fade.modal-raise-nodes.in"
        )
        if is_modal_exist:
            self._click_modal()
        return True

    def update_inactive(self, link: str) -> str:
        self.browser.get(link)
        inactive_offers = self.browser.find_elements(by=By.CSS_SELECTOR, value="a.tc-item.warning")
        game_name = self.browser.find_elements(by=By.CSS_SELECTOR, value="span.inside")
        if game_name:
            game_name = game_name[0].text
        else:
            game_name = self.browser.current_url.split("/")[3]
        if not inactive_offers:
            return f"Неактивных предложений не найдено в разделе {game_name}"
        for inactive_offer in inactive_offers:
            try:
                inactive_offer.click()
                offer_title = self.browser.find_elements(by=By.NAME, value="fields[summary][ru]")
                if offer_title:
                    offer_title = offer_title[0].get_attribute("value")
                else:
                    offer_title = "Неизвестное предложение"
                save_btn = self.browser.find_element(
                    by=By.CSS_SELECTOR, value="button.btn.btn-primary.btn-block.js-btn-save"
                )
                save_btn.click()
                logging.info(f"{offer_title} успешно активировано в разделе {game_name}.")
            except NoSuchElementException:
                logging.error(f"Ошибка активации предложения в игре {game_name}")
        return f"Все неактивные предложения в разделе {game_name} были подняты."
