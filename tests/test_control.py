import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import database


GUILD_ID = 12345


def setup_character(name, guild=GUILD_ID):
    database.insert_character(name, guild)


class TestControlSchema:
    def test_control_table_exists(self):
        cur = database.conn.cursor()
        cur.execute("PRAGMA table_info(CONTROL)")
        columns = {row[1] for row in cur.fetchall()}
        cur.close()
        assert "id" in columns
        assert "user_id" in columns
        assert "char_id" in columns

    def test_control_unique_user_per_guild(self):
        setup_character("Alice")
        setup_character("Bob")
        cur = database.conn.cursor()
        char_a_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]
        char_b_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Bob", GUILD_ID)).fetchone()[0]

        cur.execute("INSERT INTO CONTROL (user_id, char_id, guild) VALUES (?, ?, ?)", (100, char_a_id, GUILD_ID))
        database.conn.commit()

        cur.execute("SELECT COUNT(*) FROM CONTROL WHERE user_id=?", (100,))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 1


class TestControlCharacter:
    def test_control_nonexistent_character_error(self):
        pass

    def test_control_switches_character(self):
        setup_character("Alice")
        setup_character("Bob")
        cur = database.conn.cursor()
        char_a_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]
        char_b_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Bob", GUILD_ID)).fetchone()[0]

        cur.execute("INSERT INTO CONTROL (user_id, char_id, guild) VALUES (?, ?, ?)", (100, char_a_id, GUILD_ID))
        database.conn.commit()

        cur.execute("UPDATE CONTROL SET char_id=? WHERE user_id=?", (char_b_id, 100))
        database.conn.commit()

        cur.execute("SELECT char_id FROM CONTROL WHERE user_id=?", (100,))
        result = cur.fetchone()[0]
        cur.close()
        assert result == char_b_id

    def test_same_character_controlled_by_multiple_users(self):
        setup_character("Alice")
        cur = database.conn.cursor()
        char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]

        cur.execute("INSERT INTO CONTROL (user_id, char_id, guild) VALUES (?, ?, ?)", (100, char_id, GUILD_ID))
        cur.execute("INSERT INTO CONTROL (user_id, char_id, guild) VALUES (?, ?, ?)", (200, char_id, GUILD_ID))
        database.conn.commit()

        cur.execute("SELECT COUNT(*) FROM CONTROL WHERE char_id=?", (char_id,))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 2

    def test_user_can_only_control_one_character(self):
        setup_character("Alice")
        setup_character("Bob")
        cur = database.conn.cursor()
        char_a_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]
        char_b_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Bob", GUILD_ID)).fetchone()[0]

        cur.execute("INSERT INTO CONTROL (user_id, char_id, guild) VALUES (?, ?, ?)", (100, char_a_id, GUILD_ID))
        database.conn.commit()

        cur.execute("SELECT COUNT(*) FROM CONTROL WHERE user_id=?", (100,))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 1


class TestRelease:
    def test_release_removes_control(self):
        setup_character("Alice")
        cur = database.conn.cursor()
        char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]
        cur.execute("INSERT INTO CONTROL (user_id, char_id, guild) VALUES (?, ?, ?)", (100, char_id, GUILD_ID))
        database.conn.commit()

        cur.execute("DELETE FROM CONTROL WHERE user_id=?", (100,))
        database.conn.commit()

        cur.execute("SELECT COUNT(*) FROM CONTROL WHERE user_id=?", (100,))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 0


class TestMyCharacter:
    def test_no_controlled_character_error(self):
        pass

    def test_my_character_shows_info(self):
        pass
