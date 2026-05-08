import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import database


class TestExistingTablesUnchanged:
    def test_characters_table_schema(self):
        cur = database.conn.cursor()
        cur.execute("PRAGMA table_info(characters)")
        columns = {row[1]: row[2] for row in cur.fetchall()}
        cur.close()
        assert "id" in columns
        assert "bennies" in columns
        assert "name" in columns
        assert "guild" in columns
        assert "temp" in columns

    def test_character_edges_table_schema(self):
        cur = database.conn.cursor()
        cur.execute("PRAGMA table_info(character_edges)")
        columns = {row[1] for row in cur.fetchall()}
        cur.close()
        assert "id" in columns
        assert "char_id" in columns
        assert "edge" in columns

    def test_initiative_lists_table_schema(self):
        cur = database.conn.cursor()
        cur.execute("PRAGMA table_info(initiative_lists)")
        columns = {row[1] for row in cur.fetchall()}
        cur.close()
        assert "id" in columns
        assert "guild" in columns
        assert "channel" in columns
        assert "deck" in columns
        assert "round_count" in columns

    def test_initiative_membership_table_schema(self):
        cur = database.conn.cursor()
        cur.execute("PRAGMA table_info(initiative_membership)")
        columns = {row[1] for row in cur.fetchall()}
        cur.close()
        assert "id" in columns
        assert "char_id" in columns
        assert "init_id" in columns
        assert "main_card" in columns
        assert "unused_cards" in columns
        assert "tactician_cards" in columns


class TestNewTablesExist:
    def test_parties_table_exists(self):
        cur = database.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='PARTIES'")
        result = cur.fetchone()
        cur.close()
        assert result is not None

    def test_party_membership_table_exists(self):
        cur = database.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='PARTY_MEMBERSHIP'")
        result = cur.fetchone()
        cur.close()
        assert result is not None

    def test_preset_table_exists(self):
        cur = database.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='PRESET'")
        result = cur.fetchone()
        cur.close()
        assert result is not None

    def test_control_table_exists(self):
        cur = database.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='CONTROL'")
        result = cur.fetchone()
        cur.close()
        assert result is not None


class TestForeignKeys:
    def test_party_membership_fk_to_parties(self):
        cur = database.conn.cursor()
        cur.execute("PRAGMA foreign_key_list(PARTY_MEMBERSHIP)")
        fks = cur.fetchall()
        cur.close()
        tables = [fk[2] for fk in fks]
        assert "PARTIES" in tables

    def test_party_membership_fk_to_characters(self):
        cur = database.conn.cursor()
        cur.execute("PRAGMA foreign_key_list(PARTY_MEMBERSHIP)")
        fks = cur.fetchall()
        cur.close()
        tables = [fk[2] for fk in fks]
        assert "characters" in tables

    def test_preset_fk_to_characters(self):
        cur = database.conn.cursor()
        cur.execute("PRAGMA foreign_key_list(PRESET)")
        fks = cur.fetchall()
        cur.close()
        tables = [fk[2] for fk in fks]
        assert "characters" in tables

    def test_control_fk_to_characters(self):
        cur = database.conn.cursor()
        cur.execute("PRAGMA foreign_key_list(CONTROL)")
        fks = cur.fetchall()
        cur.close()
        tables = [fk[2] for fk in fks]
        assert "characters" in tables
