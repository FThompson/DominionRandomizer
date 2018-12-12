import argparse
import json
import random
import numpy
from collections import defaultdict
from dtypes import BasicCard, Card, GameSet

def randomize():
    parser = argparse.ArgumentParser()
    game_choices = [g.get_arg_form() for g in GameSet]
    game_choices.append('all')
    parser.add_argument('sets', nargs='+', choices=game_choices)
    distribution_group = parser.add_mutually_exclusive_group()
    distribution_group.add_argument('-w', '--weights', nargs='+', type=float)
    distribution_group.add_argument('-c', '--counts', nargs='+', type=int)
    parser.add_argument('-i', '--include', nargs='+')
    args = parser.parse_args()
    # TODO: --include, --exclude, --filter_types
    # TODO: refactor
    if 'base1e' in args.sets and 'base2e' in args.sets:
        parser.error('must choose only one of base1e, base2e')
    if 'intrigue1e' in args.sets and 'intrigue2e' in args.sets:
        parser.error('must choose only one of intrigue1e, intrigue2e')
    if args.weights and len(args.sets) != len(args.weights):
        parser.error('must have equal quantities of sets (%d) and weights (%d)' % (len(args.sets), len(args.weights)))
    if args.counts and len(args.sets) != len(args.counts):
        parser.error('must have equal quantities of sets (%d) and counts (%d)' % (len(args.sets), len(args.counts)))
    if args.counts and sum(args.counts) != 10:
        parser.error('counts must add up to 10')
    if len(args.include) > 10:
        parser.error('cannot have greater than ten cards defined via -i/--include')
    with open('res/cards.json') as f:
        data = json.load(f)
        all_cards = [Card.from_json(**d) for d in data]
        possible_cards = [c for c in all_cards if can_pick_card(c) and is_card_in_args(c, args.sets)]
        cards = []
        for include in args.include:
            to_compare = include.replace("'", '').replace(' ', '').lower()
            found = False
            for card in possible_cards:
                if to_compare == card.name.replace("'", '').replace(' ', '').lower():
                    cards.append(card)
                    possible_cards.remove(card)
                    found = True
            if not found:
                parser.error('unable to find card specified via -i/--include: %s' % include)
        count_to_pick = 10 - len(args.include)
        distribution = args.weights or args.counts
        if distribution:
            set_distributions = {args.sets[i]: distribution[i] for i in range(len(args.sets))}
        if args.weights:
            # TODO: change weights based on included cards
            all_distributions = numpy.array([get_distribution(set_distributions, card) for card in possible_cards])
            weight_sum = all_distributions.sum()
            normalized_weights = [i / weight_sum for i in all_distributions]
            cards.extend(numpy.random.choice(possible_cards, size=count_to_pick, replace=False, p=normalized_weights))
        elif args.counts:
            possible_card_sets = defaultdict(list)
            for card in possible_cards:
                possible_card_sets[card.game_set].append(card)
            for card in cards:
                card_set = card.game_set.replace(' ', '').lower()
                for game_set, distribution in set_distributions.items():
                    if game_set.startswith(card_set):
                        set_distributions[game_set] -= 1  # TODO: serious refactor needed this is bad dup code
            for game_set in possible_card_sets.keys():
                count = get_set_distribution(set_distributions, game_set)
                set_cards = random.sample(possible_card_sets[game_set], count)
                cards.extend(set_cards)
        else:
            cards.extend(random.sample(possible_cards, count_to_pick))
        card_sets = defaultdict(list)
        for card in cards:
            card_sets[card.game_set].append(card)
        for game_set in sorted(card_sets.keys()):
            print(game_set)
            card_sets[game_set].sort(key=lambda c: c.name)
            for card in card_sets[game_set]:
                print('- %s (%s), %s' % (card.name, ', '.join(card.types), card.cost))


# TODO: custom dict with startswith get
# TODO: refactor these functions, maybe with added GameSet functionality
def get_distribution(distributions, card):
    set_name = get_card_set_arg_form(card)
    for game_set, distribution in distributions.items():
        if game_set.startswith(set_name):
            return distribution
    return 0


# TODO: refactor these functions
def get_set_distribution(distributions, game_set):
    game_set_name = game_set.replace(' ', '').lower()
    for game_set, distribution in distributions.items():
        if game_set.startswith(game_set_name):
            return distribution
    return 0


def is_card_in_args(card, sets):
    if 'all' in sets:
        return True
    set_name = get_card_set_arg_form(card)
    for s in sets:
        if s.startswith(set_name):  # startwith to account for edition sets
            return True
    return False


def get_card_set_arg_form(card):
    set_name = card.game_set + (card.edition if card.edition else '')
    return set_name.lower()


def can_pick_card(card):
    return card.in_supply and card.name.lower() not in [c.name.lower() for c in BasicCard]

if __name__ == '__main__':
    randomize()
