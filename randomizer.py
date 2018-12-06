import argparse
import json

import random
from dtypes import BasicCard, Card, GameSet


def randomize():
    parser = argparse.ArgumentParser()
    game_choices = [g.name.lower().replace('_', '') for g in GameSet]
    game_choices.append('all')
    parser.add_argument('sets', nargs='+', choices=game_choices)
    args = parser.parse_args()
    with open('res/cards.json') as f:
        data = json.load(f)
        all_cards = [Card.from_json(**d) for d in data]
        possible_cards = [c for c in all_cards if can_pick_card(c) and is_card_in_args(c, args.sets)]
        cards = random.sample(possible_cards, 10)
        cards.sort(key=lambda c: (c.game_set, c.name))
        for card in cards:
            print('- %s (%s), %s, %s' % (card.name, ', '.join(card.types), card.game_set, card.cost))


def is_card_in_args(card, sets):
    if 'all' in sets:
        return True
    set_name = card.game_set + (card.edition if card.edition else '')
    for s in sets:
        if s.lower().startswith(set_name.lower()):  # startwith to account for edition sets
            return True
    return False


def can_pick_card(card):
    return card.in_supply and card.name.lower() not in [c.name.lower() for c in BasicCard]

if __name__ == '__main__':
    randomize()
