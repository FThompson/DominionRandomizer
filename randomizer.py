import argparse
import json
import os

from isort.settings import default

import random
from collections import defaultdict
from dtypes import BasicCard, Card, CardType, GameSet


class Randomizer():
    def __init__(self, path, sets, number=10, weights=None, counts=None, include=None, exclude=None, filter_types=None):
        self.path = path
        self.sets = [GameSet.for_arg(set_arg) for set_arg in sets]
        self.number = number
        self.weights = weights
        self.counts = counts
        self.include = include
        self.exclude = exclude
        self.filter_types = filter_types
        self.count = self.number - (len(self.include) if self.include else 0)
        self.mode = 'weighted' if self.weights else 'counted' if self.counts else 'normal'
        self.cards = {}
        self.possible_cards = {}
        self.included_cards = []
        self.load_cards()
        self.add_inclusions()
        self.add_exclusions()

    def print_cards(self):
        # convert game sets to set names to combine editioned sets under one key
        cards = defaultdict(list)
        for game_set, set_cards in self.cards.items():
            cards[game_set.set_name].extend(set_cards)
        for game_set in sorted(cards.keys()):
            print(game_set)
            cards[game_set].sort(key=lambda c: c.name)
            for card in cards[game_set]:
                print('- %s (%s), %s' % (card.name, ', '.join(card.types), card.cost))

    def randomize(self):
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
        self.cards = {game_set: self.randomize_set(game_set, count) for game_set, count in counts.items()}
        for card in self.included_cards:
            if card.game_set not in self.cards:
                self.cards[card.game_set] = []
            self.cards[card.game_set].append(card)

    def randomize_set(self, game_set, count):
        return random.sample(self.possible_cards[game_set], k=count)

    def load_cards(self):
        with open(self.path) as f:
            data = json.load(f)
            self.all_cards = [Card.from_json(**d) for d in data]
            for game_set in self.sets:
                # less efficient than building by card.game_set but done to handle editioned sets
                self.possible_cards[game_set] = [c for c in self.all_cards
                                                 if game_set.contains(c) and self.is_possible_card(c)]

    def add_inclusions(self):
        for card in self.get_name_filtered_cards(self.include, '-i/--include'):
            self.included_cards.append(card)
            self.remove_card_from_pool(card)
        if self.counts:
            self.adjust_counts()
        if self.weights:
            self.adjust_weights()

    def adjust_counts(self):
        for card in self.included_cards:
            for i in range(len(self.sets)):
                if self.sets[i].contains(card):
                    self.counts[i] -= 1

    # TODO: reconsider, is this necessary? included cards can make weighting irrelevant in randomization
    def adjust_weights(self):
        sum_weights = sum(self.weights)
        mean_weight = sum_weights / self.number
        for card in self.included_cards:
            for i in range(len(self.sets)):
                if self.sets[i].contains(card):
                    self.weights[i] -= mean_weight

    def add_exclusions(self):
        for card in self.get_name_filtered_cards(self.exclude, '-x/--exclude'):
            self.remove_card_from_pool(card)

    def remove_card_from_pool(self, card):
        for game_set in self.possible_cards:
            if game_set.contains(card):
                self.possible_cards[game_set].remove(card)
                return  # cards are unique, may exit function once found

    def get_name_filtered_cards(self, card_args, arg_hint):
        cards = []
        if card_args:
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
        return Randomizer.can_pick_card(card) and not Randomizer.in_type_filter(card, self.filter_types)

    @staticmethod
    def can_pick_card(card):
        return card.in_supply and not card.is_basic

    @staticmethod
    def in_type_filter(card, types):
        return any(t.lower() in types for t in card.types) if types else False


class RandomizerParser():
    def __init__(self, data_path):
        self.data_path = data_path

    def get_randomizer(self):
        return Randomizer(self.data_path, self.args.sets, self.args.number, self.args.weights, self.args.counts,
                          self.args.include, self.args.exclude, self.args.filter_types)

    def parse_args(self):
        self.parser = argparse.ArgumentParser()
        game_choices = [g.as_arg() for g in GameSet if g.complete]
        game_choices.append('all')
        self.parser.add_argument('sets', nargs='+', choices=game_choices)
        self.parser.add_argument('-n', '--number', type=int, default=10)
        distribution_group = self.parser.add_mutually_exclusive_group()
        distribution_group.add_argument('-w', '--weights', nargs='+', type=float)
        distribution_group.add_argument('-c', '--counts', nargs='+', type=int)
        self.parser.add_argument('-i', '--include', nargs='+', type=RandomizerParser.standardize_input)
        self.parser.add_argument('-x', '--exclude', nargs='+', type=RandomizerParser.standardize_input)
        type_choices = [t.name.lower() for t in CardType]
        type_choices.remove('curse')  # curse is not a type on any non-basic card
        self.parser.add_argument('-f', '--filter-types', nargs='+', choices=type_choices)
        self.args = self.parser.parse_args()
        self.check_args()

    def check_edition_args(self, set_name):
        first = set_name + '1e'
        second = set_name + '2e'
        if first in self.args.sets and second in self.args.sets:
            self.parser.error('must choose only one of %s, %s' % (first, second))

    def check_distribution_args(self, dist_arg):
        if dist_arg and len(self.args.sets) != len(dist_arg):
            self.parser.error('must have equal quantities of sets (%d) and weights (%d)' %
                              (len(self.args.sets), len(dist_arg)))

    def check_args(self):
        self.check_edition_args('base')
        self.check_edition_args('intrigue')
        self.check_distribution_args(self.args.weights)
        self.check_distribution_args(self.args.counts)
        if self.args.counts and sum(self.args.counts) != self.args.number:
            self.parser.error('counts must add up to %d' % self.args.number)
        if self.args.include and len(self.args.include) > self.args.number:
            self.parser.error('cannot have greater than %d cards defined via -i/--include' % self.args.number)

    @staticmethod
    def standardize_input(string):
        return string.replace("'", '').replace(' ', '').lower()


if __name__ == '__main__':
    json_path = os.path.join(os.path.dirname(__file__), 'res/cards.json')
    parser = RandomizerParser(json_path)
    parser.parse_args()
    randomizer = parser.get_randomizer()
    randomizer.randomize()
    randomizer.print_cards()
