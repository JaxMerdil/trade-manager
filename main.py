import logging
import os
import sys
import threading
import time

import requests
from aiohttp import web

from g2g.message_notify import G2gNotify
from g2g.update import G2gUpdate
from funpay.update_offers import FunpayUpdate

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
http_logger = logging.getLogger("aiohttp.access")
http_logger.setLevel(logging.INFO)
COOKIE_URL = "http:/192.168.0.1:8081/"


def web_server(g2g_notify):
    """Web server for sending cookie at request for update listings."""
    app = web.Application(logger=http_logger)
    app.add_routes([web.get("/", g2g_notify.send_cookie)])
    web.run_app(app, port=8081)


def threading_factory(funcs, args):
    thread_dict = {}
    for i in range(len(funcs)):
        thread_dict[i] = threading.Thread(target=funcs[i], args=args[f"{funcs[i]}"]).start()
    while True:
        for thread in thread_dict.keys():
            if not thread_dict[thread].is_alive():
                pass


def update_listing_price(g2g_notify):
    while g2g_notify.state != "auth":
        time.sleep(60)
    while True:
        cookie = requests.get(COOKIE_URL).json()
        update = G2gUpdate(game=20028, service=16, cookie=cookie, region=[])
        logging.info(update.update_listing_prices())
        time.sleep(86400)


def update_listing_time(g2g_notify):
    while g2g_notify.state != "auth":
        time.sleep(60)
    while True:
        cookie = requests.get(COOKIE_URL).json()
        update = G2gUpdate(game=20028, service=16, cookie=cookie, region=[])
        logging.info(update.update_listings_time())
        time.sleep(14400)


def run():
    # g2g_online = G2gNotify()
    g2g_notify = G2gNotify()
    # funpay_update = FunpayUpdate()
    server_thread = threading.Thread(target=web_server, args=(g2g_notify,))
    server_thread.start()
    notify_thread = threading.Thread(target=g2g_notify.notify_loop)
    notify_thread.start()
    ##online_thread.start()
    # funpay_update_thread = threading.Thread(target=funpay_update.check_time)
    # funpay_update_thread.start()
    managment_price_thread = threading.Thread(target=update_listing_price, args=(g2g_notify,))
    managment_price_thread.start()
    # update_time_thread = threading.Thread(target=update_listing_time, args=(g2g_notify,))
    # update_time_thread.start()
    while True:
        try:
            if not notify_thread.is_alive():
                g2g_notify.browser.quit()
                logging.info("Error. Restarting g2g notify.")
                g2g_notify = G2gNotify()
                notify_thread = threading.Thread(target=g2g_notify.notify_loop)
                notify_thread.start()
            """if not online_thread.is_alive():
                g2g_online.browser.quit()
                logging.info("Error. Restarting g2g online update.")
                g2g_online = G2gNotify()
                online_thread = threading.Thread(target=g2g_online.infinity_online_status)
                online_thread.start()"""
            if not server_thread.is_alive():
                server_thread = threading.Thread(target=web_server)
            if not managment_price_thread.is_alive():
                g2g_notify.browser.quit()
                logging.info("Error. Restarting g2g price update.")
                g2g_notify = G2gNotify()
                managment_price_thread = threading.Thread(target=update_listing_price, args=(g2g_notify,))
                managment_price_thread.start()
            """if not funpay_update_thread.is_alive():
                funpay_update.browser.quit()
                logging.info("Error. Restarting funpay update.")
                funpay_update = FunpayUpdate()
                funpay_update_thread = threading.Thread(target=funpay_update.check_time)
                funpay_update_thread.start()
                logging.info("Restarted funpay update successful")
                if not update_time_thread.is_alive():
                g2g_notify.browser.quit()
                logging.info("Error. Restarting update time g2g")
                g2g_notify = G2gNotify()
                update_time_thread = threading.Thread(target=update_listing_time, args=(g2g_notify,))
                update_time_thread.start()"""
            time.sleep(60)
        except KeyboardInterrupt:
            print("Interrupted")
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)


run()
