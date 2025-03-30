from src.backend.data_server import *
import pytest
from sqlalchemy.orm import Session
from src.testing.helpers.unit_helpers import get_exp_data
import datetime
from src.utils import get_db_path


def test_get_session_returns_valid_session(monkeypatch):
    monkeypatch.setattr("src.backend.data_server.get_db_path", lambda name: ":memory:")
    session = DataServer.get_session("test.db")
    assert isinstance(session, Session)

@pytest.mark.parametrize(
    "db_name",
    [
        "covid.db",
        "custom.db"
    ]
)
def test_serve_erd(db_name):
    exp = get_exp_data()
    server = DataServer(db_name)
    assert server.serve_erd() == exp['erds'][db_name]

@pytest.mark.parametrize(
    "table, db_name",
    [
        ("Date", "covid.db"),
        ("Source", "covid.db"),
        ("Deaths", "custom.db")
    ]
)
def test_serve_table(table, db_name):
    exp = get_exp_data()
    server = DataServer(db_name)
    assert server.serve_table(db_name, table.lower()) == [tuple(row) for row in exp["table_info"][table]]

# @pytest.mark.parametrize(
#     "db_name, table",
#     [
#         "custom.db", "MHCareCluster",
#         "deaths.db", "Deaths"
#     ]
# )
# def test_time_series(db_name, table):
#     server = DataServer(db_name)
#     data = server.serve_time_series([], db_name, table)
#     data = [list(x) for x in data]
#     exp = get_exp_data
#     assert data == exp["time_series"][table.lower()]

# def test_restr_distr():
#     pass

def test_serve_timeline():
    server = DataServer("covid.db")
    data = server.serve_timeline()
    converted = [[d.isoformat(), event, url] for d, event, url in data]
    exp = get_exp_data()
    assert converted == exp['timeline']

# def serve_second_series():
#     pass

def test_get_restrictions():
    server = DataServer("covid.db")
    assert server.get_restrictions() == ['schools_closed', 'pubs_closed', 'shops_closed', 'eating_places_closed', 'stay_at_home', 'household_mixing_indoors_banned', 'wfh', 'rule_of_6_indoors', 'curfew', 'eat_out_to_help_out']

def test_get_data_range():
    server = DataServer("covid.db")
    assert server.get_date_range() == (datetime.date(2020, 3, 1), datetime.date(2024, 1, 14))
