import database
import edges
import random

from database import InitiativeList
from decks import PlayingCardDeck
from edges import CharacterCardContainer
from tabulate import tabulate

VALID_EDGES = set(["hesitant", "quick", "levelheaded",
               "levelheaded-imp", "tactician", "tactician-imp"])

# when trying to add one edge, lookup that edge by key
# if any other edges are in the value, don't add that edge
EXCLUSIVE_EDGES = {
    "hesitant": set(["quick", "levelheaded", "levelheaded-imp"]),
    "quick": set({"hesitant"}),
    "levelheaded": set({"hesitant", "levelheaded-imp"}),
    "levelheaded-imp": set(["hesitant", "levelheaded"]),
    "tactician": set(["tactician-imp"]),
    "tactician-imp": set(["tactician"])
}

def make_initiative_chart(init_list: InitiativeList) -> str:
    chart: str = ""
    table_headers = ["Name", "Bennies", "Card"]

    # append edges, tactician cards, unused cards if anyone has those
    if False:
        table_headers.append("Edges")

    if False:
        table_headers.append("Tactician Cards")

    if False:
        table_headers.append("Unused Cards")

    return chart


def exclusivity_check(edge: str, all_edges: set[str]) -> bool:
    # remove edge from all edges
    edge_test = all_edges - set([edge])
    
    # get edges that disqualify us
    dq_edges = EXCLUSIVE_EDGES[edge]

    # if any edges exist in both, return false, else return true
    return not edge_test & dq_edges


def add_character(name: str, guild: int, temp: bool = False) -> str:
    return database.insert_character(name, guild, temp)


def remove_character(name: str, guild: int) -> str:
    return database.delete_character(name, guild)


def add_edges_to_character(name: str, guild: int, edges_to_add: set[str]) -> str:
    # collision logic
    char_id, current_edges = database.get_edges_and_id(name, guild)

    # allow only edges that actually affect initiative
    invalid_edges = list(edges_to_add - VALID_EDGES)
    edges_to_add = edges_to_add & VALID_EDGES

    # build the array for executemany()
    # res[0] is char id
    rows = []
    for edge in edges_to_add:
        if edge not in current_edges and \
        exclusivity_check(edge, set(current_edges).union(set(edges_to_add))):
            rows.append( (char_id, edge) )
        else:
            invalid_edges.append(edge)

    database.insert_edges(rows)

    inserted = list(map(lambda x: x[1], rows))

    message = f"Added {", ".join(inserted)} to {name}."
    if len(invalid_edges) > 0:
        message += f"\nCould not add {", ".join(invalid_edges)} due to errors."

    return message

def remove_edges_from_character(name: str, guild: int, edges: list[str]):
    database.delete_edges_from_character(name, guild, edges)
    return f"Deleted {", ".join(edges)} from {name}"


def shuffle_deck(deck: list[str]):
    pass


def deal_cards():
    pass


def draw_cards(deck: list[str], char):
    pass
    # draw one card

    '''
    How the order of operations of all edges/hindrances works:

    Code looks through all character edges.
    If hesitant is found, do that; ignore quick and level headed. (The bot should also prevent you from adding quick and hesitant to the same character.)

    Level headed takes priority. If found, it doesn't perform quick.
    *maybe* it warns the user if a character has both quick and level headed, and draws at least one card below 6, and tells them to manually use /choose_card and /quick_redraw

    Do tactician no matter what.

    Only do improved, don't do both improved and regular.
    '''

    # if 'hesitant' in char.edges:
    #     edges.hesitant(deck, char.card, init_list.total_drawn)
    # else:
    #     if 'levelheaded-imp' in char.edges:
    #         edges.levelheaded_imp(deck, char.card, init_list.total_drawn)
    #     elif 'levelheaded' in char.edges:
    #         edges.levelheaded(deck, char.card, init_list.total_drawn)
    #     elif 'quick' in char.edges:
    #         edges.quick(deck, char.card, init_list.total_drawn)
    
    # if 'tactician-imp' in char.edges:
    #         edges.tactician_imp(deck, char.card, init_list.total_drawn)
    # elif 'tactician' in char.edges:
    #     edges.tactician(deck, char.card, init_list.total_drawn)


def next_round(guild: int, channel: int):
    pass

def fight(guild: int, channel: int):
    pass

def add_to_initiative(characters: list[str], guild: int, channel: int):
    pass


def remove_from_initiative(characters: list[str], guild: int, channel: int):
    pass
