import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import database
import characters
import sqlite3
from die_roller import parse_tokens, roll_savage_dice


GUILD_ID = 12345
USER_ID = 99999


class TestPartyErrorMessages:
    def test_create_party_conflict_with_existing_party(self):
        characters.create_party("Warriors", GUILD_ID)
        result = characters.create_party("Warriors", GUILD_ID)
        assert result == "Party Warriors already exists."

    def test_create_party_conflict_with_character_message(self):
        characters.add_character("Rogues", GUILD_ID)
        result = characters.create_party("Rogues", GUILD_ID)
        assert result == "Party Rogues conflicts with existing character Rogues."

    def test_add_to_party_doesnt_exist_message(self):
        result = characters.add_to_party("GhostParty", ["Alice"], GUILD_ID)
        assert result == "Party GhostParty doesn't exist."

    def test_characters_not_found_message_format(self):
        characters.create_party("Heroes", GUILD_ID)
        result = characters.add_to_party("Heroes", ["Nobody", "Ghost"], GUILD_ID)
        assert "Character(s) Nobody, Ghost not found." in result

    def test_remove_from_party_doesnt_exist_message(self):
        result = characters.remove_from_party("GhostParty", ["Alice"], GUILD_ID)
        assert result == "Party GhostParty doesn't exist."

    def test_delete_party_doesnt_exist_message(self):
        result = characters.delete_party("GhostParty", GUILD_ID)
        assert result == "Party GhostParty doesn't exist."

    def test_party_members_doesnt_exist_message(self):
        result = characters.get_party_members("GhostParty", GUILD_ID)
        assert result == "Party GhostParty doesn't exist."


class TestControlErrorMessages:
    def test_control_nonexistent_character_message(self):
        result = characters.control_character(USER_ID, "Nobody", GUILD_ID)
        assert result == "Character Nobody doesn't exist."

    def test_control_switch_message_format(self):
        characters.add_character("Alice", GUILD_ID)
        characters.add_character("Bob", GUILD_ID)
        characters.control_character(USER_ID, "Alice", GUILD_ID)
        result = characters.control_character(USER_ID, "Bob", GUILD_ID)
        assert result == "Now controlling Bob instead of Alice."

    def test_release_message_format(self):
        characters.add_character("Alice", GUILD_ID)
        characters.control_character(USER_ID, "Alice", GUILD_ID)
        result = characters.release_control(USER_ID, GUILD_ID)
        assert result == "No longer controlling Alice."

    def test_my_character_no_control_message(self):
        result = characters.get_my_character(USER_ID, GUILD_ID)
        assert result == "You are not controlling a character."


class TestPresetErrorMessages:
    def test_preset_name_is_valid_roll_message(self):
        characters.add_character("Alice", GUILD_ID)
        result = characters.make_preset(USER_ID, "3d6", "2d8", GUILD_ID, "Alice")
        assert result == "3d6 is a valid roll string. Name it something that isn't a valid roll."

    def test_no_character_specified_no_control_message(self):
        result = characters.make_preset(USER_ID, "fireball", "3d6", GUILD_ID)
        assert result == "Specify a character or control a character with `/control`."

    def test_character_doesnt_exist_message(self):
        result = characters.make_preset(USER_ID, "fireball", "3d6", GUILD_ID, "Nobody")
        assert result == "Character Nobody doesn't exist."

    def test_invalid_roll_string_message(self):
        characters.add_character("Alice", GUILD_ID)
        result = characters.make_preset(USER_ID, "fireball", "notaroll", GUILD_ID, "Alice")
        assert result == "Roll string notaroll is invalid."

    def test_preset_already_exists_message(self):
        characters.add_character("Alice", GUILD_ID)
        characters.make_preset(USER_ID, "fireball", "3d6", GUILD_ID, "Alice")
        result = characters.make_preset(USER_ID, "fireball", "2d8", GUILD_ID, "Alice")
        assert result == "Preset fireball already exists for Alice."

    def test_delete_preset_character_doesnt_exist_message(self):
        result = characters.delete_preset("fireball", "Nobody", GUILD_ID)
        assert result == "Character Nobody doesn't exist."

    def test_delete_preset_doesnt_exist_message(self):
        characters.add_character("Alice", GUILD_ID)
        result = characters.delete_preset("fireball", "Alice", GUILD_ID)
        assert result == "Preset fireball doesn't exist on Alice."

    def test_list_presets_character_doesnt_exist_message(self):
        result = characters.list_presets("Nobody", GUILD_ID)
        assert result == "Character Nobody doesn't exist."

    def test_roll_invalid_message(self):
        characters.add_character("Alice", GUILD_ID)
        characters.control_character(USER_ID, "Alice", GUILD_ID)
        result = characters.make_preset(USER_ID, "zap", "xyz123", GUILD_ID, "Alice")
        assert result == "Roll string xyz123 is invalid."


class TestMyCharacterFormat:
    def test_my_character_output_format(self):
        characters.add_character("Alice", GUILD_ID)
        characters.control_character(USER_ID, "Alice", GUILD_ID)
        characters.make_preset(USER_ID, "fireball", "3d6", GUILD_ID, "Alice")

        result = characters.get_my_character(USER_ID, GUILD_ID)

        assert "Alice" in result
        assert "Bennies" in result
        assert "fireball" in result
        assert "3d6" in result
