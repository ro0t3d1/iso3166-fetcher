from dataclasses import dataclass


@dataclass
class CountryEnum:
    code: str
    name: str
    continent: str

    def to_java_enum(self):
        return '{0}("{1}", {2}),\n'.format(self.code, self.name, self.continent)


@dataclass
class SubdivisionEnum:
    code: str
    name: str
    type: str
    parent: str
    country: CountryEnum

    def to_java_enum(self):
        return '{0}("{1}", {2}, {3}),\n'.format(self.code.replace('-', '_'), self.name,
                                                to_type(self.type), self.parent.replace('-', '_'))


def to_type_enum(type):
    return "{0}(\"{1}\"),\n".format(to_type(type), type.title())


def to_type(type):
    return type.upper().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace(',', '')
