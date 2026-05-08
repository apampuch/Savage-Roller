import sys
import os
import sqlite3
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.argv.append("dbtest")

import database


@pytest.fixture(autouse=True)
def clean_db():
    database.conn.execute("DELETE FROM initiative_membership")
    database.conn.execute("DELETE FROM initiative_lists")
    database.conn.execute("DELETE FROM character_edges")

    if table_exists("PARTY_MEMBERSHIP"):
        database.conn.execute("DELETE FROM PARTY_MEMBERSHIP")
    if table_exists("PARTIES"):
        database.conn.execute("DELETE FROM PARTIES")
    if table_exists("PRESET"):
        database.conn.execute("DELETE FROM PRESET")
    if table_exists("CONTROL"):
        database.conn.execute("DELETE FROM CONTROL")

    database.conn.execute("DELETE FROM characters")
    database.conn.commit()
    yield
    database.conn.execute("DELETE FROM initiative_membership")
    database.conn.execute("DELETE FROM initiative_lists")
    database.conn.execute("DELETE FROM character_edges")

    if table_exists("PARTY_MEMBERSHIP"):
        database.conn.execute("DELETE FROM PARTY_MEMBERSHIP")
    if table_exists("PARTIES"):
        database.conn.execute("DELETE FROM PARTIES")
    if table_exists("PRESET"):
        database.conn.execute("DELETE FROM PRESET")
    if table_exists("CONTROL"):
        database.conn.execute("DELETE FROM CONTROL")

    database.conn.execute("DELETE FROM characters")
    database.conn.commit()


def table_exists(table_name):
    cur = database.conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    result = cur.fetchone()
    cur.close()
    return result is not None
