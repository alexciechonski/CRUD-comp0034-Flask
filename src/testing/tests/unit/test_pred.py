import pytest
from src.prediction.pred import Model
from src.testing.helpers.unit_helpers import get_exp_data

@pytest.mark.parametrize(
    "db_name, table",
    [
        ("custom.db", "MHCareCluster"),
        ("deaths.db", "deaths")
    ]
)
def test_prepare(db_name, table):
    model  = Model([], db_name, table)
    exp = get_exp_data()
    assert model.prepare()['custom_value'].tolist() == exp['prepped_reg_data'][table]

@pytest.mark.parametrize(
    "db_name, table",
    [
        ("custom.db", "MHCareCluster"),
        ("deaths.db", "deaths")
    ]
)
def test_train_linear(db_name, table):
    model  = Model([], db_name, table)
    exp = get_exp_data()
    assert model.train_linear()['predicted'].tolist() == exp['predicted_data'][table]

@pytest.mark.parametrize(
    "db_name, table",
    [
        ("custom.db", "MHCareCluster"),
        ("deaths.db", "deaths")
    ]
)
def test_get_correlation(db_name, table):
    model  = Model([], db_name, table)
    exp = get_exp_data()
    assert model.get_correlation() == exp['correlation_value'][table]
