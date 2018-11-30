from dtypes import Card, Cost

import re
import requests
import json
from bs4 import BeautifulSoup


class CardFetcher:
    def fetch_cards(self):
        cards = []
        response = requests.get('http://wiki.dominionstrategy.com/index.php/List_of_cards?action=raw')
        raw_cards = response.content.decode('utf-8').split('\n|-\n')
        for raw_card in raw_cards[1:]:
            cards.append(self.parse_card_data(raw_card))
        self.cards = cards

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
        if edition:
            game_set += ' ' + edition
        return game_set

    def get_types(self, raw):
        return [x.strip() for x in raw.split('-')]

    def get_cost(self, raw):
        raw_cost = raw.split('|', 1)[1].strip()
        return Cost.from_raw(raw_cost)


if __name__ == '__main__':
    fetcher = CardFetcher()
    fetcher.fetch_cards()
    for card in fetcher.cards:
        print(card)
    with open('res/cards.json', 'w') as f:
        json.dump(fetcher.cards, f, default=lambda x: x.__dict__)
