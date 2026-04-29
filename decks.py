DECK_OF_CARDS = ["RJ", "BJ"]
DECK_OF_TAROTS = []

for rank in ("A", "K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2"):
    for suit in ("S", "H", "D", "C"):
        DECK_OF_CARDS.append(suit + rank)

PlayingCardDeck = tuple(DECK_OF_CARDS)

suit_dict = {
    "S": "♠",
    "H": "♥",
    "D": "♦",
    "C": "♣"
}

suit_dict_inverted = {v: k for k, v in suit_dict.items()}

"""
Changes from pure character format (SA, C2) to symbol format (♠A, ♣2)
"""
def char_to_symbol(card: str) -> str:
    suit: str = card[0]
    suit = suit_dict[suit]

    return suit + card[1:]


def symbol_to_Char(card: str) -> str:
    suit: str = card[0]
    suit = suit_dict_inverted[suit]

    return suit + card[1:]
