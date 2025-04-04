from src.backend.data_server import *
import pytest
from sqlalchemy.orm import Session
from src.testing.helpers.unit_helpers import get_exp_data
import datetime
from src.utils import get_db_path


def test_get_session_returns_valid_session(monkeypatch, test_db_path):
    monkeypatch.setattr("src.backend.data_server.get_db_path", lambda name: test_db_path)
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
        ("MHCareCluster", "custom.db")
    ]
)
def test_serve_table(table, db_name, test_data_server):
    exp = get_exp_data()
    assert test_data_server.serve_table(db_name, table.lower()) == [tuple(row) for row in exp["table_info"][table]]

def test_time_series(covid_server):
    data = covid_server.serve_time_series([])
    exp = get_exp_data()
    assert exp['restriction_series']['0-5'] == [list(t) for t in data[0:5]]
    assert exp['restriction_series']['100-105'] == [list(t) for t in data[100:105]]
    assert exp['restriction_series']['450-455'] == [list(t) for t in data[450:455]]
    assert exp['restriction_series']['750-755'] == [list(t) for t in data[750:755]]

def test_serve_second_series():
    server = DataServer("custom.db")
    data = server.serve_second_series("custom.db", "MHCareCluster")
    exp = get_exp_data()
    assert [list(t) for t in data] == exp['custom_var_data']

def test_serve_timeline(covid_server):
    data = covid_server.serve_timeline()
    converted = [[d.isoformat(), event, url] for d, event, url in data]
    exp = get_exp_data()
    assert converted == exp['timeline']

def test_get_restrictions(covid_server):
    assert covid_server.get_restrictions() == ['schools_closed', 'pubs_closed', 'shops_closed', 'eating_places_closed', 'stay_at_home', 'household_mixing_indoors_banned', 'wfh', 'rule_of_6_indoors', 'curfew', 'eat_out_to_help_out']

def test_get_data_range(covid_server):
    assert covid_server.get_date_range() == (datetime.date(2020, 3, 1), datetime.date(2024, 1, 14))

if __name__ == "__main__":
    server = DataServer("custom.db")
    end_date = '2021-06-15'
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    data = server.serve_restr_distr(end_date)
    print(data)

