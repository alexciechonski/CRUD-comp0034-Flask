from src.backend.validation import Validator as val
import pytest

@pytest.mark.parametrize(
    "db_name, table, res",
    [
        ("covid.db", "Date", False),
        ("covid.db", "Week", False),
        ("covid.db", "Source", False),
        ("covid.db", "SummaryRestriction", False),
        ("covid.db", "Restriction", False),
        ("covid.db", "DailyRestriction", False),
        ("covid.db", "WeeklyRestriction", False),
        ("covid.db", "Infections", True),
        ("custom.db", "MHCareCluster", False),
        ("custom.db", "MentalHealth", True),
        ("deaths.db", "deaths", False),
        ("deaths.db", "MortalityRate", True)
    ]
)
def test_val_create_table(db_name, table, res, test_validator):
    assert test_validator.val_create_table(db_name, table) == res

@pytest.mark.parametrize(
    "db_name, table, res",
    [
        ("covid.db", "Date", False),
        ("covid.db", "Week", False),
        ("covid.db", "Source", False),
        ("covid.db", "SummaryRestriction", False),
        ("covid.db", "Restriction", False),
        ("covid.db", "DailyRestriction", False),
        ("covid.db", "WeeklyRestriction", False),
        ("covid.db", "Infections", True),
        ("custom.db", "MHCareCluster", True),
        ("custom.db", "MentalHealth", True),
        ("deaths.db", "Deaths", True),
        ("deaths.db", "MortalityRate", True)
    ]
)
def test_val_delete_table(db_name, table, res, test_validator):
    assert test_validator.val_delete_table(db_name, table) == res

@pytest.mark.parametrize(
    "db_name, table, res",
    [
        ("covid.db", "Date", False),
        ("covid.db", "Week", False),
        ("covid.db", "Source", False),
        ("covid.db", "SummaryRestriction", False),
        ("covid.db", "Restriction", False),
        ("covid.db", "DailyRestriction", False),
        ("covid.db", "WeeklyRestriction", False),
        ("covid.db", "Infections", True),
        ("custom.db", "MHCareCluster", True),
        ("custom.db", "MentalHealth", True),
        ("deaths.db", "Deaths", True),
        ("deaths.db", "MortalityRate", True)
    ]
)
def test_val_insert(db_name, table, res, test_validator):
    assert test_validator.val_insert(db_name, table) == res

@pytest.mark.parametrize(
    "db_name, res",
    [
        ("covid.db", False),
        ("custom.db", True),
        ("deaths.db", True)
    ]
)
def test_delete_database(db_name, res, test_validator):
    assert test_validator.val_delete_database(db_name) == res