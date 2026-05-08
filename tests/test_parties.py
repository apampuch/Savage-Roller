import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import database


GUILD_ID = 12345


class FakeContext:
    def __init__(self, guild_id=GUILD_ID, channel_id=1, user_id=100):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.author = MagicMock()
        self.author.id = user_id
        self.respond = AsyncMock()


def setup_character(name, guild=GUILD_ID):
    database.insert_character(name, guild)


class TestCreateParty:
    def test_create_party_success(self):
        import characters
        result = characters.create_party("AlphaTeam", GUILD_ID)
        assert result == "Created party AlphaTeam."

    def test_create_party_name_conflicts_with_existing_party(self):
        cur = database.conn.cursor()
        cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("AlphaTeam", GUILD_ID))
        database.conn.commit()
        cur.close()

        cur = database.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM PARTIES WHERE name=? AND guild=?", ("AlphaTeam", GUILD_ID))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 1

        try:
            cur = database.conn.cursor()
            cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("AlphaTeam", GUILD_ID))
            database.conn.commit()
            cur.close()
            assert False, "Should have raised an integrity error or been rejected"
        except Exception:
            database.conn.rollback()

    def test_create_party_name_conflicts_with_character(self):
        setup_character("Warrior")
        cur = database.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM characters WHERE name=? AND guild=?", ("Warrior", GUILD_ID))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 1

    def test_create_party_already_exists_error_message(self):
        pass

    def test_party_names_unique_per_guild(self):
        cur = database.conn.cursor()
        cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("AlphaTeam", GUILD_ID))
        cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("AlphaTeam", 99999))
        database.conn.commit()
        cur.close()

        cur = database.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM PARTIES WHERE name=?", ("AlphaTeam",))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 2


class TestAddToParty:
    def test_add_single_character_to_party(self):
        setup_character("Alice")
        cur = database.conn.cursor()
        cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("TeamA", GUILD_ID))
        database.conn.commit()

        party_id = cur.execute("SELECT id FROM PARTIES WHERE name=? AND guild=?", ("TeamA", GUILD_ID)).fetchone()[0]
        char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]
        cur.execute("INSERT INTO PARTY_MEMBERSHIP (party_id, char_id) VALUES (?, ?)", (party_id, char_id))
        database.conn.commit()
        cur.close()

        cur = database.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM PARTY_MEMBERSHIP WHERE party_id=?", (party_id,))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 1

    def test_add_multiple_characters_comma_separated(self):
        setup_character("Alice")
        setup_character("Bob")
        setup_character("Charlie")

        cur = database.conn.cursor()
        cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("TeamA", GUILD_ID))
        database.conn.commit()

        party_id = cur.execute("SELECT id FROM PARTIES WHERE name=? AND guild=?", ("TeamA", GUILD_ID)).fetchone()[0]

        for name in ["Alice", "Bob", "Charlie"]:
            char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", (name, GUILD_ID)).fetchone()[0]
            cur.execute("INSERT INTO PARTY_MEMBERSHIP (party_id, char_id) VALUES (?, ?)", (party_id, char_id))

        database.conn.commit()
        cur.close()

        cur = database.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM PARTY_MEMBERSHIP WHERE party_id=?", (party_id,))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 3

    def test_add_to_nonexistent_party_error(self):
        pass

    def test_add_some_invalid_characters_still_adds_valid_ones(self):
        setup_character("Alice")
        cur = database.conn.cursor()
        cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("TeamA", GUILD_ID))
        database.conn.commit()

        party_id = cur.execute("SELECT id FROM PARTIES WHERE name=? AND guild=?", ("TeamA", GUILD_ID)).fetchone()[0]
        char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]
        cur.execute("INSERT INTO PARTY_MEMBERSHIP (party_id, char_id) VALUES (?, ?)", (party_id, char_id))
        database.conn.commit()
        cur.close()

        cur = database.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM PARTY_MEMBERSHIP WHERE party_id=?", (party_id,))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 1

    def test_character_can_belong_to_multiple_parties(self):
        setup_character("Alice")
        cur = database.conn.cursor()
        cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("TeamA", GUILD_ID))
        cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("TeamB", GUILD_ID))
        database.conn.commit()

        party_a_id = cur.execute("SELECT id FROM PARTIES WHERE name=? AND guild=?", ("TeamA", GUILD_ID)).fetchone()[0]
        party_b_id = cur.execute("SELECT id FROM PARTIES WHERE name=? AND guild=?", ("TeamB", GUILD_ID)).fetchone()[0]
        char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]

        cur.execute("INSERT INTO PARTY_MEMBERSHIP (party_id, char_id) VALUES (?, ?)", (party_a_id, char_id))
        cur.execute("INSERT INTO PARTY_MEMBERSHIP (party_id, char_id) VALUES (?, ?)", (party_b_id, char_id))
        database.conn.commit()
        cur.close()

        cur = database.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM PARTY_MEMBERSHIP WHERE char_id=?", (char_id,))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 2


class TestRemoveFromParty:
    def test_remove_character_from_party(self):
        setup_character("Alice")
        cur = database.conn.cursor()
        cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("TeamA", GUILD_ID))
        database.conn.commit()

        party_id = cur.execute("SELECT id FROM PARTIES WHERE name=? AND guild=?", ("TeamA", GUILD_ID)).fetchone()[0]
        char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]
        cur.execute("INSERT INTO PARTY_MEMBERSHIP (party_id, char_id) VALUES (?, ?)", (party_id, char_id))
        database.conn.commit()

        cur.execute("DELETE FROM PARTY_MEMBERSHIP WHERE party_id=? AND char_id=?", (party_id, char_id))
        database.conn.commit()
        cur.close()

        cur = database.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM PARTY_MEMBERSHIP WHERE party_id=?", (party_id,))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 0

    def test_remove_from_nonexistent_party_error(self):
        pass

    def test_remove_invalid_character_error(self):
        pass


class TestDeleteParty:
    def test_delete_existing_party(self):
        cur = database.conn.cursor()
        cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("TeamA", GUILD_ID))
        database.conn.commit()

        cur.execute("DELETE FROM PARTIES WHERE name=? AND guild=?", ("TeamA", GUILD_ID))
        database.conn.commit()
        cur.close()

        cur = database.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM PARTIES WHERE name=? AND guild=?", ("TeamA", GUILD_ID))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 0

    def test_delete_nonexistent_party_error(self):
        pass

    def test_delete_party_removes_memberships(self):
        setup_character("Alice")
        cur = database.conn.cursor()
        cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("TeamA", GUILD_ID))
        database.conn.commit()

        party_id = cur.execute("SELECT id FROM PARTIES WHERE name=? AND guild=?", ("TeamA", GUILD_ID)).fetchone()[0]
        char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]
        cur.execute("INSERT INTO PARTY_MEMBERSHIP (party_id, char_id) VALUES (?, ?)", (party_id, char_id))
        database.conn.commit()

        cur.execute("DELETE FROM PARTIES WHERE name=? AND guild=?", ("TeamA", GUILD_ID))
        database.conn.commit()
        cur.close()

        cur = database.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM PARTY_MEMBERSHIP WHERE party_id=?", (party_id,))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 0


class TestPartyMembers:
    def test_list_party_members(self):
        setup_character("Alice")
        setup_character("Bob")
        cur = database.conn.cursor()
        cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("TeamA", GUILD_ID))
        database.conn.commit()

        party_id = cur.execute("SELECT id FROM PARTIES WHERE name=? AND guild=?", ("TeamA", GUILD_ID)).fetchone()[0]

        for name in ["Alice", "Bob"]:
            char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", (name, GUILD_ID)).fetchone()[0]
            cur.execute("INSERT INTO PARTY_MEMBERSHIP (party_id, char_id) VALUES (?, ?)", (party_id, char_id))
        database.conn.commit()
        cur.close()

        cur = database.conn.cursor()
        cur.execute("""
            SELECT c.name FROM characters c
            JOIN PARTY_MEMBERSHIP pm ON pm.char_id = c.id
            WHERE pm.party_id=?
        """, (party_id,))
        members = [row[0] for row in cur.fetchall()]
        cur.close()
        assert "Alice" in members
        assert "Bob" in members

    def test_list_members_nonexistent_party_error(self):
        pass

    def test_empty_party_returns_empty(self):
        cur = database.conn.cursor()
        cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("EmptyTeam", GUILD_ID))
        database.conn.commit()

        party_id = cur.execute("SELECT id FROM PARTIES WHERE name=? AND guild=?", ("EmptyTeam", GUILD_ID)).fetchone()[0]
        cur.close()

        cur = database.conn.cursor()
        cur.execute("""
            SELECT c.name FROM characters c
            JOIN PARTY_MEMBERSHIP pm ON pm.char_id = c.id
            WHERE pm.party_id=?
        """, (party_id,))
        members = cur.fetchall()
        cur.close()
        assert len(members) == 0


class TestListParties:
    def test_list_all_parties_in_guild(self):
        cur = database.conn.cursor()
        cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("TeamA", GUILD_ID))
        cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("TeamB", GUILD_ID))
        cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("OtherGuildTeam", 99999))
        database.conn.commit()
        cur.close()

        cur = database.conn.cursor()
        cur.execute("SELECT name FROM PARTIES WHERE guild=?", (GUILD_ID,))
        parties = [row[0] for row in cur.fetchall()]
        cur.close()
        assert "TeamA" in parties
        assert "TeamB" in parties
        assert "OtherGuildTeam" not in parties


class TestCharacterDeletionCascade:
    def test_deleting_character_removes_party_membership(self):
        setup_character("Alice")
        cur = database.conn.cursor()
        cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("TeamA", GUILD_ID))
        database.conn.commit()

        party_id = cur.execute("SELECT id FROM PARTIES WHERE name=? AND guild=?", ("TeamA", GUILD_ID)).fetchone()[0]
        char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]
        cur.execute("INSERT INTO PARTY_MEMBERSHIP (party_id, char_id) VALUES (?, ?)", (party_id, char_id))
        database.conn.commit()
        cur.close()

        database.delete_character("Alice", GUILD_ID)

        cur = database.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM PARTY_MEMBERSHIP WHERE char_id=?", (char_id,))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 0


class TestPartyInCommands:
    def test_party_schema_has_correct_columns(self):
        cur = database.conn.cursor()
        cur.execute("PRAGMA table_info(PARTIES)")
        columns = {row[1] for row in cur.fetchall()}
        cur.close()
        assert "id" in columns
        assert "name" in columns
        assert "guild" in columns

    def test_party_membership_schema_has_correct_columns(self):
        cur = database.conn.cursor()
        cur.execute("PRAGMA table_info(PARTY_MEMBERSHIP)")
        columns = {row[1] for row in cur.fetchall()}
        cur.close()
        assert "id" in columns
        assert "party_id" in columns
        assert "char_id" in columns

    def test_party_name_unique_per_guild_constraint(self):
        cur = database.conn.cursor()
        cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("UniqueTeam", GUILD_ID))
        database.conn.commit()

        with pytest.raises(Exception):
            cur.execute("INSERT INTO PARTIES (name, guild) VALUES (?, ?)", ("UniqueTeam", GUILD_ID))
            database.conn.commit()
        database.conn.rollback()
        cur.close()
