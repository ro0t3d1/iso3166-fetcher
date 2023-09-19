from dataclasses import dataclass

replacements_for = {
    "ZA-GP": "ZA_GT",
    "ZA-KZN": "ZA_NL",
    "KZ-75": "KZ_ALA",
    "KZ-71": "KZ_AST",
    "KZ-79": "KZ_SHY",
    "KZ-19": "KZ_ALM",
    "KZ-11": "KZ_AKM",
    "KZ-15": "KZ_AKT",
    "KZ-23": "KZ_ATY",
    "KZ-63": "KZ_VOS",
    "KZ-47": "KZ_MAN",
    "KZ-59": "KZ_SEV",
    "KZ-61": "KZ_YUZ",
    "KZ-55": "KZ_PAV",
    "KZ-35": "KZ_KAR",
    "KZ-39": "KZ_KUS",
    "KZ-43": "KZ_KZY",
    "KZ-27": "KZ_ZAP",
    "KZ-31": "KZ_ZHA",
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
        if self.code in replacements_for:
            up_to_date = '{0}("{1}", {2}, {3}),\n'.format(self.code.replace('-', '_'), self.name,
                                                          to_type(self.type), self.parent.replace('-', '_'))
            return up_to_date + '{0}("{1}", {2}, {3}, {4}),\n'.format(replacements_for.get(self.code), self.name,
                                                                      to_type(self.type), self.parent.replace('-', '_'),
                                                                      self.code.replace('-', '_'))
        else:
            return '{0}("{1}", {2}, {3}),\n'.format(self.code.replace('-', '_'), self.name,
                                                    to_type(self.type), self.parent.replace('-', '_'))


def to_type_enum(type):
    return "{0}(\"{1}\"),\n".format(to_type(type), type.title())


def to_type(type):
    return type.upper().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace(',', '')
