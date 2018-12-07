import re
from enum import Enum


class Card:
    def __init__(self, name, category, types, game_set, edition, cost, text):
        self.name = name
        self.category = category
        self.types = types
        self.game_set = game_set
        self.edition = edition
        self.cost = cost
        self.text = text
        self.in_supply = self.category == 'Card' and 'This is not in the Supply' not in self.text
        self.encoded_name = self.name.replace(' ', '_').replace("'", '%27')

    @classmethod
    def from_json(cls, **json):
        props = dict(json)
        props.pop('in_supply')
        props.pop('encoded_name')
        props['cost'] = Cost(**props['cost'])
        return cls(**props)

    def __str__(self):
        set_name = self.game_set
        if self.edition:
            set_name += ' ' + self.edition
        return '%s (%s), %s, (%s), %s' % (self.name, self.category, set_name, ', '.join(self.types), self.cost)


class Cost:
    def __init__(self, coins=0, potions=0, debt=0, has_exception=False):
        self.coins = int(coins)
        self.potions = int(potions)
        self.debt = int(debt)
        self.has_exception = bool(has_exception)

    @classmethod
    def from_raw(cls, raw_cost):
        m = re.match(r'\{\{Cost\|(\d+)(\*?)(P?)\}\}', raw_cost)  # e.g. {{Cost|5}} or {{Cost|5P}}
        if m:
            return cls(coins=m.group(1), potions=1 if m.group(3) else 0, has_exception=m.group(2))
        m = re.match(r'\{\{Cost\|(\d+)\|\|(\d+)\}\}', raw_cost)  # e.g. {{Cost|4||3}}
        if m:
            return cls(coins=m.group(1), debt=m.group(2))
        m = re.match(r'\{\{Cost\| \| \|(\d+)\}\}', raw_cost)  # e.g. {{Cost| | |8}}
        if m:
            return cls(debt=m.group(1))
        return cls()  # zero expense Cost

    def __str__(self):
        s = 'Cost('
        s += '%dC' % self.coins
        if self.has_exception:
            s += '*'
        s += ', %dP, %dD)' % (self.potions, self.debt)
        return s


class GameSet(Enum):
    BASE_1E = 1
    BASE_2E = 2
    INTRIGUE_1E = 3
    INTRIGUE_2E = 4
    SEASIDE = 5
    ALCHEMY = 6
    PROSPERITY = 7
    CORNUCOPIA = 8
    HINTERLANDS = 9
    DARK_AGES = 10
    GUILDS = 11
    ADVENTURES = 12
    EMPIRES = 13
    NOCTURNE = 14
    RENAISSANCE = 15
    PROMO = 0

    def get_arg_form(self):
        return self.name.lower().replace('_', '')


class CardCategory(Enum):
    CARD = 0
    EVENT = 1
    LANDMARK = 2
    BOON = 3
    HEX = 4
    STATE = 5
    ARTIFACT = 6
    PROJECT = 7


class BasicCard(Enum):
    COPPER = 0
    SILVER = 1
    GOLD = 2
    ESTATE = 3
    DUCHY = 4
    PROVINCE = 5
    CURSE = 6
    PLATINUM = 7
    COLONY = 8
