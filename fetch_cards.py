import argparse
import json
import os
import re
import shutil
import urllib.request
from argparse import ArgumentParser
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from dtypes import Card, Cost, GameSet, SpecialTypeCard, SplitPileCard


class CardFetcher:
    def fetch_cards(self):
        cards = []
        response = requests.get('http://wiki.dominionstrategy.com/index.php/List_of_cards?action=raw')
        raw_cards = response.content.decode('utf-8').split('\n|-\n')
        for raw_card in raw_cards[1:]:
            card = self.parse_card_data(raw_card)
            cards.append(card)
        self.cards = cards
        self.add_special_cards()

    def fetch_card_image(self, card):
        filepath = Path('res') / 'cards' / (card.encoded_name + '.jpg')
        if not filepath.exists():
            response = requests.get('http://wiki.dominionstrategy.com/index.php/File:%s.jpg' % card.encoded_name)
            soup = BeautifulSoup(response.content, 'html.parser')
            image_url = 'http://wiki.dominionstrategy.com/' + soup.select_one('#file a').get('href')
            temp_path, headers = urllib.request.urlretrieve(image_url)
            if not filepath.parent.exists():
                filepath.parent.mkdir()
            shutil.move(temp_path, filepath)

    def parse_card_data(self, raw_card):
        raw = re.split(r'\D\|\|\D', raw_card)
        name, category = self.get_name_and_category(raw[0])
        game_set = self.get_game_set(raw[1])
        types = self.get_types(raw[2])
        cost = self.get_cost(raw[3])
        text = raw[4].strip()
        return Card(name, category, types, game_set, cost, text)

    def get_name_and_category(self, raw):
        m = re.match(r'\|\{\{(.*?)\|(.*?)\}\}', raw)
        name = m.group(2)
        category = m.group(1)
        return name, category

    def get_game_set(self, raw):
        m = re.match(r'\[\[(.*?)\]\](, <abbr.+>([12]E)<)?', raw)
        game_set = m.group(1)
        edition = m.group(3)
        name = game_set + (' ' + edition if edition else '')
        return GameSet.for_name(name)

    def get_types(self, raw):
        return [x.strip() for x in raw.split('-')]

    def get_cost(self, raw):
        raw_cost = raw.split('|', 1)[1].strip()
        return Cost.from_raw(raw_cost)

    def add_special_cards(self):
        self.cards.extend([c.value for c in SpecialTypeCard])
        self.cards.extend([c.value for c in SplitPileCard])


class JSONBuiltinEncoder(json.JSONEncoder):
    def default(self, obj):  # pylint: disable=E0202
        if hasattr(obj, '__json__') and callable(getattr(obj, '__json__')):
            return obj.__json__()
        return json.JSONEncoder.default(self, obj)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--images', action='store_true')
    args = parser.parse_args()
    fetcher = CardFetcher()
    fetcher.fetch_cards()
    for card in fetcher.cards:
        if args.images:
            fetcher.fetch_card_image(card)
        print(card)
    json_path = os.path.join(os.path.dirname(__file__), 'res/cards.json')
    with open(json_path, 'w') as f:
        json.dump(fetcher.cards, f, cls=JSONBuiltinEncoder)
