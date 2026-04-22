from decks import PlayingCardDeck

def hesitant(deck: list[str], count: int, card: str) -> tuple[str, int]:
    card = deck[count]
    next_card = deck[count+1]

    card_rank = PlayingCardDeck.index(card)
    next_card_rank = PlayingCardDeck.index(next_card)
    
    return deck[max(card_rank, next_card_rank)], count + 1, []

def quick(deck: list[str], count: int, card: str) -> tuple[str, int]:
    while card[1] in ('5','4','3','2'):
        count += 1
        card = deck[count]

    return card, count, []

def levelheaded(deck: list[str], count: int, card: str) -> tuple[str, int]:
    card = deck[count]
    next_card = deck[count+1]

    card_rank = PlayingCardDeck.index(card)
    next_card_rank = PlayingCardDeck.index(next_card)

    return deck[min(card_rank, next_card_rank)], count + 1, []

def levelheaded_imp(deck: list[str], count: int, card: str) -> tuple[str, int]:
    card = deck[count]
    next_card = deck[count+1]
    next_next_card = deck[count+2]

    card_rank = PlayingCardDeck.index(card)
    next_card_rank = PlayingCardDeck.index(next_card)    
    next_next_card_rank = PlayingCardDeck.index(next_next_card)

    return deck[min(card_rank, next_card_rank, next_next_card_rank)], count + 2, []

def tactician(deck: list[str], count: int, card: str) -> tuple[str, int]:
    return deck[count+1], count + 1, [deck[count+1]]

def tactician_imp(deck: list[str], count: int, card: str) -> tuple[str, int]:
    pass
