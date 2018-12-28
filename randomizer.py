"""
This module contains Randomizer, used to generate random Dominion supplies with various randomization options,
and RandomizerParser, used to parse the Randomizer options from command line input.

"""

import argparse
import json
import os
import random
from collections import defaultdict
from dtypes import BasicCard, Card, CardType, GameSet, SpecialTypeCard, SplitPileCard


class Randomizer():
    """
    Randomizes Dominion cards from given sets and provides customization options including the number of cards, set
    weights or counts, included and excluded cards, filtered card types, and drawing events or landmarks.
    
    """

    def __init__(self, data_path, sets, number=10, weights=[], counts=[], include=[], exclude=[], filter_types=[],
                 n_events=0, n_landmarks=0):
        """
        Creates a randomizer with given arguments.
        
        :param data_path: The cards.json file path.
        :type data_path: str
        :param sets: The names of the sets to randomize, optionally in argument form (i.e. base2e).
        :type sets: List[str]
        :param number: The total number of cards to pick, defaults to 10.
        :type number: int, optional
        :param weights: The weights to be applied to each set when randomly picking cards, defaults to an empty list.
        :type weights: List[int], optional
        :param counts: The counts of cards to pick from each set, defaults to an empty list.
        :type counts: List[int], optional
        :param include: The cards to include, optionally in argument form, defaults to an empty list.
        :type include: List[str], optional
        :param exclude: The cards to exclude, optionally in argument form, defaults to an empty list.
        :type exclude: List[str], optional
        :param filter_types: The card types to filter out before randomly picking cards, defaults to an empty list.
        :type filter_types: List[str], optional
        :param n_events: The number of events to pick, defaults to 0.
        :type n_events: int, optional
        :param n_landmarks: The number of landmarks to pick, defaults to 0.
        :type n_landmarks: int, optional
        """

        self.data_path = data_path
        self.sets = GameSet.complete_sets() if 'all' in sets else [GameSet.for_arg(set_arg) for set_arg in sets]
        self.number = int(number)
        self.weights = weights
        self.counts = counts
        self.include = include
        self.exclude = exclude
        self.filter_types = filter_types
        self.n_events = int(n_events)
        self.n_landmarks = int(n_landmarks)
        self.count = self.number - len(self.include)
        self.mode = 'weighted' if self.weights else 'counted' if self.counts else 'normal'
        self.cards = {}
        self.possible_cards = {}
        self.included_cards = []
        self.events = []
        self.landmarks = []
        self.possible_events = []
        self.possible_landmarks = []
        self.load_cards()
        self.add_inclusions()
        self.add_exclusions()

    def print_cards(self):
        """
        Prints the randomizeds cards, listed by set name.
        
        """

        cards = defaultdict(list)
        for game_set, set_cards in self.cards.items():
            cards[game_set.set_name].extend(set_cards)
        for game_set in sorted(cards.keys()):
            print(game_set)
            cards[game_set].sort(key=lambda c: c.name)
            for card in cards[game_set]:
                print('- %s (%s), %s' % (card.name, ', '.join(card.types), card.cost))
        self.print_non_cards(self.events, 'Events', True)
        self.print_non_cards(self.landmarks, 'Landmarks', False)

    def print_non_cards(self, card_list, label, print_cost):
        """
        Prints the given list of non-card cards (i.e. Events, Landmarks) with the given label.
        
        :param card_list: The cards to print.
        :type card_list: List[Card]
        :param label: The header to print the cards under.
        :type label: str
        :param print_cost: True to print the card cost, otherwise False
        :type print_cost: bool
        """

        if len(card_list) > 0:
            print(label)
            for card in card_list:
                if print_cost:
                    print('- %s, %s, %s' % (card.name, card.game_set, card.cost))
                else:
                    print('- %s, %s' % (card.name, card.game_set))

    def randomize(self):
        """
        Picks random cards based on the randomizer's parameters.
        
        """


        if self.mode == 'counted':
            counts = {self.sets[i]: self.counts[i] for i in range(len(self.sets))}
        else:
            if self.mode == 'normal':
                # weight set picks based on how many cards in each set
                weights = [len(set_cards) for game_set, set_cards in self.possible_cards.items()]
                set_picks = random.choices(self.sets, weights=weights, k=self.count)
            elif self.mode == 'weighted':
                set_picks = random.choices(self.sets, weights=self.weights, k=self.count)
            counts = defaultdict(int)
            for set_pick in set_picks:
                counts[set_pick] += 1
        cards = {game_set: self.randomize_set(game_set, count) for game_set, count in counts.items()}
        self.cards = defaultdict(list, cards)
        for card in self.included_cards:
            self.cards[card.game_set].append(card)
        self.events = random.sample(self.possible_events, self.n_events)
        self.landmarks = random.sample(self.possible_landmarks, self.n_landmarks)

    def randomize_set(self, game_set, count):
        """
        Picks the given count of cards from the given game set.
        
        :param game_set: The game set to pick cards from in the possible card list.
        :type game_set: GameSet
        :param count: The count of cards to pick.
        :type count: int
        :return: The list of random cards picked from the set.
        :rtype: List[Card]
        """ 

        return random.sample(self.possible_cards[game_set], k=count)

    def load_cards(self):
        """
        Loads cards from the data path and populates possible card lists.
        
        """

        with open(self.data_path) as f:
            data = json.load(f)
            self.all_cards = [Card.from_json(**d) for d in data]
        for game_set in self.sets:
            # less efficient than building by card.game_set but done to handle editioned sets
            self.possible_cards[game_set] = [c for c in self.all_cards
                                             if game_set.contains(c) and self.is_possible_card(c)]
        self.add_special_type_cards()
        self.remove_split_pile_cards()
        self.possible_events = self.get_non_cards('Event', self.n_events)
        self.possible_landmarks = self.get_non_cards('Landmark', self.n_landmarks)

    def get_non_cards(self, category, count):
        """
        Gets all possible cards of the given category, throwing an error if fewer than the given number exist.
        
        :param category: The card category to get.
        :type category: str
        :param count: The desired count of cards. Used to throw an error if not possible to get this amount.
        :type count: int
        :raises argparse.ArgumentTypeError: Throws an argparse error if fewer than the requested number of cards exist.
        :return: The list of possible cards of the given category.
        :rtype: List[Card]
        """

        card_list = [c for c in self.all_cards if c.category == category and self.any_set_contains(c)]
        if count > len(card_list):
            raise argparse.ArgumentTypeError('too few %ss available in given sets: requested %d' % (category, count))
        return card_list

    def any_set_contains(self, card):
        """
        Checks if any set in the randomizer contains the given card.
        
        :param card: The card to check for.
        :type card: Card
        :return: True if the card is contained by this randomizer's sets, otherwise False.
        :rtype: bool
        """

        return any(game_set.contains(card) for game_set in self.sets)

    def add_special_type_cards(self):
        """
        Adds special randomizer cards into the list of possible cards to pick.
        
        """

        for card in SpecialTypeCard:
            if card.value.game_set in self.sets:
                self.possible_cards[card.value.game_set].append(card.value)

    def remove_split_pile_cards(self):
        """
        Replaces the split pile cards with their corresponding split randomizer cards.
        
        """

        for split_card in SplitPileCard:
            if split_card.value.game_set in self.sets:
                card_splits = split_card.value.name.split('/')
                set_cards = self.possible_cards[split_card.value.game_set]
                set_cards[:] = [card for card in set_cards if card.name not in card_splits]

    def add_inclusions(self):
        """
        Adds the included cards and removes them from the possible card pool and adjusts pick counts if necessary.
        
        """

        for card in self.get_name_filtered_cards(self.include, '-i/--include'):
            self.included_cards.append(card)
            self.remove_card_from_pool(card)
        if self.counts:
            self.adjust_counts()

    def adjust_counts(self):
        """
        Decrements each set's pick count based on included cards' sets.
        
        """

        for card in self.included_cards:
            for i in range(len(self.sets)):
                if self.sets[i].contains(card):
                    self.counts[i] -= 1

    def add_exclusions(self):
        """
        Removes the excluded cards from the possible card pool.
        
        """

        for card in self.get_name_filtered_cards(self.exclude, '-x/--exclude'):
            self.remove_card_from_pool(card)

    def remove_card_from_pool(self, card):
        """
        Removes the given card from the possible card pool.
        
        :param card: The card to remove from the pool.
        :type card: Card
        """

        for game_set in self.possible_cards:
            if game_set.contains(card):
                self.possible_cards[game_set].remove(card)
                break  # cards are unique, may exit function once found

    def get_name_filtered_cards(self, card_args, arg_hint):
        """
        Parses the given card arguments or throws an argparse error with the given hint if unable to find a card.
        
        :param card_args: The card arguments to parse.
        :type card_args: List[str]
        :param arg_hint: The argument hint to include in the error if necessary.
        :type arg_hint: str
        :raises argparse.ArgumentTypeError: Throws an error if the requested card could not be found.
        :return: The list of cards matching the card arguments.
        :rtype: List[Card]
        """

        cards = []
        for card_arg in card_args:
            found = False
            for card in self.all_cards:
                if card_arg == RandomizerParser.standardize_input(card.name):
                    cards.append(card)
                    found = True
            if not found:
                raise argparse.ArgumentTypeError('unable to find card specified via %s: %s' % (arg_hint, card_arg))
        return cards

    def is_possible_card(self, card):
        """
        Checks if the given card can be picked and is not type filtered.
        
        :param card: The card to check.
        :type card: Card
        :return: True if the card is a possible card for this randomizer, otherwise False.
        :rtype: bool
        """

        return card.can_pick and not Randomizer.in_type_filter(card, self.filter_types)

    @staticmethod
    def in_type_filter(card, types):
        """
        Checks if the given card has any of the given types.
        
        :param card: The card to check.
        :type card: Card
        :param types: The list of types to check for.
        :type types: List[str]
        :return: True if the card has any of the given types.
        :rtype: bool
        """

        return any(t.lower() in types for t in card.types) if types else False


class RandomizerParser():
    """
    An argument parser that parses the following arguments and converts them into a Randomizer instance.

    positional arguments:
        {base1e,base2e,intrigue1e,intrigue2e,seaside,alchemy,prosperity,cornucopia,hinterlands,darkages,guilds,
            adventures,empires,nocturne,renaissance,all}
                                Game sets to choose from, or all

    optional arguments:
        -h, --help            show this help message and exit
        -n NUMBER, --number NUMBER
                                Number of cards to pick, default 10
        -w WEIGHTS [WEIGHTS ...], --weights WEIGHTS [WEIGHTS ...]
                                Weights to be applied to each set when randomly
                                picking cards
        -c COUNTS [COUNTS ...], --counts COUNTS [COUNTS ...]
                                Counts of cards to pick from each set
        -i INCLUDE [INCLUDE ...], --include INCLUDE [INCLUDE ...]
                                Specific cards to include
        -x EXCLUDE [EXCLUDE ...], --exclude EXCLUDE [EXCLUDE ...]
                                Specific cards to exclude
        -f {action,treasure,victory,attack,duration,reaction,doom,fate,gathering,looter,night,reserve,traveller}
            [{TYPES} ...], --filter-types {TYPES} [{TYPES} ...]
                                Specific cards types to filter out before randomly
                                picking cards
        -e EVENTS, --events EVENTS
                                Number of events to pick
        -l LANDMARKS, --landmarks LANDMARKS
                                Number of landmarks to pick
    """

    def get_randomizer(self, data_path):
        """
        Construct a Randomizer instance from the parsed arguments and the given data path.
        
        :param data_path: The cards.json data path.
        :type data_path: str
        :return: A randomizer instance.
        :rtype: Randomizer
        """

        return Randomizer(data_path, self.args.sets, self.args.number, self.args.weights, self.args.counts,
                          self.args.include, self.args.exclude, self.args.filter_types, self.args.events,
                          self.args.landmarks)

    def parse_args(self):
        """
        Creates the argparse.ArgumentParser and parses and checks args.
        """

        self.parser = argparse.ArgumentParser()
        game_choices = [g.as_arg() for g in GameSet.complete_sets()]
        game_choices.append('all')
        self.parser.add_argument('sets', nargs='+', choices=game_choices, help='Game sets to choose from, or all')
        self.parser.add_argument('-n', '--number', type=int, default=10, help='Number of cards to pick, default 10')
        distribution_group = self.parser.add_mutually_exclusive_group()
        distribution_group.add_argument('-w', '--weights', nargs='+', type=float, default=[],
                                        help='Weights to be applied to each set when randomly picking cards')
        distribution_group.add_argument('-c', '--counts', nargs='+', type=int, default=[],
                                        help='Counts of cards to pick from each set')
        self.parser.add_argument('-i', '--include', nargs='+', type=RandomizerParser.standardize_input, default=[],
                                 help='Specific cards to include')
        self.parser.add_argument('-x', '--exclude', nargs='+', type=RandomizerParser.standardize_input, default=[],
                                 help='Specific cards to exclude')
        type_choices = [t.name.lower() for t in CardType if t.in_supply]
        type_choices.remove('curse')  # curse type only present on basic curse card
        self.parser.add_argument('-f', '--filter-types', nargs='+', choices=type_choices, default=[],
                                 help='Specific cards types to filter out before randomly picking cards')
        self.parser.add_argument('-e', '--events', type=int, default=0, help='Number of events to pick')
        self.parser.add_argument('-l', '--landmarks', type=int, default=0, help='Number of landmarks to pick')
        self.args = self.parser.parse_args()
        self.check_args()

    def check_edition_args(self, set_name):
        """
        Checks if the set args contain both editions of the given set name.
        Throws a parser error if not.
        
        :param set_name: The set name to check for both editions.
        :type set_name: str
        """

        first = set_name + '1e'
        second = set_name + '2e'
        if first in self.args.sets and second in self.args.sets:
            self.parser.error('must choose only one of %s, %s' % (first, second))

    def check_distribution_args(self, distribution_arg, error_hint):
        """
        Checks if the given distribution has the same number of entries as there are sets.
        Throws a parser error if not.
        
        :param dist_arg: The distribution argument to check.
        :type dist_arg: str
        """

        if distribution_arg and len(self.args.sets) != len(distribution_arg):
            self.parser.error('must have equal quantities of sets (%d) and %s (%d)' %
                              (len(self.args.sets), error_hint, len(distribution_arg)))

    # TODO: move parameter validation into Randomizer
    def check_args(self):
        """
        Checks for conflicting editions, invalid distribution counts, and invalid inclusion counts.
        """

        self.check_edition_args('base')
        self.check_edition_args('intrigue')
        self.check_distribution_args(self.args.weights, 'weights')
        self.check_distribution_args(self.args.counts, 'counts')
        if self.args.counts and sum(self.args.counts) != self.args.number:
            self.parser.error('counts must add up to %d' % self.args.number)
        if self.args.include and len(self.args.include) > self.args.number:
            self.parser.error('cannot have greater than %d cards defined via -i/--include' % self.args.number)

    @staticmethod
    def standardize_input(string):
        """
        Standardizes argument input by lowercasing and removing apostrophes and spaces.
        
        :param string: The string to standardize.
        :type string: str
        :return: The standardized string.
        :rtype: str
        """

        return string.replace("'", '').replace(' ', '').lower()


def main():
    """
    Parses randomizer args, creates a randomizer, and randomizes and prints cards.
    """

    json_path = os.path.join(os.path.dirname(__file__), 'res/cards.json')
    parser = RandomizerParser()
    parser.parse_args()
    randomizer = parser.get_randomizer(json_path)
    randomizer.randomize()
    randomizer.print_cards()

if __name__ == '__main__':
    main()
