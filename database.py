import atexit
import json
import random
import sqlite3

from decks import PlayingCardDeck
from sys import argv

class NotFoundInChannelError(LookupError):
    """Raised when an initiative list is not found in a channel."""
    pass

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

print("Starting DB", flush=True)

db_file = ""
if "dbtest" in argv:
    db_file = "test.db"
elif "docker" in argv:
    db_file = "/app/data/database.db"
else:
    db_file = "database.db"

conn = sqlite3.connect(db_file)
conn.execute("PRAGMA foreign_keys = ON;")
cur = conn.cursor()

# characters are per guild
# temp marks if a character is just a temporary character created ad-hoc 
# and is automatically deleted when its associated initiative is deleted
cur.execute("""
    CREATE TABLE IF NOT EXISTS characters(
        id INTEGER PRIMARY KEY,
        bennies INTEGER DEFAULT 0,
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
        main_card TEXT,             -- card actually used for initiative
        unused_cards TEXT,          -- cards that are "discarded" this round due to edges
        tactician_cards TEXT,       -- cards that can be assigned through tactician
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

# a similar trigger for when temporary character initiative memberships are deleted
cur.execute("""
    CREATE TRIGGER IF NOT EXISTS delete_temp_characters_after_initiative_membership_delete
    BEFORE DELETE ON initiative_membership
    FOR EACH ROW
    BEGIN
        DELETE FROM characters
        WHERE id = OLD.char_id
        AND temp = 1
        AND NOT EXISTS (
            SELECT 1
            FROM initiative_membership im2
            WHERE im2.char_id = characters.id
            AND im2.init_id != OLD.init_id
        );
    END;
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS PARTIES(
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        guild INTEGER NOT NULL,
        UNIQUE(name, guild)
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS PARTY_MEMBERSHIP(
        id INTEGER PRIMARY KEY,
        party_id INTEGER NOT NULL,
        char_id INTEGER NOT NULL,
        FOREIGN KEY(party_id) REFERENCES PARTIES(id) ON DELETE CASCADE,
        FOREIGN KEY(char_id) REFERENCES characters(id) ON DELETE CASCADE,
        UNIQUE(party_id, char_id)
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS PRESET(
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        roll_string TEXT NOT NULL,
        char_id INTEGER NOT NULL,
        FOREIGN KEY(char_id) REFERENCES characters(id) ON DELETE CASCADE,
        UNIQUE(name, char_id)
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS CONTROL(
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        char_id INTEGER NOT NULL,
        guild INTEGER NOT NULL,
        FOREIGN KEY(char_id) REFERENCES characters(id) ON DELETE CASCADE,
        UNIQUE(user_id, guild)
    );
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
            cur = conn.cursor()
            
            party_exists = cur.execute("SELECT 1 FROM PARTIES WHERE name=? AND guild=?", (name, guild)).fetchone()
            if party_exists:
                return f"Character {name} conflicts with existing party {name}."
            
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
            cur.execute("DELETE FROM characters WHERE id = (SELECT id FROM characters WHERE name=? AND guild=? LIMIT 1)", (name, guild))

            if cur.rowcount == 0:
                return f"Could not find a character named {name} to delete."
            else:
                return f"Deleted character {name}."
    except sqlite3.IntegrityError as e:
        raise e


def change_char_name(character: str, new_name: str, guild: int) -> str:
    try:
        with conn:
            cur = conn.cursor()
            
            party_exists = cur.execute("SELECT 1 FROM PARTIES WHERE name=? AND guild=?", (new_name, guild)).fetchone()
            if party_exists:
                return f"Character {new_name} conflicts with existing party {new_name}."

            cur.execute("UPDATE characters SET name=? WHERE name=? AND guild=?", (new_name, character, guild))

            if cur.rowcount == 0:
                return f"No character found with name {character}"

            return f"Renamed {character} to {new_name}."
    except sqlite3.IntegrityError as e:
        raise e


def add_benny(names: list[str], guild: int) -> str:
    try:
        with conn:
            cur = conn.cursor()

            # report lists
            found_names =   []
            found_bennies = []
            missing_names = []

            for name in names:
                cur.execute("UPDATE characters SET bennies=bennies+1 WHERE name=? AND guild=? RETURNING bennies", (name, guild))

                row = cur.fetchone()

                if row is not None:
                    found_names.append(name)
                    found_bennies.append(row[0])
                else:
                    missing_names.append(name)
            
            # build the message
            message = ""

            for i in range(0, len(found_names)):
                message += f"{found_names[i]} - {found_bennies[i]} bennies.\n"

            if len(missing_names) > 0:
                message += f"Missing characters: {", ".join(missing_names)}"

            return message.rstrip()

    except sqlite3.IntegrityError as e:
        raise e


def sub_benny(names: list[str], guild: int) -> str:
    try:
        with conn:
            cur = conn.cursor()

            # report lists
            found_names =   []
            found_bennies = []
            zero_names =    []
            missing_names = []

            for name in names:
                cur.execute("UPDATE characters SET bennies=bennies-1 WHERE name=? AND guild=? AND bennies > 0 RETURNING bennies", (name, guild))

                row = cur.fetchone()

                if row is not None:
                    found_names.append(name)
                    found_bennies.append(row[0])
                else:
                    # check if we failed due to no name existing or zero bennies
                    cur.execute("SELECT 1 FROM characters WHERE name=? AND guild=?", (name, guild))

                    exists = cur.fetchone()

                    if not exists:
                        missing_names.append(name)
                    else:
                        zero_names.append(name)
            
            # build the message
            message = ""

            for i in range(0, len(found_names)):
                message += f"{found_names[i]} - {found_bennies[i]} bennies.\n"

            if len(zero_names) > 0:
                message += f"Out of bennies: {", ".join(zero_names)}\n"

            if len(missing_names) > 0:
                message += f"Missing characters: {", ".join(missing_names)}"

            return message.rstrip()

    except sqlite3.IntegrityError as e:
        raise e


def set_bennies(names: list[str], number: int, guild: int) -> str:
    try:
        with conn:
            cur = conn.cursor()

            # report lists
            found_names =   []
            missing_names = []

            for name in names:
                cur.execute("UPDATE characters SET bennies=? WHERE name=? AND guild=?", (number, name, guild))

                if cur.rowcount > 0:
                    found_names.append(name)
                else:
                    missing_names.append(name)
            
            # build the message
            message = ""

            for i in range(0, len(found_names)):
                message += f"{found_names[i]} - {number} bennies.\n"

            if len(missing_names) > 0:
                message += f"Missing characters: {", ".join(missing_names)}"

            return message.rstrip()


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

            initiative_list = cur.execute("SELECT deck, round_count, id FROM initiative_lists WHERE guild=? AND channel=?", (guild, channel)).fetchone()  

            if initiative_list == None:
                raise NotFoundInChannelError(f"No initiative list found in this channel.")

            # TODO test this shit
            # get all of the characters

            character_rows = cur.execute("""
                SELECT c.name, im.main_card, c.bennies,
                COALESCE(
                    json_group_array(DISTINCT e.edge)
                    FILTER (WHERE e.edge IS NOT NULL), '[]'
                ) AS edges,
                im.unused_cards, im.tactician_cards
                FROM initiative_membership im
                INNER JOIN characters c
                    ON im.char_id = c.id
                LEFT JOIN character_edges e ON c.id = e.char_id
                WHERE im.init_id=?
                GROUP BY c.id;
            """,
            (initiative_list[2],)).fetchall()

            return initiative_list, character_rows
    except TypeError as e:
        raise e
    except sqlite3.IntegrityError as e:
        raise e


'''
Helper function that gets characters and makes temporary characters out of characters not found in the database.
This is used when creating a new initiative.
Temporary characters are deleted from the database when an initiative ends.
'''
def get_characters(characters: list[str], guild: int, make_temp_chars:bool = True):
    try:
        with conn:
            cur = conn.cursor()
            # lookup characters that already exist from our list
            # TODO make this more secure
            placeholders = ", ".join("?" * len(characters))
            char_res = cur.execute(f"SELECT id, name FROM characters WHERE name IN ({placeholders}) AND guild=?", characters + [guild]).fetchall()

            found_chars = list(map(lambda x: x[1], char_res))
            found_ids = list(map(lambda x: x[0], char_res))

            missing_chars = set(characters) - set(found_chars)

            if make_temp_chars and len(missing_chars) > 0:
                # make a temporary character for each character that isn't defined in the db
                temp_chars = []
                for char in missing_chars:
                    temp_chars.append((char, guild, True))

                # get ids of new temp characters
                placeholders = ", ".join("?" * len(missing_chars))

                cur.executemany("INSERT INTO characters (name, guild, temp) VALUES (?, ?, ?)", temp_chars)
                missing_res = cur.execute(f"SELECT id, name FROM characters WHERE name IN ({placeholders}) AND guild=?", list(missing_chars) + [guild]).fetchall()

                # add temp characters to list
                found_ids += list(map(lambda x: x[0], missing_res))

            return found_ids
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
                raise NotFoundInChannelError("No fight in this channel.")

            init_id = res[0]
            
            # get characters and their ids
            found_ids = get_characters(characters, guild)

            rows = [(char_id, init_id) for char_id in found_ids]

            cur.executemany("INSERT INTO initiative_membership (char_id, init_id) VALUES (?,?)", rows)

    except sqlite3.IntegrityError as e:
        raise e


def delete_from_list(characters: list[str], guild: int, channel: int):
    try:
        with conn:
            cur = conn.cursor()

            res = cur.execute("SELECT id FROM initiative_lists WHERE guild=? AND channel=?", (guild, channel)).fetchone()

            if res is None:
                raise NotFoundInChannelError(f"No fight in this channel.")

            init_id = res[0]

            found_ids = get_characters(characters, guild)

            for char_id in found_ids:
                cur.execute("DELETE FROM initiative_membership WHERE char_id=? AND init_id=?", (char_id, init_id))    
                        
    except sqlite3.IntegrityError as e:
        raise e


def update_list(character_names: list[str], character_info: list[list], guild: int, channel: int, deck: list[str], round_count: int):
    # changes the deck of an initiative_list
    # usually called after drawing cards or shuffling

    # character info is a list with list of the following, in order:
    # name, guild, channel, main_card, unused_cards, tactician_cards
    # unused_cards and tactician_cards must be converted to json with dumps

    try:
        with conn:
            cur = conn.cursor()

            # update the list itself
            init_list_id = cur.execute("""
                UPDATE initiative_lists SET deck=?, round_count=? WHERE guild=? AND channel=? RETURNING id;
            """, (json.dumps(deck), round_count, guild, channel)).fetchone()

            if cur.rowcount == 0:
                raise LookupError("No fight in this channel.")
            else:
                # get all character ids
                char_id_getters = [ [x, guild] for x in character_names ]

                char_ids = []
                for name, guild in char_id_getters:
                    rows = cur.execute("""
                        SELECT id FROM characters
                        WHERE name=? AND guild=?
                    """, (name, guild)).fetchall()
                    char_ids.extend(rows)

                # append ids to character_info
                if len(char_ids) != len(character_info):
                    raise ValueError("Length of char_ids not equal to length of character_info!")

                for i in range(0, len(character_info)):
                    character_info[i].append(char_ids[i][0])
                    character_info[i].append(init_list_id[0])

                # update all initiative memberships
                cur.executemany("""
                    UPDATE initiative_membership
                    SET main_card=?, unused_cards=?, tactician_cards=?
                    WHERE char_id=? AND init_id=?
                """, character_info)
    except sqlite3.IntegrityError as e:
        raise e


def create_party(name: str, guild: int) -> str:
    try:
        with conn:
            cur = conn.cursor()
            
            char_exists = cur.execute("SELECT 1 FROM characters WHERE name=? AND guild=?", (name, guild)).fetchone()
            if char_exists:
                return f"Party {name} conflicts with existing character {name}."
            
            cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", (name, guild))
            return f"Created party {name}."
    except sqlite3.IntegrityError as e:
        if e.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE":
            return f"Party {name} already exists."
        else:
            raise e


def add_to_party(party_name: str, character_names: list[str], guild: int) -> str:
    try:
        with conn:
            cur = conn.cursor()
            
            party = cur.execute("SELECT id FROM PARTIES WHERE name=? AND guild=?", (party_name, guild)).fetchone()
            if not party:
                return f"Party {party_name} doesn't exist."
            
            party_id = party[0]
            found_chars = []
            missing_chars = []
            
            for char_name in character_names:
                char = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", (char_name, guild)).fetchone()
                if char:
                    try:
                        cur.execute("INSERT INTO PARTY_MEMBERSHIP (party_id, char_id) VALUES (?, ?)", (party_id, char[0]))
                        found_chars.append(char_name)
                    except sqlite3.IntegrityError:
                        found_chars.append(char_name)
                else:
                    missing_chars.append(char_name)
            
            message = f"Added {', '.join(found_chars)} to {party_name}." if found_chars else ""
            if missing_chars:
                if message:
                    message += f"\nCharacter(s) {', '.join(missing_chars)} not found."
                else:
                    message = f"Character(s) {', '.join(missing_chars)} not found."
            
            return message
    except sqlite3.IntegrityError as e:
        raise e


def remove_from_party(party_name: str, character_names: list[str], guild: int) -> str:
    try:
        with conn:
            cur = conn.cursor()
            
            party = cur.execute("SELECT id FROM PARTIES WHERE name=? AND guild=?", (party_name, guild)).fetchone()
            if not party:
                return f"Party {party_name} doesn't exist."
            
            party_id = party[0]
            found_chars = []
            missing_chars = []
            
            for char_name in character_names:
                char = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", (char_name, guild)).fetchone()
                if char:
                    cur.execute("DELETE FROM PARTY_MEMBERSHIP WHERE party_id=? AND char_id=?", (party_id, char[0]))
                    found_chars.append(char_name)
                else:
                    missing_chars.append(char_name)
            
            message = f"Removed {', '.join(found_chars)} from {party_name}." if found_chars else ""
            if missing_chars:
                if message:
                    message += f"\nCharacter(s) {', '.join(missing_chars)} not found."
                else:
                    message = f"Character(s) {', '.join(missing_chars)} not found."
            
            return message
    except sqlite3.IntegrityError as e:
        raise e


def delete_party(name: str, guild: int) -> str:
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM PARTIES WHERE name=? AND guild=?", (name, guild))
            
            if cur.rowcount == 0:
                return f"Party {name} doesn't exist."
            else:
                return f"Deleted party {name}."
    except sqlite3.IntegrityError as e:
        raise e


def get_party_members(party_name: str, guild: int) -> str:
    try:
        with conn:
            cur = conn.cursor()
            
            party = cur.execute("SELECT id FROM PARTIES WHERE name=? AND guild=?", (party_name, guild)).fetchone()
            if not party:
                return f"Party {party_name} doesn't exist."
            
            members = cur.execute("""
                SELECT c.name FROM characters c
                JOIN PARTY_MEMBERSHIP pm ON pm.char_id = c.id
                WHERE pm.party_id=?
            """, (party[0],)).fetchall()
            
            if members:
                return f"Members of {party_name}:\n" + "\n".join([m[0] for m in members])
            else:
                return f"Party {party_name} has no members."
    except sqlite3.IntegrityError as e:
        raise e


def list_parties(guild: int) -> str:
    try:
        with conn:
            cur = conn.cursor()
            parties = cur.execute("SELECT name FROM PARTIES WHERE guild=?", (guild,)).fetchall()
            
            if parties:
                return "Parties:\n" + "\n".join([p[0] for p in parties])
            else:
                return "No parties found."
    except sqlite3.IntegrityError as e:
        raise e


def get_character_names_from_parties(party_names: list[str], guild: int) -> list[str]:
    try:
        with conn:
            cur = conn.cursor()
            all_char_names = []
            
            for party_name in party_names:
                party = cur.execute("SELECT id FROM PARTIES WHERE name=? AND guild=?", (party_name, guild)).fetchone()
                if party:
                    members = cur.execute("""
                        SELECT c.name FROM characters c
                        JOIN PARTY_MEMBERSHIP pm ON pm.char_id = c.id
                        WHERE pm.party_id=?
                    """, (party[0],)).fetchall()
                    all_char_names.extend([m[0] for m in members])
            
            return all_char_names
    except sqlite3.IntegrityError as e:
        raise e


def resolve_names_to_characters(names: list[str], guild: int) -> list[str]:
    try:
        with conn:
            cur = conn.cursor()
            all_char_names = []
            
            for name in names:
                char = cur.execute("SELECT name FROM characters WHERE name=? AND guild=?", (name, guild)).fetchone()
                if char:
                    all_char_names.append(char[0])
                else:
                    party = cur.execute("SELECT id FROM PARTIES WHERE name=? AND guild=?", (name, guild)).fetchone()
                    if party:
                        members = cur.execute("""
                            SELECT c.name FROM characters c
                            JOIN PARTY_MEMBERSHIP pm ON pm.char_id = c.id
                            WHERE pm.party_id=?
                        """, (party[0],)).fetchall()
                        all_char_names.extend([m[0] for m in members])
            
            return list(set(all_char_names))
    except sqlite3.IntegrityError as e:
        raise e


def control_character(user_id: int, char_name: str, guild: int) -> str:
    try:
        with conn:
            cur = conn.cursor()
            
            char = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", (char_name, guild)).fetchone()
            if not char:
                return f"Character {char_name} doesn't exist."
            
            old_control = cur.execute("SELECT c.name FROM CONTROL ctrl JOIN characters c ON ctrl.char_id = c.id WHERE ctrl.user_id=? AND ctrl.guild=?", (user_id, guild)).fetchone()
            
            cur.execute("DELETE FROM CONTROL WHERE user_id=? AND guild=?", (user_id, guild))
            cur.execute("INSERT INTO CONTROL (user_id, char_id, guild) VALUES (?, ?, ?)", (user_id, char[0], guild))
            
            if old_control:
                return f"Now controlling {char_name} instead of {old_control[0]}."
            else:
                return f"Now controlling {char_name}."
    except sqlite3.IntegrityError as e:
        raise e


def release_control(user_id: int, guild: int) -> str:
    try:
        with conn:
            cur = conn.cursor()
            
            char = cur.execute("SELECT c.name FROM CONTROL ctrl JOIN characters c ON ctrl.char_id = c.id WHERE ctrl.user_id=? AND ctrl.guild=?", (user_id, guild)).fetchone()
            
            if not char:
                return "You are not controlling a character."
            
            cur.execute("DELETE FROM CONTROL WHERE user_id=? AND guild=?", (user_id, guild))
            return f"No longer controlling {char[0]}."
    except sqlite3.IntegrityError as e:
        raise e


def get_controlled_character(user_id: int, guild: int):
    try:
        with conn:
            cur = conn.cursor()
            result = cur.execute("""
                SELECT c.id, c.name FROM CONTROL ctrl
                JOIN characters c ON ctrl.char_id = c.id
                WHERE ctrl.user_id=? AND ctrl.guild=?
            """, (user_id, guild)).fetchone()
            return result
    except sqlite3.IntegrityError as e:
        raise e


def create_preset(preset_name: str, char_name: str, roll_string: str, guild: int) -> str:
    try:
        with conn:
            cur = conn.cursor()
            
            char = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", (char_name, guild)).fetchone()
            if not char:
                return f"Character {char_name} doesn't exist."
            
            cur.execute("INSERT INTO PRESET (name, roll_string, char_id) VALUES (?, ?, ?)", (preset_name, roll_string, char[0]))
            return f"Created preset {preset_name} for {char_name}."
    except sqlite3.IntegrityError as e:
        if e.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE":
            return f"Preset {preset_name} already exists for {char_name}."
        else:
            raise e


def delete_preset(preset_name: str, char_name: str, guild: int) -> str:
    try:
        with conn:
            cur = conn.cursor()
            
            char = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", (char_name, guild)).fetchone()
            if not char:
                return f"Character {char_name} doesn't exist."
            
            cur.execute("DELETE FROM PRESET WHERE name=? AND char_id=?", (preset_name, char[0]))
            
            if cur.rowcount == 0:
                return f"Preset {preset_name} doesn't exist on {char_name}."
            else:
                return f"Deleted preset {preset_name} from {char_name}."
    except sqlite3.IntegrityError as e:
        raise e


def get_preset(preset_name: str, char_id: int):
    try:
        with conn:
            cur = conn.cursor()
            result = cur.execute("SELECT roll_string FROM PRESET WHERE name=? AND char_id=?", (preset_name, char_id)).fetchone()
            return result[0] if result else None
    except sqlite3.IntegrityError as e:
        raise e


def list_presets(char_name: str, guild: int) -> str:
    try:
        with conn:
            cur = conn.cursor()
            
            char = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", (char_name, guild)).fetchone()
            if not char:
                return f"Character {char_name} doesn't exist."
            
            presets = cur.execute("SELECT name, roll_string FROM PRESET WHERE char_id=?", (char[0],)).fetchall()
            
            if presets:
                return f"Presets for {char_name}:\n" + "\n".join([f"{p[0]}: {p[1]}" for p in presets])
            else:
                return f"{char_name} has no presets."
    except sqlite3.IntegrityError as e:
        raise e


def get_character_info(char_name: str, guild: int) -> str:
    try:
        with conn:
            cur = conn.cursor()
            
            char = cur.execute("SELECT id, bennies FROM characters WHERE name=? AND guild=?", (char_name, guild)).fetchone()
            if not char:
                return f"Character {char_name} doesn't exist."
            
            char_id, bennies = char
            
            edges = cur.execute("SELECT edge FROM character_edges WHERE char_id=?", (char_id,)).fetchall()
            edge_list = [e[0] for e in edges] if edges else []
            
            presets = cur.execute("SELECT name, roll_string FROM PRESET WHERE char_id=?", (char_id,)).fetchall()
            
            result = f"{char_name}\n{bennies} Bennies\nEdges: {', '.join(edge_list) if edge_list else 'None'}\nPresets:\n"
            
            if presets:
                for p in presets:
                    result += f"{p[0]}: {p[1]}\n"
            else:
                result += "None\n"
            
            return result.rstrip()
    except sqlite3.IntegrityError as e:
        raise e
