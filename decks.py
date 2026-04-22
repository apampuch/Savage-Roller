DECK_OF_CARDS = ["RJ", "BJ"]
DECK_OF_TAROTS = []

for rank in ("A", "K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2"):
    for suit in ("S", "H", "D", "C"):
        DECK_OF_CARDS.append(suit + rank)

PlayingCardDeck = tuple(DECK_OF_CARDS)
