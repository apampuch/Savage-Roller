from decks import PlayingCardDeck

# return this thing to return cards
# main_card is the card actually used
# count is the index of the card in the deck, mostly here so we don't have to return multiple things
# other_cards is the cards not used
# tactician_cards are handled by tactician
class CharacterCardContainer:
    def __init__(self, main_card, count):
        self.main_card = main_card
        self.count = count
        self.other_cards = []
        self.tactician_cards = []

'''
How the order of operations of all edges/hindrances works:

Code looks through all edges.
If hesitant is found, do that; ignore quick and level headed. (The bot should also prevent you from adding quick and hesitant to the same character.)

Level headed takes priority. If found, it doesn't perform quick.
*maybe* it warns the user if a character has both quick and level headed, and draws at least one card below 6, and tells them to manually use /choose_card and /quick_redraw

Do tactician no matter what.
'''

def hesitant(deck: list[str], card_container: CharacterCardContainer):
    card_container.count += 1
    next_card = deck[card_container.count]

    card_rank = PlayingCardDeck.index(card_container.main_card)
    next_card_rank = PlayingCardDeck.index(next_card)

    # if either card is a joker, just go with that one, since even hesitant always takes the joker
    if card_rank in (0, 1):
        card_container.main_card = PlayingCardDeck[card_rank]
        card_container.other_cards.append(PlayingCardDeck[next_card_rank])
    elif next_card_rank in (0, 1):
        card_container.main_card = PlayingCardDeck[next_card_rank]
        card_container.other_cards.append(PlayingCardDeck[card_rank])
    else:
        card_container.main_card = PlayingCardDeck[max(card_rank, next_card_rank)]
        card_container.other_cards.append(PlayingCardDeck[min(card_rank, next_card_rank)])

def quick(deck: list[str], card_container: CharacterCardContainer):
    # while the card 5 or lower
    while card_container.main_card[1] in ('5','4','3','2') and card_container.count < len(deck):
        card_container.other_cards.append(card_container.main_card)
        card_container.count += 1
        card_container.main_card = deck[card_container.count]

def levelheaded(deck: list[str], card_container: CharacterCardContainer):
    card_container.count += 1
    next_card = deck[card_container.count]

    card_rank = PlayingCardDeck.index(card_container.main_card)
    next_card_rank = PlayingCardDeck.index(next_card)

    card_container.main_card = PlayingCardDeck[min(card_rank, next_card_rank)]
    card_container.other_cards.append(PlayingCardDeck[max(card_rank, next_card_rank)])

def levelheaded_imp(deck: list[str], card_container: CharacterCardContainer) :
    card_container.count += 1
    next_card = deck[card_container.count]
    card_container.count += 1
    next_next_card = deck[card_container.count]

    all_cards_ranks = sorted([PlayingCardDeck.index(card_container.main_card), PlayingCardDeck.index(next_card), PlayingCardDeck.index(next_next_card)])
    all_cards = [PlayingCardDeck[x] for x in all_cards_ranks]

    card_container.main_card = all_cards[0]
    card_container.other_cards = all_cards[1:]

def tactician(deck: list[str], card_container: CharacterCardContainer):
    card_container.count += 1
    card_container.tactician_cards.append(deck[count])

def tactician_imp(deck: list[str], card_container: CharacterCardContainer):
    card_container.count += 1
    card_container.tactician_cards.append(deck[count])
    card_container.count += 1
    card_container.tactician_cards.append(deck[count])
