# Project Overview #
The project is a PowerBI-like app for public health researchers and data scientists for creating simple statistical models to investigate
the effects of enforcing restrictions on chosen variables. 

# Table of Contents #
- [Functionality](#functionality)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [Dataset](#dataset)
- [Project Limitations](#project-limitations-and-possible-improvements)
- [Linting](#linting)

# Functionality #
The app consists of 4 pages, each with a unique functionality:
### Dataset ###
The dataset page consists of a CRUD functionality, which allows for creating, deleting and modifying tables through data insertion from csv. The user has a choice to perform operations on the original database (covid.db), which contains data on restrictions enforced in time, or a custom database (custom.db), which contains 2 examplary tables with data.

The databases are represented as an entity-relationship diagram and enable the user to view table properties by clicking on them.

### Restriction Distribution ###
The restriction distribution page consists of interactive bar chart, which allows the user to specify a list of restrictions and end date and represents how many days each of the selected restrictions has been in place.

### Time Series ###
The time series page allows the user to graph the number of restrictions in time and plot it against any other variable from a table in one the databases to find patterns and correlation. It creates a linear regression model for the two variables and enables the usage of a local LLM to comment on the results.

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
│   │   │   └── graph.db
│   │   ├── __init__.py
│   │   ├── data_server.py
│   │   └── erd_manager.py
│   ├── frontend/
│   │   ├── assets/
│   │   │   └── styles.css
│   │   ├── pages/
│   │   │   ├── dataset.py
│   │   │   ├── home.py
│   │   │   ├── restriction_distribution.py
│   │   │   ├── time_series.py
│   │   │   └──timeline.py
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── diagrams.py
│   │   ├── index.py
│   │   └── input_validation.py
│   ├── prediction/
│   │   └──pred.py
│   ├── testing/
│   │   ├── helpers/
│   │   │   └──crud_actions.py
│   │   ├── resources/
│   │   │   ├── bad_schema.csv
│   │   │   ├── deaths.csv
│   │   │   └── test.csv
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── test_crud_exceptions.py
│   │   │   ├── test_crud.py
│   │   │   ├── test_distr.py
│   │   │   ├── test_navigation.py
│   │   │   ├── test_time_series.py
│   │   │   ├── test_timeline.py
│   │   │   └── test.workflow.py
│   │   └──__init__.py
│   ├── __init__.py
│   ├── config.json
│   ├── config.py
│   └── utils.py
├── venv/
│
├── .gitignore
├── coursework1.pdf
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

### Original Dataset ###
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

# Project Limitations and Possible Improvements #

The current version of the application works completely; however, there are a few improvements that can be made to optimize its performance and improve the user experience:

### Graph Database ###
To keep track of relationships and produce ERDs a graph.db has been implemented, which is a local sqlite file. It consists of tables to keep track of graphs, nodes, edges and edge types with its primary purpose being retrieving adjacency lists for each database. Usage of an API like GraphQL would improve the performance and simplify the code.

### ORM ###
The application does not use an ORM and instead executes all SQL queries directly, which impacts performance and reduces scalability. An ORM was not implemented due to the complexity introduced by graph.db, which stores tables from all databases along with their relationships. For that reason, more time was allocated to testing and other features to enhance the user experience, as the app is not designed to be large-scale. However, using an ORM like SQLAlchemy would improve both performance and scalability in the long run.

### Relationships ###
The app does not provide users with the ability to create relationships between tables through the GUI, which helps keep both the frontend and backend code simpler while making it easier to validate the schema of newly created tables. However, the database is designed in a way that allows for the implementation of this feature in the future. To support table creation based on foreign keys, a functionality would need to be added that lets users select specific fields from existing tables and include them as foreign keys in new tables. Additionally, users would need the ability to choose a combination of fields from multiple tables to send data to the machine learning pipeline. This could be done through an SQL console or an interactive table interface. Proper data validation should also be implemented on the backend. While adding this functionality would significantly increase the complexity of the app, it could improve data management and usability.

### Record Modification ###
The app does not allow the user to create, update and delete individual records; therefore, the only way to modify a table is by deleting it, creating it again and inserting a new csv file. Such implementaion simplifies the code; however, can make it difficult for users to fix errors in data. To improve the user experience a functionality can be added that allows the user to create, update and delete records in individual tables. 

### LLM Response Quality ###
The LLM runs locally using Ollama. The only open-source model that performs fast enough to maintain a smooth user experience is TinyLlama. However, this model is highly prone to hallucinations, particularly when handling complex queries. To improve accuracy, a more robust LLM could be hosted on a server, or an API could be used to fetch responses from more advanced models.

# Linting #
PyLint has been used for lining, ensuring the code meets the PEP8 Python style standards

