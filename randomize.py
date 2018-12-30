"""
This module contains the command-line interface for the Dominion randomizer.

"""


import argparse
import os
from dtypes import CardType, GameSet
from randomizer import Randomizer


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
        self.parser.add_argument('-i', '--include', nargs='+', default=[], help='Specific cards to include')
        self.parser.add_argument('-x', '--exclude', nargs='+', default=[], help='Specific cards to exclude')
        type_choices = [t.name.lower() for t in CardType if t.in_supply]
        type_choices.remove('curse')  # curse type only present on basic curse card
        self.parser.add_argument('-f', '--filter-types', nargs='+', choices=type_choices, default=[],
                                 help='Specific cards types to filter out before randomly picking cards')
        self.parser.add_argument('-e', '--events', type=int, default=0, help='Number of events to pick')
        self.parser.add_argument('-l', '--landmarks', type=int, default=0, help='Number of landmarks to pick')
        self.args = self.parser.parse_args()


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