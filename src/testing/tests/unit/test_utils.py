from src.utils import *
import pytest
import json
from src.testing.helpers.unit_helpers import get_exp_data

@pytest.mark.parametrize(
    "input_db_name, expected_path",
    [
        ("covid.db", "src/backend/data/covid.db"),
        ("custom.db", "src/backend/data/custom.db"),
        ("test.db", "src/backend/data/test.db"),
    ]
)
def test_get_db_path(input_db_name, expected_path):
    assert get_db_path(input_db_name) == expected_path

@pytest.mark.parametrize(
    "table, db_path",
    [
        ("Date", "src/backend/data/covid.db"),
        ("Source", "src/backend/data/covid.db"),
        ("MHCareCluster", "src/backend/data/custom.db")
    ]
)
def test_get_table_info(table, db_path):
    exp = get_exp_data()
    assert get_table_info(table.lower(), db_path) == [tuple(row) for row in exp["table_info"][table]]

def test_show_tables():
    tables = show_tables("covid.db")
    exp = get_exp_data()
    assert tables == exp["db_table"]["covid.db"]

def test_get_databases():
    dbs = get_databases()
    assert set(dbs) == {"covid.db", "custom.db", "deaths.db"}

def test_get_all_tables():
    all_tables = get_all_tables()
    exp = get_exp_data()
    assert sorted(all_tables, key=lambda x: (x['database'], x['name'])) == sorted(exp["all_tables"], key=lambda x: (x['database'], x['name']))

def test_get_resp():
    return get_resp("Hello") is not None

def test_create_database():
    create_database("test.db")
    return "test.db" in get_databases()

def test_table_not_empty():
    query_db("CREATE TABLE test_table (col INTEGER)", get_db_path("test.db"))
    assert not table_not_empty("test.db", "test_table")
    query_db("INSERT INTO test_table (col) VALUES (1)", get_db_path("test.db"))
    assert table_not_empty("test.db", "test_table")

def test_delete_database():
    delete_database("test.db")
    return "test.db" not in get_databases()

@pytest.mark.parametrize(
    "table, db_name",
    [
        ("Date", "covid.db"),
        ("Restriction", "covid.db"),
        ("MHCareCluster", "custom.db")
    ]
)
def test_get_primary_keys(table, db_name):
    exp = get_exp_data()
    assert get_primary_keys(table.lower(), get_db_path(db_name)) == exp["primary_keys"][db_name][table]

if __name__ == "__main__":
    print(get_all_tables())