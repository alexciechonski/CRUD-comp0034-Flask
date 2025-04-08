import pytest
from sqlalchemy.orm import declarative_base
from src.backend.log.log_manager import LogManager

TEST_DB_NAME = "test.db"
TEST_TABLE_NAME = "test_table"

Base = declarative_base()

@pytest.mark.parametrize(
    "new_data",
    [
        ({"id": 1, "time": "2020-01-01", "measured_value":150}),
        ({"id": 2, "time": "2020-01-02", "measured_value":300}),
        ({"id": 3, "time": "2020-01-03", "measured_value":1000}),
    ]
)
def test_create_change(temp_log_file, in_memory_db, new_data):
    manager = LogManager()
    manager.create_change(TEST_DB_NAME, TEST_TABLE_NAME, new_data)

    assert len(manager.log) == 1
    entry = manager.log[-1]
    assert entry["change"] == "create"
    assert entry["new_data"] == new_data

@pytest.mark.parametrize(
    "old_data, new_data",
    [
        (
            {"id": 1, "time": "2020-01-01", "measured_value":150},
            {"id": 1, "time": "2020-01-01", "measured_value":200}
        ),
        (
            {"id": 2, "time": "2020-01-02", "measured_value":300},
            {"id": 2, "time": "2020-01-02", "measured_value":400}
        ),
        (
            {"id": 2, "time": "2020-01-02", "measured_value":1000},
            {"id": 2, "time": "2020-01-02", "measured_value":1}
        )
    ]
)
def test_update_change(temp_log_file, in_memory_db, old_data, new_data):
    manager = LogManager()
    manager.update_change(TEST_DB_NAME, TEST_TABLE_NAME, new_data, old_data)

    assert len(manager.log) == 1
    entry = manager.log[-1]
    assert entry["change"] == "update"
    assert entry["new_data"] == new_data
    assert entry["prev_data"] == old_data

@pytest.mark.parametrize(
    "old_data",
    [
        ({"id": 1, "time": "2020-01-01", "measured_value":200}),
        ({"id": 2, "time": "2020-01-02", "measured_value":400}),
        ({"id": 2, "time": "2020-01-02", "measured_value":1})
    ]
)
def test_delete_change(temp_log_file, in_memory_db, old_data):
    manager = LogManager()
    manager.delete_change(TEST_DB_NAME, TEST_TABLE_NAME, old_data)

    assert len(manager.log) == 1
    entry = manager.log[-1]
    assert entry["change"] == "delete"
    assert entry["prev_data"] == old_data

@pytest.mark.parametrize(
    "old_data, new_data",
    [
        (
            {},
            {"id": 1, "time": "2023-04-01", "measured_value":200}
        ),
        (
            {"id": 1, "time": "2023-04-01", "measured_value":200},
            {"id": 1, "time": "2023-04-01", "measured_value":300}
        ),
        (
            {"id": 1, "time": "2023-04-01", "measured_value":300},
            {}
        )
    ]
)
def test_remove_change(temp_log_file, in_memory_db, new_data, old_data):
    manager = LogManager()
    manager.create_change(TEST_DB_NAME, TEST_TABLE_NAME, new_data)
    manager.update_change(TEST_DB_NAME, TEST_TABLE_NAME, new_data, old_data)
    manager.delete_change(TEST_DB_NAME, TEST_TABLE_NAME, old_data)

    assert len(manager.log) == 3
    manager.remove_change("test.db", "test_table", "update")
    assert len(manager.log) == 2
    assert all(entry["change"] != "update" for entry in manager.log)

@pytest.mark.parametrize(
    "data",
    [
        ({"id": 1, "time": "2023-04-01", "measured_value":300})
    ]
)
def test_to_tables_returns_dataframe(temp_log_file, in_memory_db, data):
    manager = LogManager()
    manager.create_change(TEST_DB_NAME, TEST_TABLE_NAME, data)
    df = manager.to_tables()
    assert not df.empty
    assert "change_type" in df.columns
