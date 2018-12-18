import re
from enum import Enum


class Card:
    def __init__(self, name, category, types, game_set, cost, text, special_can_pick=False):
        self.name = name
        self.category = category
        self.types = types
        self.game_set = game_set
        self.cost = cost
        self.text = text
        self.in_supply = (self.category == 'Card' and 'This is not in the Supply' not in self.text and
                          all(CardType.is_in_supply(t) for t in self.types))
        self.is_basic = self.name.lower() in [c.name.lower() for c in BasicCard]
        self.can_pick = special_can_pick or (self.in_supply and not self.is_basic)
        self.encoded_name = self.name.replace(' ', '_').replace('/', '_').replace("'", '%27')

    @classmethod
    def from_json(cls, **json):
        props = dict(json)
        props.pop('in_supply')
        props.pop('is_basic')
        props.pop('can_pick')
        props.pop('encoded_name')
        props['game_set'] = GameSet.for_name(props['game_set'])
        props['cost'] = Cost(**props['cost'])
        return cls(**props)

    def __str__(self):
        return '%s (%s), %s, (%s), %s' % (self.name, self.category, self.game_set, ', '.join(self.types), self.cost)

    def __json__(self):
        return self.__dict__


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

    def __json__(self):
        return self.__dict__


class GameSet(Enum):
    BASE = 'Base', None, False
    BASE_1E = 'Base', 1
    BASE_2E = 'Base', 2
    INTRIGUE = 'Intrigue', None, False
    INTRIGUE_1E = 'Intrigue', 1
    INTRIGUE_2E = 'Intrigue', 2
    SEASIDE = 'Seaside'
    ALCHEMY = 'Alchemy'
    PROSPERITY = 'Prosperity'
    CORNUCOPIA = 'Cornucopia'
    HINTERLANDS = 'Hinterlands'
    DARK_AGES = 'Dark Ages'
    GUILDS = 'Guilds'
    ADVENTURES = 'Adventures'
    EMPIRES = 'Empires'
    NOCTURNE = 'Nocturne'
    RENAISSANCE = 'Renaissance'
    PROMO = 'Promo', None, False

    def __init__(self, set_name, edition=None, complete=True):
        self.set_name = set_name
        self.full_set_name = set_name + ((' %dE' % edition) if edition else '')
        self.complete = complete

    def contains(self, card):
        return self.full_set_name.startswith(card.game_set.full_set_name)

    def as_arg(self):
        return self.full_set_name.lower().replace(' ', '')

    def __str__(self):
        return self.set_name

    def __json__(self):
        return self.full_set_name

    @classmethod
    def for_arg(cls, arg):
        for game_set in cls:
            if game_set.as_arg() == arg:
                return game_set
        return None

    @classmethod
    def for_name(cls, name):
        for game_set in cls:
            if game_set.full_set_name == name:
                return game_set
        return None

    @classmethod
    def complete_sets(cls):
        return [g for g in GameSet if g.complete]


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
    POTION = 9


class CardType(Enum):
    ACTION = 0, True
    TREASURE = 1, True
    VICTORY = 2, True
    CURSE = 3, True
    ATTACK = 4, True
    DURATION = 5, True
    REACTION = 6, True
    CASTLE = 7, False
    DOOM = 8, True
    FATE = 9, True
    GATHERING = 10, True
    HEIRLOOM = 11, False
    KNIGHT = 12, False
    LOOTER = 13, True
    NIGHT = 14, True
    PRIZE = 15, False
    RESERVE = 16, True
    RUINS = 17, False
    SHELTER = 18, False
    SPIRIT = 19, False
    TRAVELLER = 20, True
    ZOMBIE = 21, False

    def __init__(self, value, in_supply):
        self.in_supply = in_supply

    @classmethod
    def is_in_supply(cls, card_type):
        for t in CardType:
            if t.name.lower() == card_type.lower():
                return t.in_supply
        return False


class SpecialTypeCard(Enum):
    KNIGHTS = Card('Knights', 'Card', ['Action', 'Attack', 'Knight'], GameSet.DARK_AGES, Cost(5), '', True)
    CASTLES = Card('Castles', 'Card', ['Victory', 'Castle'], GameSet.EMPIRES, Cost(3), '', True)


class SplitPileCard(Enum):
    ENCAMPMENT_PLUNDER = Card('Encampment/Plunder', 'Card', ['Action'], GameSet.EMPIRES, Cost(2), '', True)
    PATRICIAN_EMPORIUM = Card('Patrician/Emporium', 'Card', ['Action'], GameSet.EMPIRES, Cost(2), '', True)
    SETTLERS_BUSTLING_VILLAGE = Card('Settlers/Bustling Village', 'Card', ['Action'], GameSet.EMPIRES, Cost(2), '',
                                     True)
    CATAPULT_ROCKS = Card('Catapult/Rocks', 'Card', ['Action', 'Attack'], GameSet.EMPIRES, Cost(3), '', True)
    GLADIATOR_FORTUNE = Card('Gladiator/Fortune', 'Card', ['Action'], GameSet.EMPIRES, Cost(3), '', True)
    SAUNA_AVANTO = Card('Sauna/Avanto', 'Card', ['Action'], GameSet.PROMO, Cost(4), '', True)
