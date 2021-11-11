import os
import sys
import logging
import time
import threading
import uuid

import pygamp as pg
import requests

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(stream_handler)


class SendCurrencyRate(threading.Thread):
    name = 'send_curr_rate'

    def __init__(self, client_id=None):
        # GA event params
        self.property_id = os.environ.get('PROPERTY_ID')
        if client_id:
            self.client_id = client_id  # create random client identifier
        else:
            self.client_id = str(uuid.uuid4())  # create random client identifier
        self.event_index = os.environ.get('EVENT_INDEX')  # 'UA/USD'

        self.time_to_sleep = 60  # seconds
        self.currency_rate_url = 'https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=5'

        threading.Thread.__init__(self)
        self.shutdown_flag = threading.Event()

    def run(self):
        while not self.shutdown_flag.is_set():
            time.sleep(self.time_to_sleep)

            try:
                response = requests.get(self.currency_rate_url)
                if response.status_code == 200:
                    if response.json():
                        rate = None
                        for currency in response.json():
                            if currency['ccy'] == 'USD':
                                rate = currency['buy']
                                break
                        if not rate:
                            logger.error(f'No rate for USD!')
                            continue

                        # sending custom metric to Google Analytics
                        pg.custom_metric(
                            cid=self.client_id,
                            property_id=self.property_id,
                            index=self.event_index,
                            value=str(rate))
                        logger.info(f'Metric sent | value: {rate}')

                    else:
                        logger.error(f'Empty currencies list!')
                else:
                    logger.info(f'Unexpected status code: {response.status_code}')
            except:
                logger.exception(f'Unexpected error')

    def stop(self):
        self.shutdown_flag.set()


if __name__ == '__main__':
    SendCurrencyRate(os.environ.get('CLIENT_ID')).start()
