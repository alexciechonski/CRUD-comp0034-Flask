import datetime
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from src.backend.models import Base, Date, Restriction, DailyRestriction, Source, SummaryRestriction, create_custom_table

@pytest.fixture
def in_memory_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def test_model_tables_exist(in_memory_session):
    inspector = inspect(in_memory_session.bind)
    table_names = inspector.get_table_names()
    expected = {'Date', 'Restriction', 'DailyRestriction', 'Source', 'SummaryRestriction'}
    assert expected.issubset(set(table_names))

def test_relationships_can_be_instantiated(in_memory_session):
    date = Date(date_id=1, date=datetime.date(2020, 1, 1))
    restriction = Restriction(restriction_id=1, restriction="Lockdown")
    dr = DailyRestriction(daily_restriction_id=1, date=date, restriction=restriction, in_place=True)
    source = Source(source_id=1, name="Gov", source="gov.uk")
    sr = SummaryRestriction(summary_id=1, date=date, source=source)

    in_memory_session.add_all([date, restriction, dr, source, sr])
    in_memory_session.commit()

    loaded_date = in_memory_session.query(Date).first()
    assert len(loaded_date.daily_restrictions) == 1
    assert len(loaded_date.summary_restrictions) == 1

def test_create_custom_table():
    engine = create_engine("sqlite:///:memory:")
    CustomModel = create_custom_table("TestCustom", [
        ("time", "date", "NOT NULL"),
        ("measured_value", "float", "NOT NULL")
    ])
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    assert "TestCustom" in inspector.get_table_names()
    columns = [col['name'] for col in inspector.get_columns("TestCustom")]
    assert set(columns) == {"id", "time", "measured_value"}
