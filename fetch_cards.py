"""
This module contains CardFetcher, which can be called via command line to fetch cards, and card images if the
-i/--images argument is present. Card data is saved into res/cards.json and card images are saved into res/cards/.

"""

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

from json_util import JSONUnderscoreEncoder
from dtypes import Card, Cost, GameSet, SpecialTypeCard, SplitPileCard


class CardFetcher:
    """
    Fetches Dominion card data and images from the Dominion Wiki.
    
    """

    def fetch_cards(self):
        """
        Fetches and parses all cards from the Dominion Wiki.
        Uses http://wiki.dominionstrategy.com/index.php/List_of_cards?action=raw.
        
        """

        cards = []
        response = requests.get('http://wiki.dominionstrategy.com/index.php/List_of_cards?action=raw')
        raw_cards = response.content.decode('utf-8').split('\n|-\n')
        for raw_card in raw_cards[1:]:  # skip data header line
            card = self.parse_card_data(raw_card)
            cards.append(card)
        self.cards = cards
        self.add_special_cards()

    def fetch_card_image(self, card):
        """
        Fetches a given card's image at maximum available resolution and saves it to res/cards/{name}.jpg.
        If the image already exists at that path, this function returns without doing anything.
        
        :param card: The card to fetch the image of.
        :type card: Card
        """

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
        """
        Parses a Card object from the given raw card data entry pulled from the Dominion Wiki.
        Card text is left in Wiki format and should not be rendered directly.
        
        :param raw_card: The raw card data entry.
        :type raw_card: str
        :return: The Card parsed from the data.
        :rtype: Card
        """

        raw = re.split(r'\D\|\|\D', raw_card)
        name, category = self.get_name_and_category(raw[0])
        game_set = self.get_game_set(raw[1])
        types = self.get_types(raw[2])
        cost = self.get_cost(raw[3])
        text = raw[4].strip()
        return Card(name, category, types, game_set, cost, text)

    def get_name_and_category(self, raw):
        """
        Parses the name and category from the given raw string.
        
        :param raw: The raw data part, like "|{{Card|Cellar}}".
        :type raw: str
        :return: The card's name and category as a tuple.
        :rtype: Tuple[str]
        """

        m = re.match(r'\|\{\{(.*?)\|(.*?)\}\}', raw)
        name = m.group(2)
        category = m.group(1)
        return name, category

    def get_game_set(self, raw):
        """
        Parses the game set and edition from the given raw string.
        
        :param raw: The raw data part, like "[[Base]], <abbr title="Only in First Edition">1E</abbr>".
        :type raw: str
        :return: The card's game set.
        :rtype: GameSet
        """

        m = re.match(r'\[\[(.*?)\]\](, <abbr.+>([12]E)<)?', raw)
        game_set = m.group(1)
        edition = m.group(3)
        name = game_set + (' ' + edition if edition else '')
        return GameSet.for_name(name)

    def get_types(self, raw):
        """
        Parses the card's types.
        
        :param raw: The raw data part, like "Action - Reaction".
        :type raw: str
        :return: The card's types as a list.
        :rtype: List[str]
        """

        return [x.strip() for x in raw.split('-')]

    def get_cost(self, raw):
        """
        Parses the card's cost, including coins, potions, and debt.
        
        :param raw: The raw data part, like "{{Cost|2}}".
        :type raw: str
        :return: The card's cost as a Cost object.
        :rtype: Cost
        """

        raw_cost = raw.split('|', 1)[1].strip()
        return Cost.from_raw(raw_cost)

    def add_special_cards(self):
        """
        Adds special randomizer cards and split pile randomizer cards to the card fetcher.
        These card objects are absent from the Dominion Wiki list of cards due to their special status.
        
        """

        self.cards.extend([c.value for c in SpecialTypeCard])
        self.cards.extend([c.value for c in SplitPileCard])


def main():
    """
    Runs the card fetcher and saves cards to res/cards.json.
    If the -i/--images argument is specified, the fetcher will also retrieve card images, saved to res/cards/*.jpg.
    
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--images', action='store_true', help='Fetch card images')
    args = parser.parse_args()
    fetcher = CardFetcher()
    fetcher.fetch_cards()
    for card in fetcher.cards:
        if args.images:
            fetcher.fetch_card_image(card)
        print(card)
    json_path = os.path.join(os.path.dirname(__file__), 'res/cards.json')
    with open(json_path, 'w') as f:
        json.dump(fetcher.cards, f, cls=JSONUnderscoreEncoder)
        
if __name__ == '__main__':
    main()
