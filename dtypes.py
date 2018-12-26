"""
This module contains various common Dominion types and enums.

"""

import re
from enum import Enum


class Card:
    """
    Represents a Dominion card, including non-card cards like Events.
    
    """

    def __init__(self, name, category, types, game_set, cost, text, special_can_pick=False):
        """
        Creates a card instance.
        
        :param name: The card's name.
        :type name: str
        :param category: The card's category (Card, Event, etc.).
        :type category: str
        :param types: The card's types (Attack, Duration, etc.).
        :type types: List[str]
        :param game_set: The card's game set.
        :type game_set: GameSet
        :param cost: The card's cost, including coins, potions, and debt.
        :type cost: Cost
        :param text: The card's text.
        :type text: str
        :param special_can_pick: True if this card has a special randomizer, otherwise False. Defaults to False.
        :param special_can_pick: bool, optional
        """

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
        """
        Parses a Card from the given json dictionary.
        
        :return: The card instance stored in the given json data.
        :rtype: Card
        """

        props = dict(json)
        props['game_set'] = GameSet.for_name(props['game_set'])
        props['cost'] = Cost(**props['cost'])
        return cls(**props)

    def __str__(self):
        """
        Formats this card like "Cellar (Card), Base, (Action), Cost(2C, 0P, 0D)"
        
        :return: The card's formatted data.
        :rtype: str
        """

        return '%s (%s), %s, (%s), %s' % (self.name, self.category, self.game_set, ', '.join(self.types), self.cost)

    def __json__(self):
        """
        Creates a dict of this card's data to be stored in a json file.
        
        :return: This card's data as a dict.
        :rtype: Dict[str, T]
        """

        return {'name': self.name, 'category': self.category, 'types': self.types, 'game_set': self.game_set,
                'cost': self.cost, 'text': self.text}


class Cost:
    """
    Represents a cost, consisting of coins, potions, and/or debt.
    
    """

    def __init__(self, coins=0, potions=0, debt=0, has_exception=False):
        """
        Creates a Cost instance.
        
        :param coins: The cost's coins component, defaults to 0
        :param coins: int, optional
        :param potions: The cost's potions component, defaults to 0
        :param potions: int, optional
        :param debt: The cost's debt component, defaults to 0
        :param debt: int, optional
        :param has_exception: True if the card's cost has an asterisk, defaults to False
        :param has_exception: bool, optional
        """

        self.coins = int(coins)
        self.potions = int(potions)
        self.debt = int(debt)
        self.has_exception = bool(has_exception)

    @classmethod
    def from_raw(cls, raw_cost):
        """
        Parses a cost from the given raw data string, as formatted in the Dominion Wiki.
        Possible formats:
        * {{Cost|2}}
        * {{Cost|4P}}
        * {{Cost|8||8}}
        * {{Cost| | |5}}
        
        :param raw_cost: The raw cost, in one of the above forms.
        :type raw_cost: str
        :return: The Cost object.
        :rtype: Cost
        """

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
        """
        Formats this cost like Cost(8C*, 0P, 0D).
        
        :return: The formatted cost string.
        :rtype: str
        """

        s = 'Cost('
        s += '%dC' % self.coins
        if self.has_exception:
            s += '*'
        s += ', %dP, %dD)' % (self.potions, self.debt)
        return s

    def __json__(self):
        """
        This cost's json encoded form.
        
        :return: The cost's attribute dictionary.
        :rtype: Dict[str, T]
        """

        return self.__dict__


class GameSet(Enum):
    """
    An enumeration of all Dominion game sets.
    Game sets with multiple editions have entries for each edition as well as the non-editioned name.
    """

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
        """
        Creates a game set with given name, edition, and completedness.
        
        :param set_name: The game set's name.
        :type set_name: str
        :param edition: The game set's edition, defaults to None
        :param edition: int, optional
        :param complete: True if the game set is a complete set, otherwise False, defaults to True
        :param complete: bool, optional
        """

        self.set_name = set_name
        self.full_set_name = set_name + ((' %dE' % edition) if edition else '')
        self.complete = complete

    def contains(self, card):
        """
        Checks if this game set contains the given card.
        
        :param card: The card to check for.
        :type card: Card
        :return: True if the card is in this set, otherwise False.
        :rtype: bool
        """

        # uses startswith to handle editioned sets properly
        return self.full_set_name.startswith(card.game_set.full_set_name)

    def as_arg(self):
        """
        Converts this set's name into argument form (no spaces, lowercase).
        
        :return: The set's name, in lowercase, without any spaces.
        :rtype: str
        """

        return self.full_set_name.lower().replace(' ', '')

    def __str__(self):
        """
        Returns this set's name without edition.
        
        :return: This set's name.
        :rtype: str
        """

        return self.set_name

    def __json__(self):
        """
        Returns this set's json form.
        
        :return: The game set's name including edition.
        :rtype: str
        """

        return self.full_set_name

    @classmethod
    def for_arg(cls, arg):
        """
        Gets the game set with the given argument form.
        
        :param arg: The arg to check for.
        :type arg: str
        :return: The game set if found, otherwise None.
        :rtype: GameSet
        """

        arg = arg.lower().replace(' ', '')
        for game_set in cls:
            if game_set.as_arg() == arg:
                return game_set
        return None

    @classmethod
    def for_name(cls, name):
        """
        Gets the game set with the given name.
        
        :param name: The name to check for.
        :type name: str
        :return: The game set if found, otherwise None.
        :rtype: GameSet
        """

        for game_set in cls:
            if game_set.full_set_name == name:
                return game_set
        return None

    @classmethod
    def complete_sets(cls):
        """
        Gets all complete sets.
        
        :return: A list of all complete game sets.
        :rtype: List[GameSet]
        """

        return [g for g in GameSet if g.complete]


class CardCategory(Enum):
    """
    An enumeration of card categories (Card, Event, etc.).
    
    """

    CARD = 0
    EVENT = 1
    LANDMARK = 2
    BOON = 3
    HEX = 4
    STATE = 5
    ARTIFACT = 6
    PROJECT = 7


class BasicCard(Enum):
    """
    An enumeration of basic cards that are used in all or most games.
    
    """

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
    """
    An enumeration of card types (Attack, Duration, etc.) and whether or not cards with each type are in the supply.
    
    """

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
        """
        Creates a card type.
        
        :param value: The enum index, used only for creating unique objects.
        :type value: int
        :param in_supply: True if cards of this type are in the supply, otherwise False.
                          If a card has any type where in_supply is False, then that card is not in the supply.
        :type in_supply: bool
        """

        self.in_supply = in_supply

    @classmethod
    def is_in_supply(cls, card_type):
        """
        Checks if the given card type is in the supply.
        
        :param card_type: The card type to check.
        :type card_type: str
        :return: True if the card type is in the supply, otherwise False.
        :rtype: bool
        """

        for t in CardType:
            if t.name.lower() == card_type.lower():
                return t.in_supply
        return False


class SpecialTypeCard(Enum):
    """
    An enumeration of special randomizer cards, which replace several unique cards of the same type (Knight, Castle).
    Drawing the randomizer for the entire type means the game should include the stack of unique cards of that type.
    """

    KNIGHTS = Card('Knights', 'Card', ['Action', 'Attack', 'Knight'], GameSet.DARK_AGES, Cost(5), '', True)
    CASTLES = Card('Castles', 'Card', ['Victory', 'Castle'], GameSet.EMPIRES, Cost(3), '', True)


class SplitPileCard(Enum):
    """
    An enumeration of special randomizer cards, which replace pairs of cards that exist only in split piles.
    Drawing the randomizer for the pair means the game should include both cards in a split pile stack.

    The types of each pair card listed below represent only the types from the top (first) card in the split pile.
    """

    ENCAMPMENT_PLUNDER = Card('Encampment/Plunder', 'Card', ['Action'], GameSet.EMPIRES, Cost(2), '', True)
    PATRICIAN_EMPORIUM = Card('Patrician/Emporium', 'Card', ['Action'], GameSet.EMPIRES, Cost(2), '', True)
    SETTLERS_BUSTLING_VILLAGE = Card('Settlers/Bustling Village', 'Card', ['Action'], GameSet.EMPIRES, Cost(2), '',
                                     True)
    CATAPULT_ROCKS = Card('Catapult/Rocks', 'Card', ['Action', 'Attack'], GameSet.EMPIRES, Cost(3), '', True)
    GLADIATOR_FORTUNE = Card('Gladiator/Fortune', 'Card', ['Action'], GameSet.EMPIRES, Cost(3), '', True)
    SAUNA_AVANTO = Card('Sauna/Avanto', 'Card', ['Action'], GameSet.PROMO, Cost(4), '', True)
