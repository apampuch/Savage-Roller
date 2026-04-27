import atexit
import json
import random
import sqlite3

from decks import PlayingCardDeck
from sys import argv

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

def exclusivity_check(edge: str, all_edges: set[str]) -> bool:
    # remove edge from all edges
    edge_test = all_edges - set([edge])
    
    # get edges that disqualify us
    dq_edges = EXCLUSIVE_EDGES[edge]

    # if any edges exist in both, return false, else return true
    return not edge_test & dq_edges

print("Starting DB")

db_file = ""
if "dbtest" in argv:
    db_file = "test.db"
else:
    db_file = "database.db"

conn = sqlite3.connect(db_file)
conn.execute("PRAGMA foreign_keys = ON;")
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
    CREATE TABLE IF NOT EXISTS character_edges(
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
        guild INTEGER NOT NULL,         -- guild id this initiative list belongs to
        channel INTEGER NOT NULL,       -- channel id this initiative list belongs to
        deck TEXT NOT NULL,             -- JSON list of cards in two character suit-rank format
        round_count INTEGER DEFAULT 0,  -- total number of rounds this combat
        UNIQUE (guild, channel)
    );
""")
cur.execute("""
    CREATE TABLE IF NOT EXISTS initiative_membership(
        id INTEGER PRIMARY KEY,
        char_id INTEGER NOT NULL,
        init_id INTEGER NOT NULL,
        FOREIGN KEY(char_id) REFERENCES characters(id) ON DELETE CASCADE,
        FOREIGN KEY(init_id) REFERENCES initiative_lists(id) ON DELETE CASCADE
    );
""")

# CREATE TRIGGER to delete temporary characters when deleting an initiative list
# this will only delete temporary characters that aren't in another initiative list
# so that using the same name in different channels doesn't fuck with anything
cur.execute("""
    CREATE TRIGGER IF NOT EXISTS delete_temp_characters_after_initiative_delete
    BEFORE DELETE ON initiative_lists
    FOR EACH ROW
    BEGIN
        DELETE FROM characters
        WHERE id IN (
            SELECT c.id
            FROM characters c
            JOIN initiative_membership im ON im.char_id = c.id
            WHERE im.init_id = OLD.id
            AND c.temp = 1
        )
        AND NOT EXISTS (
            SELECT 1
            FROM initiative_membership im2
            WHERE im2.char_id = characters.id
            AND im2.init_id != OLD.id
        );
    END;
""")

conn.commit()
cur.close()

@atexit.register
def shutdown():
    conn.close()
    print("DB closed successfully.")


def insert_character(name: str, guild: int, temp: bool = False) -> str:
    try:
        with conn:
            conn.execute("""
                INSERT INTO characters (name, guild, temp)
                VALUES (?, ?, ?)
            """,
            (name, guild, temp))

            return f"Created character {name}."
    except sqlite3.IntegrityError as e:
        if e.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE":
            return f"Character {name} already exists on this server."
        else:
            raise e


def delete_character(name: str, guild: int):
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM characters WHERE name=? AND guild=? LIMIT 1", (name, guild))

            if cur.rowcount == 0:
                return f"Could not find a character named {name} to delete."
            else:
                return f"Deleted character {name}."
    except sqlite3.IntegrityError as e:
        raise e


def get_edges_and_id(name: str, guild: int) -> tuple[int, tuple]:
    try:
        with conn:
            cur = conn.cursor()
            
            res = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", (name, guild)).fetchone()
            if res == None:
                cur.close()
                raise LookupError(f"Character {name} not found on this server.")
        
            edge_res = cur.execute("SELECT edge FROM character_edges WHERE char_id=?", res).fetchall()

            # silly array to fix the fact that you will often get nothing from the above query
            r_tuple = ()
            if len(edge_res) > 0:
                r_tuple = edge_res[0]

            return res[0], r_tuple
    except sqlite3.IntegrityError as e:
        raise e


def insert_edges(rows: list[str]):
    try:
        with conn:
            cur = conn.cursor()

            cur.executemany("INSERT INTO character_edges (char_id, edge) VALUES (?, ?)", rows)
    except sqlite3.IntegrityError as e:
        raise e


def delete_edges_from_character(name: str, guild: int, edges: list[str]):
    try:
        with conn:
            cur = conn.cursor()
            
            res = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", (name, guild)).fetchone()
            if res is None:
                cur.close()
                raise LookupError(f"Character {name} not found on this server.")

            # build the array for executemany()
            # res[0] is char id
            rows = []
            for edge in edges:
                # do not bother checking for invalid edges because who cares if we delete what isn't possible
                rows.append( (res[0], edge) )

            cur.executemany("DELETE FROM character_edges WHERE char_id=? AND edge=?", rows)

            rowcount = cur.rowcount

            return rowcount
    except sqlite3.IntegrityError as e:
        raise e


def get_initiative_list_and_characters(guild: int, channel: int):
    try:
        with conn:
            cur = conn.cursor()

            initiative_list = cur.execute("SELECT deck, round_count FROM initiative_lists WHERE guild=? AND channel=?", (guild, channel)).fetchone()  

            # TODO test this shit
            # get all of the characters
            character_rows = cur.execute("""
                SELECT c.name, c.bennies, json_group_array(DISTINCT e.edge) AS edges
                FROM initiative_membership im
                INNER JOIN characters c
                    ON im.char_id = c.id
                LEFT JOIN character_edges e ON c.id = e.char_id
                WHERE im.init_id=?
                GROUP BY c.id
            """, 
            (initiative_list[4])).fetchall()
    except sqlite3.IntegrityError as e:
        raise e


'''
Helper function that gets characters and makes temporary characters out of characters not found in the database.
This is used when creating a new initiative.
Temporary characters are deleted from the database when an initiative ends.
'''
def get_characters_and_make_temporary_characters(characters: list[str], guild: int):
    try:
        with conn:
            cur = conn.cursor()
            # lookup characters that already exist from our list
            placeholders = ", ".join("?" * len(characters))
            char_res = cur.execute(f"SELECT id, name FROM characters WHERE name IN ({placeholders}) AND guild=?", characters + [guild]).fetchall()

            found_chars = list(map(lambda x: x[1], char_res))
            found_ids = list(map(lambda x: x[0], char_res))

            missing_chars = set(characters) - set(found_chars)

            if len(missing_chars) > 0:
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
    except sqlite3.IntegrityError as e:
        raise e

'''
Makes a new initiative list.
Does not actually start combat, call next_round to do that.
'''
def new_list(guild: int, channel: int):
    try:
        with conn:
            cur = conn.cursor()

            # delete any existing initiative in this guild+channel
            cur.execute("DELETE FROM initiative_lists WHERE guild=? AND channel=?", (guild, channel))

            deck = list(PlayingCardDeck)
            random.shuffle(deck)

            # actually make the initiative list in the database
            cur.execute("INSERT INTO initiative_lists (guild, channel, deck, round_count) VALUES (?,?,?,0)", (guild, channel, json.dumps(deck)))

            # fight() will then deal in the cards
    except sqlite3.IntegrityError as e:
        raise e


def delete_list(guild: int, channel: int):
    try:
        with conn:
            cur = conn.cursor()

            # initiative lists are per guild and channel
            cur.execute("DELETE FROM initiative_lists WHERE guild=? AND channel=?", (guild, channel))
    except sqlite3.IntegrityError as e:
        raise e


def insert_into_list(characters: list[str], guild: int, channel: int):
    try:
        with conn:
            cur = conn.cursor()

            res = cur.execute("SELECT id FROM initiative_lists WHERE guild=? AND channel=?", (guild, channel)).fetchone()
            if res is None:
                raise LookupError(f"No fight in this channel.")
            
            # get characters and their ids
            found_chars, found_ids = get_characters_and_make_temporary_characters(characters, guild)

            rows = [(char_id, cur.lastrowid) for char_id in found_ids]

            cur.executemany("INSERT INTO initiative_membership (char_id, init_id) VALUES (?,?)", rows)

    except sqlite3.IntegrityError as e:
        raise e

def delete_from_list(characters: list[str], guild: int, channel: int):
    try:
        with conn:
            cur = conn.cursor()

            res = cur.execute("SELECT id FROM initiative_lists WHERE guild=? AND channel=?", (guild, channel)).fetchone()
            if res is None:
                raise LookupError(f"No fight in this channel.")
    except sqlite3.IntegrityError as e:
        raise e


def update_list(guild: int, channel: int, deck: list[str], round_count: int):
    # changes the deck of an initiative_list
    # usually called after drawing cards or shuffling
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("UPDATE initiative_lists SET deck=?, round_count=? WHERE guild=? AND channel=? LIMIT 1", (json.dumps(deck), round_count, guild, channel)).fetchone()
            if cur.rowcount == 0:
                raise LookupError(f"No fight in this channel.")
    except sqlite3.IntegrityError as e:
        raise e
