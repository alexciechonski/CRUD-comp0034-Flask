"""
This module provides utility functions to interact with files.

The `save_to_csv` function allows users to save a `pandas.DataFrame` or a dictionary to a CSV file.
It automatically converts the dictionary to a DataFrame before saving and supports specifying the
file name and file path for the output CSV.

The 'get_queries' function reads the queries from a text file and stores them in a list.
"""
from typing import Any
import pickle # Reference: https://docs.python.org/3/library/pickle.html
import pandas as pd 
def save_to_csv(data: Any, file_name: str, path: str) -> None:
    """
    Saves data to a CSV file, supporting both DataFrames and dictionaries.

    This function takes a `pandas.DataFrame` or a dictionary as input and saves it as a CSV file.
    If a dictionary is provided, it is first converted to a single-row DataFrame before saving.
    The resulting CSV file is saved to the specified path with the given file name.

    Parameters:
    - data (Any): The data to save, which can be either a `pandas.DataFrame` or a dictionary.
    - file_name (str): The name of the CSV file (without path).
    - path (str): The directory path where the CSV file will be saved.

    Returns:
    - None
    """
    path = f"{path}/{file_name}"
    if isinstance(data, pd.DataFrame):
        data.to_csv(path, index=False)
    elif isinstance(data, dict):
        converted_data = pd.DataFrame([data])
        converted_data.to_csv(path, index=False)

def get_queries(txt_file: str) -> list[str]:
    """
    Reads the queries from a text file into a python list of strings
    Parameters:
    - txt_file (str): file path of the file with queries

    Returns:
    - queries (list[str]): list of queries as strings
    """
    queries = []
    with open(txt_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        current_query = ""
        for line in lines:
            current_query += line
            if line.strip().endswith(';'):
                queries.append(current_query.strip())
                current_query = ""
    return queries

def read_expectation(test_num: int) -> Any:
    """
    Reads the expected output for a test case from a pickle file.

    Parameters:
        test_num (int): The test case number corresponding to the expected output file.

    Returns:
        Any: The expected output loaded from the pickle file.
    """
    path = f"coursework2/expectation/exp{test_num}.pkl"
    with open(path, 'rb') as file:
        exp = pickle.load(file)
    return exp
