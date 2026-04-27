from decks import PlayingCardDeck
from initiative_list import Character, InitiativeList

def hesitant(init_list: InitiativeList, char: Character) -> None:
    old_card = char.main_card
    new_card = init_list.draw_card()

    old_rank = PlayingCardDeck.index(old_card)
    new_rank = PlayingCardDeck.index(new_card)

    # if either card is a joker, just go with that one, 
    # since even hesitant always takes the joker
    if old_rank in (0, 1):
        char.main_card = PlayingCardDeck[old_rank]
        char.unused_cards.append(PlayingCardDeck[new_rank])
    elif new_rank in (0, 1):
        char.main_card = PlayingCardDeck[new_rank]
        char.unused_cards.append(PlayingCardDeck[old_rank])
    else:
        char.main_card = PlayingCardDeck[max(old_rank, new_rank)]
        char.unused_cards.append(PlayingCardDeck[min(old_rank, new_rank)])

def quick(init_list: InitiativeList, char: Character) -> None:
    # while the card 5 or lower
    while char.main_card[1] in ('5','4','3','2'):
        char.unused_cards.append(char.main_card)
        char.main_card = init_list.draw_card()

def levelheaded(init_list: InitiativeList, char: Character) -> None:
    old_card = char.main_card
    new_card = init_list.draw_card()

    old_rank = PlayingCardDeck.index(old_card)
    new_rank = PlayingCardDeck.index(new_card)

    char.main_card = PlayingCardDeck[min(old_rank, new_rank)]
    char.unused_cards.append(PlayingCardDeck[max(old_rank, new_rank)])

def levelheaded_imp(init_list: InitiativeList, char: Character) -> None:
    old_card = char.main_card
    new_card = init_list.draw_card()
    fnl_card = init_list.draw_card()

    old_rank = PlayingCardDeck.index(old_card)
    new_rank = PlayingCardDeck.index(new_card)
    fnl_rank = PlayingCardDeck.index(fnl_card)

    all_cards_ranks = sorted([old_rank, new_rank, fnl_rank])
    all_cards = [PlayingCardDeck[x] for x in all_cards_ranks]

    char.main_card = all_cards[0]
    char.unused_cards += all_cards[1:]

def tactician(init_list: InitiativeList, char: Character) -> None:
    char.tactician_cards.append(init_list.draw_card())

def tactician_imp(init_list: InitiativeList, char: Character) -> None:
    char.tactician_cards.append(init_list.draw_card())
    char.tactician_cards.append(init_list.draw_card())
