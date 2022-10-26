import requests
import re

from . import USER_AGENT
from .model import CountryEnum, SubdivisionEnum

from bs4 import BeautifulSoup


class GeonamesFetcher:
    COUNTRIES_URL = 'https://www.geonames.org/countries/'

    SubdivisionTypeAlias = {
        "department": ["département", "departamento"],
        "province": ["provincia"],
    }

    CountyContinentAlias = {
        "CX": "C_AS",
        "TL": "C_AS"
    }

    def get_countries(self):
        countries = []
        rows = self.__get_html(self.COUNTRIES_URL).find("table", id='countries').find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if cells:
                country_code = cells[0].get_text().strip()
                country_name = cells[4].get_text().strip()
                if country_code in self.CountyContinentAlias:
                    continent_code = self.CountyContinentAlias[country_code]
                else:
                    continent_code = 'C_{0}'.format(cells[8].get_text().strip())
                countries.append(CountryEnum(country_code, country_name, continent_code))
        return countries

    def get_continent_subdivisions(self, countries):
        subdivisions = {}
        for country in countries:
            print("Getting subdivisions for country {0}".format(country.code))
            subdivisions.setdefault(country.continent, []).extend(self.get_country_subdivision(country))
        return subdivisions

    def get_country_subdivision(self, country):
        subdivisions = []
        subdivision_url = 'https://www.geonames.org/{0}/administrative-division-{1}.html'.format(country.code,
                                                                                                 country.name.lower())
        html_content = self.__get_html(subdivision_url)

        subdivision1_rows = html_content.find("table", id='subdivtable1')
        if subdivision1_rows:
            for row in subdivision1_rows.find_all("tr"):
                cells = row.find_all("td")
                if cells and len(cells) > 10 and not cells[11].get_text() and cells[1].get_text().strip():
                    subdivisions.append(
                        self.__create_subdivision_enum(cells[1].get_text().strip(), cells[4].get_text().strip(),
                                                       cells[5].get_text().strip(), country))

        subdivision2_rows = html_content.find("table", id='subdivtable2')
        if subdivision2_rows:
            for row in subdivision2_rows.find_all("tr"):
                cells = row.find_all("td")
                if cells and len(cells) > 11 and not cells[12].get_text() and cells[1].get_text().strip():
                    subdivisions.append(
                        self.__create_subdivision_enum(cells[1].get_text().strip(), cells[5].get_text().strip(),
                                                       cells[6].get_text().strip(), country))

        subdivision3_rows = html_content.find("table", id='subdivtable3')
        if subdivision3_rows:
            print("WARNING: More subdivision were found on subdivtable3. {0}".format(country))

        return subdivisions

    def __create_subdivision_enum(self, code, name, type, country, sanitise_type=True):
        code = '{0}-{1}'.format(country.code, code)
        if sanitise_type:
            return SubdivisionEnum(code=code, name=self.__clean_name(name),
                                   type=self.__get_type_alias(self.__create_type(type)), parent=country.code,
                                   country=country)
        return SubdivisionEnum(code=code, name=self.__clean_name(name), type=type, parent=country.code,
                               country=country)

    def __get_type_alias(self, type):
        for subdivision_alias in self.SubdivisionTypeAlias:
            if type in self.SubdivisionTypeAlias[subdivision_alias]:
                return subdivision_alias
        return type

    @staticmethod
    def __create_type(type):
        sanitized_type = type.lower()
        search_result = re.search(r".*\((?P<type>.*)\).*", sanitized_type)
        if search_result:
            return search_result.group("type").strip()
        search_result = re.search(r"(?P<type>.*) \[english] / .* \[.*]", sanitized_type)
        if search_result:
            return search_result.group("type").strip()
        search_result = re.search(r"(?P<type>.*) \[french] / .* \[.*]", sanitized_type)
        if search_result:
            return search_result.group("type").strip()
        search_result = re.search(r".* \[.*] / (?P<type>.*) \[english]", sanitized_type)
        if search_result:
            return search_result.group("type").strip()
        search_result = re.search(r"(?P<type>.*) \[.*]", sanitized_type)
        if search_result:
            return search_result.group("type").strip()
        return sanitized_type if sanitized_type else 'UNKNOWN'

    @staticmethod
    def __get_html(url):
        headers = {'User-Agent': USER_AGENT.random}
        response = requests.get(url, headers=headers)
        return BeautifulSoup(response.content, "html.parser")

    @staticmethod
    def __clean_name(name):
        name = name.replace('*', '')
        search_result = re.search(r"(?P<name>.*) \(see also separate ISO 3166-1 entry under [A-Z]{2}\)", name)
        if search_result:
            return search_result.group("name").strip()
        return name
