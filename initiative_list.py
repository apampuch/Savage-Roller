import json
import database

from dataclasses import dataclass, field
from decks import PlayingCardDeck
from tabulate import tabulate
from random import shuffle

@dataclass
class InitiativeList:
    deck: list[str] = field(default_factory=list)
    _characters: list[Character] = field(default_factory=list)
    round_count: int = 0

    @property
    def characters(self):
        return tuple(self._characters)

    # use these functions to keep shit sorted
    def add_character(self, char):
        self._characters.append(char)
        self.sort_characters()
    
    def sort_characters(self):
        self._characters = sorted(self._characters, key=lambda x: PlayingCardDeck.index(x.main_card))

    def remove_character(self, char):
        self._characters.remove(char)

    def make_initiative_chart(self) -> str:
        tab_dict = {}
        for key in ["Name", "Card", "Bennies", "Edges", "Unused", "Tactician"]:
            tab_dict[key] = []

        for char in self.characters:
            char.insert_into_tabulate(tab_dict)

        # delete any columns with unused values
        if all(map(lambda c: len(c.edges) == 0, self.characters)):
            del tab_dict["Edges"]
        if all(map(lambda c: len(c.unused_cards) == 0, self.characters)):
            del tab_dict["Unused"]
        if all(map(lambda c: len(c.tactician_cards) == 0, self.characters)):
            del tab_dict["Tactician"]

        return tabulate(tab_dict, headers="keys", tablefmt="simple")

    def shuffle_deck(self, full_shuffle = False):
        # if full shuffle, shuffle a full new deck of cards
        # if not, only shuffle from cards that not attached to characters in some way
        if full_shuffle:
            self.deck = list(PlayingCardDeck)
        else:
            cards_already_out = [card for char in self.characters 
            for card in ([char.main_card] + char.unused_cards + char.tactician_cards)]

            self.deck = list(set(PlayingCardDeck) - set(cards_already_out))

        shuffle(self.deck)

    def draw_card(self):
        # check if we're at the end of the deck

        # if we are, shuffle the deck, 
        if len(self.deck) == 0:
            self.shuffle_deck()

        # pop a card
        return self.deck.pop(0)

    def update_db(self, guild, channel):
        # build character info list
        character_info = []
        # character info is a list with list of the following, in order:
        # name, main_card, unused_cards, tactician_cards
        # unused_cards and tactician_cards must be converted to json with dumps
        names = []
        for char in self.characters:
            info = []

            names.append(char.name)
            info.append(char.main_card)
            info.append(json.dumps(char.unused_cards))
            info.append(json.dumps(char.tactician_cards))

            character_info.append(info)


        database.update_list(names, character_info, guild, channel, self.deck, self.round_count)

@dataclass
class Character:
    name: str
    main_card: str
    bennies: int = 0
    edges: list[str] = field(default_factory=list)
    unused_cards: list[str] = field(default_factory=list)
    tactician_cards: list[str] = field(default_factory=list)

    def insert_into_tabulate(self, tab_dict: dict):
        tab_dict["Name"].append(self.name)
        tab_dict["Card"].append(self.main_card)
        tab_dict["Bennies"].append(self.bennies)
        tab_dict["Edges"].append(", ".join(self.edges))
        tab_dict["Unused"].append(", ".join(self.unused_cards))
        tab_dict["Tactician"].append(", ".join(self.tactician_cards))
