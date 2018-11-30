from dtypes import Card, GameSet, BasicCard
import json
import random
import argparse


def main():
    parser = argparse.ArgumentParser()
    game_choices = [g.name.lower().replace('_', '') for g in GameSet]
    game_choices.append('all')
    parser.add_argument('sets', nargs='+', choices=game_choices)
    args = parser.parse_args()
    with open('res/cards.json') as f:
        data = json.load(f)
        all_cards = [Card.from_json(**d) for d in data]
        possible_cards = [c for c in all_cards if can_pick_card(c) and is_set_in_args(c.game_set, args.sets)]
        cards = random.sample(possible_cards, 10)
        for card in cards:
            print(card)


def is_set_in_args(game_set, sets):
    if 'all' in sets:
        return True
    for s in sets:
        if s.lower().startswith(game_set.lower().replace(' ', '')):
            return True


def can_pick_card(card):
    return card.in_supply and card.name.lower() not in [c.name.lower() for c in BasicCard]

if __name__ == '__main__':
    main()
