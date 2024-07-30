import requests

from . import USER_AGENT
from .model import CurrencyEnum

from bs4 import BeautifulSoup


class CryptoCurrencyFetcher:
    CRYPTO_CURRENCIES_URL = 'https://www.ifcmarkets.com/en/cryptocurrency-abbreviations'

    TestCurrencies = [
        CurrencyEnum('TST', 'Standard Token', '', True),
        CurrencyEnum('TETH', 'Test Ethereum', '', True)
    ]

    def get_crypto_currencies(self):
        crypto_currencies = []
        rows = self.__get_html(self.CRYPTO_CURRENCIES_URL).find("table", id='equities_table').find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if cells:
                name = cells[0].get_text().strip()
                code = cells[1].get_text().strip()
                symbol = cells[2].get_text().split(',')[0].strip()
                crypto_currencies.append(CurrencyEnum(code, name, symbol, False))
        crypto_currencies.extend(self.TestCurrencies)
        return crypto_currencies

    @staticmethod
    def __get_html(url):
        return BeautifulSoup(CryptoCurrencyFetcher.__get_response(url).content, "html.parser")

    @staticmethod
    def __get_response(url):
        headers = {'User-Agent': USER_AGENT.get_random_user_agent()}
        return requests.get(url, headers=headers)
