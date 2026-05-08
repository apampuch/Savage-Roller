import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import database


GUILD_ID = 12345


def setup_character(name, guild=GUILD_ID):
    database.insert_character(name, guild)


def setup_party_with_members(party_name, char_names, guild=GUILD_ID):
    cur = database.conn.cursor()
    cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", (party_name, guild))
    database.conn.commit()
    party_id = cur.execute("SELECT id FROM PARTIES WHERE name=? AND guild=?", (party_name, guild)).fetchone()[0]

    for name in char_names:
        char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", (name, guild)).fetchone()[0]
        cur.execute("INSERT INTO PARTY_MEMBERSHIP (party_id, char_id) VALUES (?, ?)", (party_id, char_id))

    database.conn.commit()
    cur.close()
    return party_id


class TestFightWithParties:
    def test_fight_accepts_party_name(self):
        setup_character("Alice")
        setup_character("Bob")
        setup_party_with_members("TeamA", ["Alice", "Bob"])

        cur = database.conn.cursor()
        cur.execute("""
            SELECT c.name FROM characters c
            JOIN PARTY_MEMBERSHIP pm ON pm.char_id = c.id
            JOIN PARTIES p ON p.id = pm.party_id
            WHERE p.name=? AND p.guild=?
        """, ("TeamA", GUILD_ID))
        members = [row[0] for row in cur.fetchall()]
        cur.close()
        assert "Alice" in members
        assert "Bob" in members

    def test_fight_mix_party_and_character_names(self):
        setup_character("Alice")
        setup_character("Bob")
        setup_character("Charlie")
        setup_party_with_members("TeamA", ["Alice", "Bob"])

        cur = database.conn.cursor()
        cur.execute("""
            SELECT c.name FROM characters c
            JOIN PARTY_MEMBERSHIP pm ON pm.char_id = c.id
            JOIN PARTIES p ON p.id = pm.party_id
            WHERE p.name=? AND p.guild=?
        """, ("TeamA", GUILD_ID))
        party_members = [row[0] for row in cur.fetchall()]
        cur.close()

        all_chars = set(party_members + ["Charlie"])
        assert "Alice" in all_chars
        assert "Bob" in all_chars
        assert "Charlie" in all_chars

    def test_overlapping_party_and_character_is_fine(self):
        setup_character("Alice")
        setup_character("Bob")
        setup_party_with_members("TeamA", ["Alice", "Bob"])

        cur = database.conn.cursor()
        cur.execute("""
            SELECT c.name FROM characters c
            JOIN PARTY_MEMBERSHIP pm ON pm.char_id = c.id
            JOIN PARTIES p ON p.id = pm.party_id
            WHERE p.name=? AND p.guild=?
        """, ("TeamA", GUILD_ID))
        party_members = [row[0] for row in cur.fetchall()]
        cur.close()

        all_names = party_members + ["Alice"]
        assert all_names.count("Alice") == 2


class TestDealInWithParties:
    def test_deal_in_party(self):
        setup_character("Alice")
        setup_character("Bob")
        setup_party_with_members("TeamA", ["Alice", "Bob"])

        cur = database.conn.cursor()
        cur.execute("""
            SELECT c.name FROM characters c
            JOIN PARTY_MEMBERSHIP pm ON pm.char_id = c.id
            JOIN PARTIES p ON p.id = pm.party_id
            WHERE p.name=? AND p.guild=?
        """, ("TeamA", GUILD_ID))
        members = [row[0] for row in cur.fetchall()]
        cur.close()
        assert len(members) == 2


class TestGiveBennyWithParties:
    def test_give_benny_to_party(self):
        setup_character("Alice")
        setup_character("Bob")
        setup_party_with_members("TeamA", ["Alice", "Bob"])

        cur = database.conn.cursor()
        cur.execute("""
            SELECT c.name FROM characters c
            JOIN PARTY_MEMBERSHIP pm ON pm.char_id = c.id
            JOIN PARTIES p ON p.id = pm.party_id
            WHERE p.name=? AND p.guild=?
        """, ("TeamA", GUILD_ID))
        members = [row[0] for row in cur.fetchall()]
        cur.close()

        result = database.add_benny(members, GUILD_ID)
        assert "Alice" in result
        assert "Bob" in result


class TestSetBenniesWithParties:
    def test_set_bennies_for_party(self):
        setup_character("Alice")
        setup_character("Bob")
        setup_party_with_members("TeamA", ["Alice", "Bob"])

        cur = database.conn.cursor()
        cur.execute("""
            SELECT c.name FROM characters c
            JOIN PARTY_MEMBERSHIP pm ON pm.char_id = c.id
            JOIN PARTIES p ON p.id = pm.party_id
            WHERE p.name=? AND p.guild=?
        """, ("TeamA", GUILD_ID))
        members = [row[0] for row in cur.fetchall()]
        cur.close()

        result = database.set_bennies(members, 5, GUILD_ID)
        assert "Alice" in result
        assert "Bob" in result

    def test_multiple_parties_in_one_command(self):
        setup_character("Alice")
        setup_character("Bob")
        setup_character("Charlie")
        setup_character("Dave")
        setup_party_with_members("TeamA", ["Alice", "Bob"])
        setup_party_with_members("TeamB", ["Charlie", "Dave"])

        cur = database.conn.cursor()
        all_members = []
        for party_name in ["TeamA", "TeamB"]:
            cur.execute("""
                SELECT c.name FROM characters c
                JOIN PARTY_MEMBERSHIP pm ON pm.char_id = c.id
                JOIN PARTIES p ON p.id = pm.party_id
                WHERE p.name=? AND p.guild=?
            """, (party_name, GUILD_ID))
            all_members.extend([row[0] for row in cur.fetchall()])
        cur.close()

        result = database.set_bennies(all_members, 3, GUILD_ID)
        assert "Alice" in result
        assert "Bob" in result
        assert "Charlie" in result
        assert "Dave" in result
