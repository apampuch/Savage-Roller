import atexit
import edges
import random
import sqlite3

from contextlib import closing
from decks import PlayingCardDeck

# remove this eventually and make edges
VALID_EDGES = ["hesitant", "quick", "levelheaded",
               "levelheaded-imp", "tactician", "tactician-imp"]

# DECK_OF_CARDS = ["RJ", "BJ"]
# DECK_OF_TAROTS = []

# for rank in ("A", "K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2"):
#     for suit in ("S", "H", "D", "C"):
#         DECK_OF_CARDS.append(suit + rank)

print("Starting DB")
conn = sqlite3.connect("database.db")
cur = conn.cursor()

# characters are per guild
# temp marks if a character is just a temporary character created ad-hoc and safe to be deleted when its associated initiative is deleted
cur.execute("""
    CREATE TABLE IF NOT EXISTS characters(
        id INTEGER PRIMARY KEY,
        bennies INTEGER,
        name TEXT NOT NULL,
        guild INTEGER NOT NULL,
        temp BOOLEAN,
        UNIQUE(name, guild)
    );
""")
cur.execute("""
    CREATE TABLE IF NOT EXISTS char_edges(
        id INTERGER PRIMARY KEY,
        char_id INTEGER NOT NULL,
        edge TEXT,
        FOREIGN KEY(char_id) REFERENCES characters(id) ON DELETE CASCADE,
        UNIQUE(char_id, edge)
    );
""")

# initiative lists are per guild and channel
# each deck is required for initiative
# this is stored in seed and total_drawn
# recreate the deck's state by loading the seed into random.seed()
# then keep drawing where total_drawn left off
cur.execute("""
    CREATE TABLE IF NOT EXISTS initiative_lists(
        id INTEGER PRIMARY KEY,
        guild INTEGER NOT NULL,
        channel INTEGER NOT NULL,
        seed INTEGER NOT NULL,
        total_drawn INTEGER NOT NULL
    );
""")
cur.execute("""
    CREATE TABLE IF NOT EXISTS initiative_membership(
        id INTEGER PRIMARY KEY,
        card TEXT NOT NULL,
        char_id INTEGER NOT NULL,
        init_id INTEGER NOT NULL,
        FOREIGN KEY(char_id) REFERENCES characters(id) ON DELETE CASCADE,
        FOREIGN KEY(init_id) REFERENCES initiative_lists(id) ON DELETE CASCADE
    );
""")

# CREATE TRIGGER to delete temporary characters when deleting an initiative list

conn.commit()
cur.close()


def add_character(character: str, guild: int, temp: bool = False):
    cur = conn.cursor()

    try:
        cur.execute("INSERT INTO characters (name, guild, temp) VALUES (?, ?)", (character, guild, temp))
    except sqlite3.IntegrityError as e:
        cur.close()
        raise e

    conn.commit()
    cur.close()

def delete_character(character: str, guild: int):
    cur = conn.cursor()
    
    # res = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", (character, guild)).fetchone()
    # if res == None:
    #     cur.close()
    #     raise LookupError(f"Character {character} not found on this server.")

    cur.execute("DELETE FROM characters WHERE id=?", res)

    conn.commit()
    cur.close()

def add_edges_to_character(character: str, guild: int, edges: set[str]):
    cur = conn.cursor()
    
    res = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", (character, guild)).fetchone()
    if res == None:
        cur.close()
        raise LookupError(f"Character {character} not found on this server.")

    current_edges = cur.execute("SELECT edge FROM char_edges WHERE char_id=?", res).fetchmany()
    current_edges = list(map(lambda x: x[0], current_edges))

    # build the array for executemany()
    # res[0] is char id
    rows = []
    invalid = []
    for edge in edges:
        if edge in VALID_EDGES and edge not in current_edges:
            rows.append( (res[0], edge) )
        else:
            invalid.append(edge)

    cur.executemany("INSERT INTO char_edges (char_id, edge) VALUES (?, ?)", rows)

    conn.commit()
    cur.close()

    return invalid

def remove_edges_from_character(character: str, guild: int, edges: list[str]):
    cur = conn.cursor()
    
    res = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", (character, guild)).fetchone()
    if res is None:
        cur.close()
        raise LookupError(f"Character {character} not found on this server.")

    # build the array for executemany()
    # res[0] is char id
    rows = []
    for edge in edges:
        # do not bother checking for invalid edges because who cares if we delete what isn't possible
        rows.append( (res[0], edge) )

    cur.executemany("DELETE FROM char_edges WHERE char_id=? AND edge=?", rows)

    rowcount = cur.rowcount

    conn.commit()
    cur.close()

    return rowcount

def get_characters_and_make_temporary_characters(characters: list[str], guild: int):
    # lookup characters that already exist from our list
    placeholders = ", ".join("?" * len(characters))
    char_res = cur.execute(f"SELECT id, name FROM characters WHERE name IN ({placeholders}) AND guild=?", characters + [guild]).fetchall()

    found_chars = list(map(lambda x: x[1], char_res))
    found_ids = list(map(lambda x: x[0], char_res))

    if len(missing_chars) > 0:
        missing_chars = set(characters) - set(found_chars)

        # make a temporary character for each character that isn't defined in the db
        temp_chars = []
        for char in missing_chars:
            temp_chars.append((char, guild, True))

        # get ids of new temp characters
        placeholders = ", ".join("?" * len(missing_chars))

        cur.executemany("INSERT INTO characters (name, guild, temp) VALUES (?, ?, ?)", temp_chars)
        missing_res = cur.execute(f"SELECT id, name FROM characters WHERE name IN ({placeholders}) AND guild=?", list(missing_chars) + [guild]).fetchall()

        # add temp characters to lists
        found_chars += list(map(lambda x: x[1], missing_res))
        found_ids += list(map(lambda x: x[0], missing_res))

    return found_chars, found_ids

def next_round():
    pass

# initiative entries can either point to characters, or can point to strings that are just "placeholders"
def new_initiative(characters: list[str], guild: int, channel: int):
    cur = conn.cursor()

    # delete any existing initiative in this guild+channel
    cur.execute("DELETE FROM initiative_lists WHERE guild=? AND channel=?", (guild, channel))

    # generate a seed
    seed = random.randrange(2**32)
    random.seed(seed)

    # shuffle the deck
    deck = list(PlayingCardDeck)
    random.shuffle(deck)

    # track cards drawn
    cards_drawn = 0

    # get characters and their ids
    found_chars, found_ids = get_characters_and_make_temporary_characters(characters, guild)

    # handle each edge for each character, then draw cards based on those edges

    conn.commit()
    cur.close()


def delete_initiative(guild: int, channel: int):
    cur = conn.cursor()

    # delete any temporary characters

    conn.commit()
    cur.close()


def add_to_initiative(characters: list[str], guild: int, channel: int):
    cur = conn.cursor()

    res = cur.execute("SELECT id FROM initiative_lists WHERE guild=? AND channel=?", (guild, channel)).fetchone()
    if res is None:
        raise LookupError(f"No fight in this channel.")

    conn.commit()
    cur.close()


def remove_from_initiative(characters: list[str], guild: int, channel: int):
    cur = conn.cursor()

    res = cur.execute("SELECT id FROM initiative_lists WHERE guild=? AND channel=?", (guild, channel)).fetchone()
    if res is None:
        raise LookupError(f"No fight in this channel.")

    conn.commit()
    cur.close()

@atexit.register
def shutdown():
    conn.close()
    print("DB closed successfully.")
