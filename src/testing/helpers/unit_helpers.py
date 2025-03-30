import json 
from src.testing.conftest import EXP_OUTPUTS

def get_exp_data():
    with open(EXP_OUTPUTS, "r") as f:
        data = json.load(f)
    return data