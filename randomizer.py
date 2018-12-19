import argparse
import json
import os
import random
from collections import defaultdict
from dtypes import BasicCard, Card, CardType, GameSet, SpecialTypeCard, SplitPileCard


class Randomizer():
    def __init__(self, data_path, sets, number=10, weights=None, counts=None, include=None, exclude=None,
                 filter_types=None, n_events=0, n_landmarks=0):
        self.data_path = data_path
        self.sets = GameSet.complete_sets() if 'all' in sets else [GameSet.for_arg(set_arg) for set_arg in sets]
        self.number = number
        self.weights = weights
        self.counts = counts
        self.include = include
        self.exclude = exclude
        self.filter_types = filter_types
        self.n_events = n_events
        self.n_landmarks = n_landmarks
        self.count = self.number - (len(self.include) if self.include else 0)
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
        # convert game sets to set names to combine editioned sets under one key
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
        if len(card_list) > 0:
            print(label)
            for card in card_list:
                if print_cost:
                    print('- %s, %s, %s' % (card.name, card.game_set, card.cost))
                else:
                    print('- %s, %s' % (card.name, card.game_set))

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
        cards = {game_set: self.randomize_set(game_set, count) for game_set, count in counts.items()}
        self.cards = defaultdict(list, cards)
        for card in self.included_cards:
            self.cards[card.game_set].append(card)
        self.events = random.sample(self.possible_events, self.n_events)
        self.landmarks = random.sample(self.possible_landmarks, self.n_landmarks)

    def randomize_set(self, game_set, count):
        return random.sample(self.possible_cards[game_set], k=count)

    def load_cards(self):
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
        card_list = [c for c in self.all_cards if c.category == category and self.any_set_contains(c)]
        if count > len(card_list):
            raise argparse.ArgumentTypeError('too few %ss available in given sets: requested %d' % (category, count))
        return card_list

    def any_set_contains(self, card):
        return any(game_set.contains(card) for game_set in self.sets)

    def add_special_type_cards(self):
        for card in SpecialTypeCard:
            if card.value.game_set in self.sets:
                self.possible_cards[card.value.game_set].append(card.value)

    def remove_split_pile_cards(self):
        for split_card in SplitPileCard:
            if split_card.value.game_set in self.sets:
                card_splits = split_card.value.name.split('/')
                set_cards = self.possible_cards[split_card.value.game_set]
                set_cards[:] = [card for card in set_cards if card.name not in card_splits]

    def add_inclusions(self):
        for card in self.get_name_filtered_cards(self.include, '-i/--include'):
            self.included_cards.append(card)
            self.remove_card_from_pool(card)
        if self.counts:
            self.adjust_counts()

    def adjust_counts(self):
        for card in self.included_cards:
            for i in range(len(self.sets)):
                if self.sets[i].contains(card):
                    self.counts[i] -= 1

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
        return card.can_pick and not Randomizer.in_type_filter(card, self.filter_types)

    @staticmethod
    def in_type_filter(card, types):
        return any(t.lower() in types for t in card.types) if types else False


class RandomizerParser():
    def get_randomizer(self, data_path):
        return Randomizer(data_path, self.args.sets, self.args.number, self.args.weights, self.args.counts,
                          self.args.include, self.args.exclude, self.args.filter_types, self.args.events,
                          self.args.landmarks)

    def parse_args(self):
        self.parser = argparse.ArgumentParser()
        game_choices = [g.as_arg() for g in GameSet.complete_sets()]
        game_choices.append('all')
        self.parser.add_argument('sets', nargs='+', choices=game_choices)
        self.parser.add_argument('-n', '--number', type=int, default=10)
        distribution_group = self.parser.add_mutually_exclusive_group()
        distribution_group.add_argument('-w', '--weights', nargs='+', type=float)
        distribution_group.add_argument('-c', '--counts', nargs='+', type=int)
        self.parser.add_argument('-i', '--include', nargs='+', type=RandomizerParser.standardize_input)
        self.parser.add_argument('-x', '--exclude', nargs='+', type=RandomizerParser.standardize_input)
        type_choices = [t.name.lower() for t in CardType if t.in_supply]
        self.parser.add_argument('-f', '--filter-types', nargs='+', choices=type_choices)
        self.parser.add_argument('-e', '--events', type=int, default=0)
        self.parser.add_argument('-l', '--landmarks', type=int, default=0)
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
    parser = RandomizerParser()
    parser.parse_args()
    randomizer = parser.get_randomizer(json_path)
    randomizer.randomize()
    randomizer.print_cards()
