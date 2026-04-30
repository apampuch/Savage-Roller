import database
from decks import PlayingCardDeck, char_to_symbol
import edges

from initiative_list import Character, InitiativeList
from json import dumps, loads

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


def exclusivity_check(edge: str, all_edges: set[str]) -> bool:#
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


def rename_character(old_name: str, new_name: str, guild: int) -> str:
    return database.change_char_name(old_name, new_name, guild)


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

"""
Helper function.
"""
def get_init_list(guild: int, channel: int, sort_init=True) -> InitiativeList:
    init_row, char_rows = database.get_initiative_list_and_characters(guild, channel)

    # make character and init list objects
    init_list = InitiativeList(
        _characters=[],
        deck=loads(init_row[0]),
        round_count=init_row[1]
    )

    # sort the characters after because we're adding several manually
    # do not add characters like this btw
    # I can do it because I'm smart and special and you're not
    for row in char_rows:
        init_list._characters.append(
            Character(
                name=row[0],
                main_card=row[1],
                bennies=row[2],
                edges=loads(row[3]),
                unused_cards=loads(row[4]) if row[4] is not None else [],
                tactician_cards=loads(row[5]) if row[4] is not None else []
            )
        )

    # note that in several cases we don't want to sort the characters
    # such as when we're getting an init list that hasn't been dealt yet
    if sort_init:
        init_list.sort_characters()
    
    return init_list


def fight(characters: list[str], guild: int, channel: int) -> str:
    # make a new list
    database.new_list(guild, channel)

    # add characters to it
    database.insert_into_list(characters, guild, channel)

    # deal cards to each character
    chart: str = next_round(guild, channel)

    if len(characters) > 0:
        return chart
    else:
        return "Made empty iniative. Add some characters."


def deal_card_to_character(init_list: InitiativeList, char: Character):
    # draw one card
    char.main_card = init_list.draw_card()

    '''
    How the order of operations of all edges/hindrances works:

    Code looks through all character edges.
    If hesitant is found, do that; ignore quick and level headed. (The bot should also prevent you from adding quick and hesitant to the same character.)

    Level headed takes priority. If found, it doesn't perform quick.
    *maybe* it warns the user if a character has both quick and level headed, and draws at least one card below 6, and tells them to manually use /choose_card and /quick_redraw

    Level headed overrules quick because you might want to take a lower card and try to use Quick on that.
    That can be done manually with the 

    Do tactician no matter what.

    Only do improved, don't do both improved and regular.
    '''

    if 'hesitant' in char.edges:
        edges.hesitant(init_list, char)
    else:
        if 'levelheaded-imp' in char.edges:
            edges.levelheaded_imp(init_list, char)
        elif 'levelheaded' in char.edges:
            edges.levelheaded(init_list, char)
        # there may be an issue where you can draw an empty deck with the quick edge
        elif 'quick' in char.edges:
            edges.quick(init_list, char)
    
    if 'tactician-imp' in char.edges:
        edges.tactician_imp(init_list, char)
    elif 'tactician' in char.edges:
        edges.tactician(init_list, char)


"""
This is only used to deal cards to characters already assigned one.
Usually when spending bennies.
"""
def deal_new_card_to_character(name: str, guild: int, channel: int) -> str:
    try:
        init_list = get_init_list(guild, channel, False)
    except database.NotFoundInChannelError:
        return "No initiative list in this channel."

    char: Character | None = next((char for char in init_list.characters if char.name == name), None)

    if char == None:
        return f"Could not find character with name {name}."

    # set as main card if higher, or unused if lower
    new_card = init_list.draw_card()
    if PlayingCardDeck.index(new_card) < PlayingCardDeck.index(char.main_card):
        char.unused_cards.append(char.main_card)
        char.main_card = new_card
    else:
        char.unused_cards.append(new_card)

    init_list.sort_characters()
    init_list.update_db(guild, channel)

    return init_list.make_initiative_chart()


def show_list(guild: int, channel: int) -> str:
    try:
        init_list = get_init_list(guild, channel)
    except database.NotFoundInChannelError:
        return "No initiative list in this channel."

    return init_list.make_initiative_chart()

def next_round(guild: int, channel: int) -> str:
    try:
        init_list = get_init_list(guild, channel, False)
    except database.NotFoundInChannelError:
        return "No initiative list in this channel."
    init_list.round_count += 1

    # clear all unused and tactician cards from characters
    for char in init_list.characters:
        char.unused_cards.clear()
        char.tactician_cards.clear()

    prepend: str = ""

    # check if a joker was drawn last round
    last_round_cards = [card for char in init_list.characters
    for card in ([char.main_card] + char.unused_cards + char.tactician_cards)]

    # shuffle if it was
    if "RJ" in last_round_cards or "BJ" in last_round_cards:
        init_list.shuffle_deck(full_shuffle=True)
        prepend = "Joker drawn last round, reshuffling deck.\n\n"

    for char in init_list.characters:
        deal_card_to_character(init_list, char)

    init_list.update_db(guild, channel)

    return prepend + get_init_list(guild, channel).make_initiative_chart()


def add_to_initiative(characters: list[str], guild: int, channel: int):
    try:
        database.insert_into_list(characters, guild, channel)
    except database.NotFoundInChannelError:
        return "No initiative list in this channel."

    init_list = get_init_list(guild, channel, False)

    chars = [c for c in init_list.characters if c.name in characters]

    for char in chars:
        deal_card_to_character(init_list, char)

    init_list.update_db(guild, channel)
    init_list.sort_characters()
    return init_list.make_initiative_chart()


def remove_from_initiative(characters: list[str], guild: int, channel: int):
    try:
        database.delete_from_list(characters, guild, channel)
    except database.NotFoundInChannelError:
        return "No initiative list in this channel."

    init_list = get_init_list(guild, channel, False)

    init_list.sort_characters()
    return init_list.make_initiative_chart()


def choose_card(name: str, card: str, guild: int, channel: int) -> str:
    try:
        init_list = get_init_list(guild, channel, False)
    except database.NotFoundInChannelError:
        return "No initiative list in this channel."

    char: Character | None = next((char for char in init_list.characters if char.name == name), None)

    if char == None:
        return f"Could not find character with name {name}."

    if card in char.unused_cards:
        char.unused_cards.remove(card)
        char.unused_cards.append(char.main_card)
        char.main_card = card

        init_list.sort_characters()
        return init_list.make_initiative_chart()
        
    else:
        return f"Could not find card {char_to_symbol(card)} in {name}'s unused cards."

def assign_tactician_card(tactician_name: str, card: str, recipient_name: str, guild: int, channel: int) -> str:
    try:
        init_list = get_init_list(guild, channel, False)
    except database.NotFoundInChannelError:
        return "No initiative list in this channel."

    tactician_char: Character | None = next((char for char in init_list.characters if char.name == tactician_name), None)    
    recipient_char: Character | None = next((char for char in init_list.characters if char.name == recipient_name), None)

    if tactician_char == None and recipient_char == None:
        return f"Could not find character with name {tactician_name} nor {recipient_name}."
    elif tactician_char == None:
        return f"Could not find character with name {tactician_name}."
    elif recipient_char == None:
        return f"Could not find character with name {recipient_name}."

    if card in tactician_char.tactician_cards:
        tactician_char.tactician_cards.remove(card)
        recipient_char.unused_cards.append(recipient_char.main_card)
        recipient_char.main_card = card

        init_list.sort_characters()
        return init_list.make_initiative_chart()
    else:
        return f"Could not find card {char_to_symbol(card)} in {tactician_name}'s tactician cards."

def quick_redraw(name: str, guild: int, channel: int) -> str:
    try:
        init_list = get_init_list(guild, channel, False)
    except database.NotFoundInChannelError:
        return "No initiative list in this channel."

    char: Character | None = next((char for char in init_list.characters if char.name == name), None)

    if char == None:
        return f"Could not find character with name {name}."

    edges.quick(init_list, char)
    init_list.sort_characters()
    return init_list.make_initiative_chart()
