from dataclasses import dataclass

replacements_of = {
    "IN_CT": "IN-CG",
    "IN_OR": "IN-OD",
    "IN_TG": "IN-TS",
    "IN_UT": "IN-UK",
    "KZ_ALA": "KZ-75",
    "KZ_AKM": "KZ-11",
    "KZ_AKT": "KZ-15",
    "KZ_ALM": "KZ-19",
    "KZ_AST": "KZ-71",
    "KZ_ATY": "KZ-23",
    "KZ_KAR": "KZ-35",
    "KZ_KUS": "KZ-39",
    "KZ_KZY": "KZ-43",
    "KZ_MAN": "KZ-47",
    "KZ_PAV": "KZ-55",
    "KZ_SEV": "KZ-59",
    "KZ_SHY": "KZ-79",
    "KZ_VOS": "KZ-63",
    "KZ_YUZ": "KZ-61",
    "KZ_ZAP": "KZ-27",
    "KZ_ZHA": "KZ-31",
    "NO_O1": "NO-30",
    "NO_O2": "NO-30",
    "NO_O4": "NO-34",
    "NO_O5": "NO-34",
    "NO_O6": "NO-30",
    "NO_O7": "NO-38",
    "NO_O8": "NO-38",
    "NO_O9": "NO-42",
    "NO_10": "NO-42",
    "NO_12": "NO-46",
    "NO_14": "NO-46",
    "NO_19": "NO-54",
    "NO_20": "NO-54",
    "ZA_GT": "ZA-GP",
    "ZA_NL": "ZA-KZN",
}


@dataclass
class CountryEnum:
    code: str
    name: str
    continent: str

    def to_java_enum(self):
        return '{0}("{1}", {2}),\n'.format(self.code, self.name, self.continent)


@dataclass
class SubdivisionWithParentEnum:
    code: str
    name: str
    type: str
    parent: str
    country: CountryEnum

    def to_java_enum(self):
        if self.code in replacements_of.values():
            up_to_date = '{0}("{1}", {2}, {3}),\n'.format(self.code.replace('-', '_'), self.name,
                                                          to_type(self.type), self.parent.replace('-', '_'))

            for replacement in self.__get_keys_by_value(replacements_of, self.code):
                up_to_date += '{0}("{1}", {2}, {3}, {4}),\n'.format(replacement, self.name,
                                                                   to_type(self.type), self.parent.replace('-', '_'),
                                                                   self.code.replace('-', '_'))

            return up_to_date
        else:
            return '{0}("{1}", {2}, {3}),\n'.format(self.code.replace('-', '_'), self.name,
                                                    to_type(self.type), self.parent.replace('-', '_'))

    @staticmethod
    def __get_keys_by_value(dict, value):
        return [key for key, val in dict.items() if val == value]


def to_type_enum(type):
    return "{0}(\"{1}\"),\n".format(to_type(type), type.title())


def to_type(type):
    return type.upper().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace(',', '')
