# Project Overview #
The project is a PowerBI-like app for public health researchers and data scientists for creating simple statistical models to investigate
the effects of enforcing restrictions on chosen variables. 

# Table of Contents #
- [Functionality](#functionality)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [Dataset](#dataset)
- [Linting](#linting)

# Functionality #
The app consists of 6 pages, each with a unique functionality:
### Dataset ###
The dataset page consists of a CRUD functionality, which allows for creating, deleting and modifying tables through data insertion from csv. It also allows for creating and deleting databases. When inserting data the user has to follow a specific schema in order for it to be plotted later.

The databases are represented as an entity-relationship diagram and enable the user to view table properties by clicking on them.

### Table CRUD ###
This page offers a functionality of creating, updating and deleting records of a chosen table. The page supports modifications using the editable table or by filling out a form depending on the type of operation to be performed.

### Restriction Distribution ###
The restriction distribution page consists of interactive bar chart, which allows the user to specify a list of restrictions and an end date. The bar chart represents how many days each of the selected restrictions has been in place.

### Time Series ###
The time series page allows the user to graph the number of restrictions in time and plot it against any other variable from a table in one the databases to find patterns and correlation. It creates a linear regression model for the two variables and enables the usage of a local LLM to comment on the results.

### Audit Log ###
The audit log page allows the user to check the 10 latest CRUD modifications and revert them. 

### Timeline ###
The timeline page allows the users to see how restrictions have been enforced in time on a timeline and allows to view the source for each restriction by clicking on it.

# Project Structure #
```
comp0034-cw-alexciechonski/
│
├── .github/
│   └── workflows/
│        └── pytests.yml
├── src/
│   ├── backend/
│   │   ├── data/
│   │   │   ├── covid.db
│   │   │   ├── custom.db
│   │   │   └── deaths.db
│   │   ├── log/
│   │   │   ├── audit_log.json
│   │   │   ├── covid.db_state_backup.json
│   │   │   ├── custom.db_state_backup.json
│   │   │   ├── deaths.db_state_backup.json
│   │   │   └── log_manager.py
│   │   ├── validation/
│   │   │   ├── __init__.py
│   │   │   └── validator.py
│   │   ├── __init__.py
│   │   ├── data_server.py
│   │   ├── erd_manager.py
│   │   ├── models.py
│   │   ├── revert_manager.py
│   │   └── routes.py
│   ├── frontend/
│   │   ├── static/
│   │   │   └── css/
|   │   │      └── styles.css
│   │   ├── templates/
│   │   │   ├── audit_log.html
│   │   │   ├── base.html
│   │   │   ├── dataset.html
│   │   │   ├── index.html
│   │   │   ├── restriction_distribution.html
│   │   │   ├── table_crud.html
│   │   │   ├── time_series.html
│   │   │   └── timeline.html
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── dash_app.py
│   │   └── diagrams.py
│   ├── prediction/
│   │   └──pred.py
│   ├── testing/
│   │   ├── helpers/
│   │   │   ├── crawl_helpers.py
│   │   │   └── unit_helpers.py
│   │   ├── resources/
│   │   │   ├── bad_schema.csv
│   │   │   ├── deaths.csv
│   │   │   ├── MHCareCluster.csv
│   │   │   └── test.csv
│   │   ├── tests/
│   │   │   ├── unit
│   │   │   │   ├── test_app.py
│   │   │   │   ├── test_data_server.py
│   │   │   │   ├── test_erd_manager.py
│   │   │   │   ├── test_log_manager.py
│   │   │   │   ├── test_models.py
│   │   │   │   ├── test_revert_manager.py
│   │   │   │   ├── test_routes.py
│   │   │   │   ├── test_utils.py
│   │   │   │   └── test_validation.py
│   │   │   └── workflow
│   │   │       ├── test_crud.py
│   │   │       ├── test_dataset_flow.py
│   │   │       ├── test_restr_distr_flow.py
│   │   │       ├── test_time_serise_flow.py
│   │   │       └── test_timeline_flow.py
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   └── exp_outputs.json
│   ├── __init__.py
│   ├── config.json
│   ├── config.py
│   └── utils.py
├── venv/
│
├── .gitignore
├── coursework2.pdf
├── pyproject.toml
├── README.md
└── requirements.txt
```

# Setup and installation #
The setup for this project consists of 4 steps:
1. Clone the repository:
    ```
    git clone https://github.com/ucl-comp0035/comp0034-cw-alexciechonski
    cd comp0034-cw-alexciechonski
    ```

2. Create and activate a virtual environment:

    Mac OS/Linux:
    ```
    python3 -m venv venv
    source venv/bin/activate
    ```

    Windows:
    ```
    python3 -m venv venv
    venv\Scripts\activate
    ```

    If necessary select a Python interpreter related to the virtual environment by using Cmd+Shift+P (MacOS) or Ctrl+Shift+P (Windows)

3. Install the requirements
    ```
    pip install -r requirements.txt
    ```

4. Install graphviz

    MacOS:
    ```
    sudo apt-get install graphviz
    ```

    Windows:
    Follow the guide here:
    https://graphviz.org/download/

5. Install playwright browsers
    ```
    playwright install
    ```

6. Install ollama

    Follow the guide here:
    https://ollama.com/download

    then run:
    
    ```
    ollama run tinyllama
    ```

7. Install the project in editable mode
    ```
    pip install -e .
    ```

# Dataset #

The original dataset used in this project is sourced from https://data.london.gov.uk/dataset/covid-19-restrictions-timeseries. It is licensed under the UK Open Government Licence, which can be found here https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/.

### MHCareCluster ###
The MHCareCluster Dataset has been used as a metric of mental health. It has been derived from NHS Monthly Statistics:
 
NHS Digital, Mental Health Services Monthly Statistics, Performance December 2020, Provisional January 2021, Published 2021. Available at: https://digital.nhs.uk/data-and-information/publications/statistical/mental-health-services-monthly-statistics/performance-december-2020-provisional-january-2021. Licensed under the Open Government Licence v3.0

### Deaths ###
The Deaths dataset has been derived from the Financial Times Github repository:
Financial Times, Coronavirus Excess Mortality Data, GitHub Repository. Available at: https://github.com/Financial-Times/coronavirus-excess-mortality-data.

# Testing #
Tests have been designed to test each callback and each functionality.
To run them use:
```
pytest --cov=src/testing/tests --cov-report=term-missing
```
The results of the tests can be seen in the actions tab.

# Linting #
PyLint has been used for lining, ensuring the code meets the PEP8 Python style standards

