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
        for key in ["Name", "Card", "Bennies", "Edges", "Unused Cards", "Tactician Cards"]:
            tab_dict[key] = []

        for char in self.characters:
            char.insert_into_tabulate(tab_dict)

        # delete any columns with unused values
        if all(map(lambda c: len(c.edges) == 0, self.characters)):
            del tab_dict["Edges"]
        if all(map(lambda c: len(c.unused_cards) == 0, self.characters)):
            del tab_dict["Unused Cards"]
        if all(map(lambda c: len(c.tactician_cards) == 0, self.characters)):
            del tab_dict["Tactician Cards"]

        return tabulate(tab_dict, headers="keys", tablefmt="simple_grid")

    def shuffle_deck(self):
        # do not shuffle cards already out
        # call this function with everyone in init_list having no cards
        # to get a clean, full deck
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
        tab_dict["Unused Cards"].append(", ".join(self.unused_cards))
        tab_dict["Tactician Cards"].append(", ".join(self.tactician_cards))
