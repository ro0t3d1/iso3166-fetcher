import os
from library.iso import IsoFetcher
from library.geonames import GeonamesFetcher
from library.model import to_type_enum
from library.ifcmarkets import CryptoCurrencyFetcher
from collections import OrderedDict

# Configure chromedriver path
CHROME_DRIVER_PATH = ''

# Configure output folder path
OUTPUT_FOLDER_PATH = 'output'

iso_fetcher = IsoFetcher(CHROME_DRIVER_PATH)
geonames_fetcher = GeonamesFetcher()
crypto_currency_fetcher = CryptoCurrencyFetcher()


def write_file_from_dataclass(entity_name, entities):
    with open(os.path.join(OUTPUT_FOLDER_PATH, "{0}.txt".format(entity_name)), 'w') as f:
        f.writelines([entity.to_java_enum() for entity in entities])


def write_file_from_lines(lines, file_name):
    with open(os.path.join(OUTPUT_FOLDER_PATH, "{0}.txt".format(file_name)), 'w') as f:
        f.writelines(lines)


def sort_subdivisions(continent_subdivisions):
    if not continent_subdivisions:
        return []
    continent_subdivisions.sort(key=lambda subdivision: subdivision.code)
    return sort_by_subdivision_level(continent_subdivisions)


def get_subdivision_level(country_code, subdivision, subdivisions):
    if subdivision.parent == country_code:
        return 1
    for country_subdivision in subdivisions:
        if subdivision.parent == country_subdivision.code:
            return 1 + get_subdivision_level(country_code, country_subdivision, subdivisions)
    return 0


def sort_by_subdivision_level(continent_subdivisions):
    sorted_subdivisions = []

    country_subdivisions_map = {}
    for subdivision in continent_subdivisions:
        country_subdivisions_map.setdefault(subdivision.country.code, []).append(subdivision)

    for country in country_subdivisions_map:
        subdivisions_by_level = {}

        for subdivision in country_subdivisions_map[country]:
            subdivisions_by_level.setdefault(
                get_subdivision_level(country, subdivision, country_subdivisions_map[country]), []).append(subdivision)

        for level in OrderedDict(sorted(subdivisions_by_level.items())):
            subdivisions_by_level[level].sort(key=lambda subdivision: subdivision.code)
            sorted_subdivisions.extend(subdivisions_by_level[level])

    return sorted_subdivisions


if __name__ == '__main__':
    countries = []

    # Get countries from geonames
    geonames_country_map = {}
    for geonames_country in geonames_fetcher.get_countries():
        geonames_country_map[geonames_country.code] = geonames_country

    # Get countries from iso.org
    iso_org_country_map = {}
    for iso_org_country in iso_fetcher.get_countries():
        # Data repair continent information
        iso_org_country.continent = geonames_country_map.get(iso_org_country.code).continent
        countries.append(iso_org_country)
        iso_org_country_map[iso_org_country.code] = iso_org_country

    # Get subdivisions from iso.org
    iso_org_continent_subdivisions = {}
    for country in countries:
        subdivisions = iso_fetcher.get_subdivisions(country)
        iso_org_continent_subdivisions.setdefault(country.continent, []).extend(subdivisions)

    # Add countries from geonames that do not exist in iso.org
    for geonames_country in geonames_country_map:
        if geonames_country not in iso_org_country_map:
            countries.append(geonames_country_map[geonames_country])

    # Get subdivision from geonames
    geonames_continent_subdivisions = geonames_fetcher.get_continent_subdivisions(countries)

    # Add subdivisions from geonames that do not exist in iso.org
    continent_subdivisions = {}
    for continent in geonames_continent_subdivisions:
        iso_org_continent_subdivisions_code = [sb.code for sb in iso_org_continent_subdivisions[continent]]
        for subdivision in geonames_continent_subdivisions[continent]:
            if subdivision.code not in iso_org_continent_subdivisions_code:
                continent_subdivisions.setdefault(continent, []).append(subdivision)

    # Add all iso.org subdivisions
    for continent in iso_org_continent_subdivisions:
        continent_subdivisions.setdefault(continent, []).extend(iso_org_continent_subdivisions[continent])

    # Write subdivisions by continent
    for continent in continent_subdivisions:
        write_file_from_dataclass(continent, sort_subdivisions(continent_subdivisions[continent]))

    # Get crypto currencies from ifcmarkets
    crypto_currencies = sorted(crypto_currency_fetcher.get_crypto_currencies(), key=lambda currencies: currencies.code)

    # Write crypto currencies
    write_file_from_dataclass('crypto_currencies', crypto_currencies)

    # Get fiat currencies from iso.org
    fiat_currencies = iso_fetcher.get_currencies()

    # Get fiat currencies from geonames
    country_fiat_currency_map = geonames_fetcher.get_currencies_by_country()

    # Filter fiat currencies not used on any country
    fiat_currencies = {fiat_currency for fiat_currency in fiat_currencies if
                       fiat_currency.code in country_fiat_currency_map.values()}

    fiat_currencies.update(iso_fetcher.get_deprecated_currencies())

    # Get all fiat currency iso codes
    fiat_currency_iso_codes = {currency.code for currency in fiat_currencies}

    # Write fiat currencies
    fiat_currencies = sorted(fiat_currencies, key=lambda currencies: currencies.code)
    write_file_from_dataclass('fiat_currencies', fiat_currencies)

    # Add fiat currency on each country
    for country in countries:
        currency_iso = country_fiat_currency_map.get(country.code)
        if currency_iso and currency_iso in fiat_currency_iso_codes:
            country.fiat_currency = country_fiat_currency_map.get(country.code)

    # Write countries
    countries.sort(key=lambda country: country.code)
    write_file_from_dataclass('countries', countries)

    # Get subdivision type by subdivision code
    subdivision_types = {}
    unique_types = set()
    for continent in continent_subdivisions:
        for subdivision in continent_subdivisions[continent]:
            subdivision_types[subdivision.code] = subdivision.type
            unique_types.add(subdivision.type.lower())

    # Write subdivision type enum
    write_file_from_lines([to_type_enum(line) for line in sorted(unique_types)], 'subdivision_types_enum')
