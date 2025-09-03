import csv
import iso4217parse
import re
import requests
import xml.etree.ElementTree as ET

from . import USER_AGENT
from .model import SubdivisionWithParentEnum, CountryEnum, CurrencyEnum

from bs4 import BeautifulSoup
from io import StringIO
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


class IsoFetcher:
    COUNTRY_URL = 'https://www.iso.org/obp/ui/#search'
    SUBDIVISION_URL = 'https://www.iso.org/obp/ui/#iso:code:3166:{0}'
    CURRENCY_URL = 'https://www.six-group.com/dam/download/financial-information/data-center/iso-currrency/lists/list-one.xml'
    DEPRECATED_CURRENCY_URL = 'https://raw.githubusercontent.com/datasets/currency-codes/master/data/codes-all.csv'

    driver_options = Options()
    driver_options.add_argument(f'user-agent={USER_AGENT.get_random_user_agent()}')
    driver_options.add_argument("--headless")

    driver_path = None

    def __init__(self, driver_path):
        self.driver_path = driver_path

    def get_countries(self):
        print("Getting countries")
        driver = webdriver.Chrome(self.driver_path, options=self.driver_options)
        countries = []
        try:
            driver.get(self.COUNTRY_URL)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))).click()
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "gwt-uid-12"))).click()
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'v-button-go')]"))).click()
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//select[contains(@class, 'v-select-select')]")))
            Select(driver.find_element(By.XPATH,
                                       "//select[contains(@class, 'v-select-select')]")).select_by_visible_text(
                '300')
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//table//tr/td[contains(text(), 'Zimbabwe')]")))
            rows = BeautifulSoup(driver.page_source, "html.parser").find("table", attrs={'role': 'grid'}).find_all(
                "tr")
            for row in rows:
                cells = row.find_all("td")
                if cells:
                    name = self.__clean_region_name(cells[0].get_text()).strip()
                    code = cells[2].get_text().strip()
                    countries.append(CountryEnum(code, name, '', ''))
            return countries
        except Exception as ex:
            print("Failed loading countries. Ex: {0}".format(ex))
            return []
        finally:
            driver.close()

    def get_subdivisions(self, country):
        print("Getting subdivisions for country {0}".format(country.code))
        try:
            return self.__get_subdivision_from_html_content(country, self.__get_subdivisions_html(country))
        except Exception as ex:
            print("Failed getting subdivisions for country {0}. Ex: {1}".format(country.code, ex))
            return []

    def get_currencies(self):
        currencies = set()

        response = requests.get(self.CURRENCY_URL)
        root = ET.fromstring(response.text)

        for ccy_ntry in root.findall('.//CcyNtry'):
            ccy_nm = ccy_ntry.find('CcyNm')
            ccy = ccy_ntry.find('Ccy')
            if ccy is not None and ccy_nm is not None:
                currency_name = ccy_nm.text
                currency_code = ccy.text
                currencies.add(
                    CurrencyEnum(currency_code, currency_name, self.get_currency_symbol(currency_code), False)
                )

        return currencies

    def get_deprecated_currencies(self):
        currencies = set()

        resp = requests.get(self.DEPRECATED_CURRENCY_URL)
        data = csv.DictReader(StringIO(resp.text))
        for row in data:
            if row.get("WithdrawalDate", "").strip():
                currencies.add(
                    CurrencyEnum(row.get('AlphabeticCode'), self.__clean_currency_name(row.get('Currency')),
                                 self.get_currency_symbol(row.get('AlphabeticCode')), False)
                )

        return currencies

    @staticmethod
    def get_currency_symbol(currency_code):
        currency = iso4217parse.by_alpha3(currency_code)
        return currency.symbols[0] if currency and currency.symbols else ''

    def __get_subdivisions_html(self, country):
        driver = webdriver.Chrome(self.driver_path, options=self.driver_options)
        try:
            driver.get(self.SUBDIVISION_URL.format(country.code))
            element_present = EC.presence_of_element_located((By.ID, 'subdivision'))
            WebDriverWait(driver, 30).until(element_present)
            return driver.page_source
        except Exception as ex:
            print("Failed loading '{0} subdivisions'. Ex: {1}".format(country.code, ex))
            return None
        finally:
            driver.close()

    def __get_subdivision_from_html_content(self, country, html_content):
        subdivisions = {}
        html = BeautifulSoup(html_content, "html.parser")
        rows = html.find("table", id='subdivision').find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if cells:
                type = cells[0].get_text().strip()
                code = self.__clean_subdivision_code(cells[1].get_text().strip())
                name = self.__clean_region_name(cells[2].get_text().strip())
                language = cells[4].get_text().strip()
                parent = cells[6].get_text().strip()
                if not parent:
                    parent = country.code
                subdivisions.setdefault(code, {}).setdefault(language,
                                                             SubdivisionWithParentEnum(code, name, type, parent,
                                                                                       country))

        language_subdivisions = []
        for subdivision in subdivisions:
            if 'en' in subdivisions[subdivision]:
                language_subdivisions.append(subdivisions[subdivision]['en'])
            else:
                first_language = list(subdivisions[subdivision].keys())[0]
                language_subdivisions.append(subdivisions[subdivision][first_language])
        return language_subdivisions

    @staticmethod
    def __clean_region_name(name):
        name = name.replace('*', '')
        search_result = re.search(r"(?P<name>.*) \(see also separate country code entry under [A-Z]{2}\)", name)
        if search_result:
            return search_result.group("name").strip()
        return name

    @staticmethod
    def __clean_subdivision_code(code):
        return code.replace('*', '')

    @staticmethod
    def __clean_currency_name(name):
        cleaned = re.sub(r'"[^"]*"\s*', '', name)
        cleaned = cleaned.replace('\u00A0', ' ')
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()
