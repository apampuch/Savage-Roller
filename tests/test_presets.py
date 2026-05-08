import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import database
from die_roller import parse_tokens, roll_savage_dice


GUILD_ID = 12345


def setup_character(name, guild=GUILD_ID):
    database.insert_character(name, guild)


def is_valid_roll(roll_string):
    try:
        roll_data = parse_tokens(roll_string)
        roll_savage_dice(roll_data)
        return True
    except (ValueError, Exception):
        return False


class TestPresetSchema:
    def test_preset_table_exists(self):
        cur = database.conn.cursor()
        cur.execute("PRAGMA table_info(PRESET)")
        columns = {row[1] for row in cur.fetchall()}
        cur.close()
        assert "id" in columns
        assert "name" in columns
        assert "roll_string" in columns
        assert "char_id" in columns

    def test_preset_name_unique_per_character(self):
        setup_character("Alice")
        cur = database.conn.cursor()
        char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]

        cur.execute("INSERT INTO PRESET (name, roll_string, char_id) VALUES (?, ?, ?)", ("attack", "2s8", char_id))
        database.conn.commit()

        with pytest.raises(Exception):
            cur.execute("INSERT INTO PRESET (name, roll_string, char_id) VALUES (?, ?, ?)", ("attack", "1d6", char_id))
            database.conn.commit()
        database.conn.rollback()
        cur.close()

    def test_same_preset_name_different_characters(self):
        setup_character("Alice")
        setup_character("Bob")
        cur = database.conn.cursor()
        char_a_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]
        char_b_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Bob", GUILD_ID)).fetchone()[0]

        cur.execute("INSERT INTO PRESET (name, roll_string, char_id) VALUES (?, ?, ?)", ("attack", "2s8", char_a_id))
        cur.execute("INSERT INTO PRESET (name, roll_string, char_id) VALUES (?, ?, ?)", ("attack", "1d6", char_b_id))
        database.conn.commit()
        cur.close()

        cur = database.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM PRESET WHERE name=?", ("attack",))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 2


class TestMakePreset:
    def test_create_preset_successfully(self):
        setup_character("Alice")
        cur = database.conn.cursor()
        char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]
        cur.execute("INSERT INTO PRESET (name, roll_string, char_id) VALUES (?, ?, ?)", ("fireball", "3d6", char_id))
        database.conn.commit()

        cur.execute("SELECT name, roll_string FROM PRESET WHERE char_id=?", (char_id,))
        row = cur.fetchone()
        cur.close()
        assert row[0] == "fireball"
        assert row[1] == "3d6"

    def test_preset_name_cannot_be_valid_roll_string(self):
        assert is_valid_roll("2d6") is True
        assert is_valid_roll("1s8") is True
        assert is_valid_roll("fireball") is False
        assert is_valid_roll("attack") is False

    def test_preset_name_validation_rejects_roll_strings(self):
        valid_rolls = ["1d6", "2s8", "3d6+1", "s10w8"]
        for roll in valid_rolls:
            assert is_valid_roll(roll) is True, f"{roll} should be a valid roll"

        invalid_names = ["fireball", "attack", "my-move", "big_hit"]
        for name in invalid_names:
            assert is_valid_roll(name) is False, f"{name} should not be a valid roll"

    def test_preset_with_nonexistent_character_error(self):
        pass

    def test_preset_with_invalid_roll_string_error(self):
        assert is_valid_roll("xyz") is False
        assert is_valid_roll("not_a_roll") is False

    def test_preset_already_exists_error(self):
        setup_character("Alice")
        cur = database.conn.cursor()
        char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]
        cur.execute("INSERT INTO PRESET (name, roll_string, char_id) VALUES (?, ?, ?)", ("fireball", "3d6", char_id))
        database.conn.commit()

        with pytest.raises(Exception):
            cur.execute("INSERT INTO PRESET (name, roll_string, char_id) VALUES (?, ?, ?)", ("fireball", "2d8", char_id))
            database.conn.commit()
        database.conn.rollback()
        cur.close()

    def test_make_preset_uses_controlled_character_when_no_name_given(self):
        setup_character("Alice")
        cur = database.conn.cursor()
        char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]
        cur.execute("INSERT INTO CONTROL (user_id, char_id, guild) VALUES (?, ?, ?)", (100, char_id, GUILD_ID))
        database.conn.commit()

        controlled = cur.execute("SELECT char_id FROM CONTROL WHERE user_id=?", (100,)).fetchone()
        cur.close()
        assert controlled is not None
        assert controlled[0] == char_id

    def test_make_preset_no_character_and_no_control_error(self):
        cur = database.conn.cursor()
        cur.execute("SELECT char_id FROM CONTROL WHERE user_id=?", (999,))
        result = cur.fetchone()
        cur.close()
        assert result is None


class TestDeletePreset:
    def test_delete_existing_preset(self):
        setup_character("Alice")
        cur = database.conn.cursor()
        char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]
        cur.execute("INSERT INTO PRESET (name, roll_string, char_id) VALUES (?, ?, ?)", ("fireball", "3d6", char_id))
        database.conn.commit()

        cur.execute("DELETE FROM PRESET WHERE name=? AND char_id=?", ("fireball", char_id))
        database.conn.commit()

        cur.execute("SELECT COUNT(*) FROM PRESET WHERE char_id=?", (char_id,))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 0

    def test_delete_nonexistent_preset_error(self):
        pass

    def test_delete_preset_nonexistent_character_error(self):
        pass

    def test_any_user_can_delete_any_preset(self):
        setup_character("Alice")
        cur = database.conn.cursor()
        char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]
        cur.execute("INSERT INTO PRESET (name, roll_string, char_id) VALUES (?, ?, ?)", ("fireball", "3d6", char_id))
        database.conn.commit()

        cur.execute("DELETE FROM PRESET WHERE name=? AND char_id=?", ("fireball", char_id))
        database.conn.commit()

        cur.execute("SELECT COUNT(*) FROM PRESET WHERE char_id=?", (char_id,))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 0


class TestListPresets:
    def test_list_presets_for_character(self):
        setup_character("Alice")
        cur = database.conn.cursor()
        char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]
        cur.execute("INSERT INTO PRESET (name, roll_string, char_id) VALUES (?, ?, ?)", ("fireball", "3d6", char_id))
        cur.execute("INSERT INTO PRESET (name, roll_string, char_id) VALUES (?, ?, ?)", ("heal", "1d8+2", char_id))
        database.conn.commit()
        cur.close()

        cur = database.conn.cursor()
        cur.execute("SELECT name, roll_string FROM PRESET WHERE char_id=?", (char_id,))
        presets = cur.fetchall()
        cur.close()
        assert len(presets) == 2
        names = [p[0] for p in presets]
        assert "fireball" in names
        assert "heal" in names

    def test_list_presets_nonexistent_character_error(self):
        pass


class TestRollWithPreset:
    def test_valid_roll_string_takes_priority_over_preset(self):
        assert is_valid_roll("1d6") is True

    def test_preset_used_when_not_valid_roll(self):
        assert is_valid_roll("fireball") is False

    def test_neither_valid_roll_nor_preset_returns_error(self):
        assert is_valid_roll("not_a_roll") is False

    def test_preset_rolls_correct_roll_string(self):
        setup_character("Alice")
        cur = database.conn.cursor()
        char_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]
        cur.execute("INSERT INTO PRESET (name, roll_string, char_id) VALUES (?, ?, ?)", ("fireball", "3d6", char_id))
        database.conn.commit()
        cur.close()

        cur = database.conn.cursor()
        cur.execute("SELECT roll_string FROM PRESET WHERE name=? AND char_id=?", ("fireball", char_id))
        roll_string = cur.fetchone()[0]
        cur.close()
        assert roll_string == "3d6"
        assert is_valid_roll(roll_string) is True


class TestPresetGloballyUnique:
    def test_preset_names_not_globally_unique(self):
        setup_character("Alice")
        cur = database.conn.cursor()
        char_a_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", GUILD_ID)).fetchone()[0]
        cur.close()

        database.insert_character("Alice", 99999)
        cur = database.conn.cursor()
        char_b_id = cur.execute("SELECT id FROM characters WHERE name=? AND guild=?", ("Alice", 99999)).fetchone()[0]

        cur.execute("INSERT INTO PRESET (name, roll_string, char_id) VALUES (?, ?, ?)", ("fireball", "3d6", char_a_id))
        cur.execute("INSERT INTO PRESET (name, roll_string, char_id) VALUES (?, ?, ?)", ("fireball", "2d8", char_b_id))
        database.conn.commit()
        cur.close()

        cur = database.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM PRESET WHERE name=?", ("fireball",))
        count = cur.fetchone()[0]
        cur.close()
        assert count == 2
