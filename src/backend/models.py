"""
SQLAlchemy models for the database tables.
"""
from sqlalchemy import create_engine, Column, Integer, String, Date as SQLDate, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Date(Base):
    __tablename__ = 'Date'

    date_id = Column(Integer, primary_key=True)
    date = Column(SQLDate, nullable=False)

    # Relationships
    daily_restrictions = relationship("DailyRestriction", back_populates="date")
    summary_restrictions = relationship("SummaryRestriction", back_populates="date")

class Restriction(Base):
    __tablename__ = 'Restriction'

    restriction_id = Column(Integer, primary_key=True)
    restriction = Column(String, nullable=False)

    # Relationships
    daily_restrictions = relationship("DailyRestriction", back_populates="restriction")

class DailyRestriction(Base):
    __tablename__ = 'DailyRestriction'

    daily_restriction_id = Column(Integer, primary_key=True)
    date_id = Column(Integer, ForeignKey('Date.date_id'), nullable=False)
    restriction_id = Column(Integer, ForeignKey('Restriction.restriction_id'), nullable=False)
    in_place = Column(Boolean, nullable=False)

    # Relationships
    date = relationship("Date", back_populates="daily_restrictions")
    restriction = relationship("Restriction", back_populates="daily_restrictions")

class Source(Base):
    __tablename__ = 'Source'

    source_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    source = Column(String, nullable=False)

    # Relationships
    summary_restrictions = relationship("SummaryRestriction", back_populates="source")

class SummaryRestriction(Base):
    __tablename__ = 'SummaryRestriction'

    summary_id = Column(Integer, primary_key=True)
    date_id = Column(Integer, ForeignKey('Date.date_id'), nullable=False)
    source_id = Column(Integer, ForeignKey('Source.source_id'), nullable=False)

    # Relationships
    date = relationship("Date", back_populates="summary_restrictions")
    source = relationship("Source", back_populates="summary_restrictions")

def init_db(database_url):
    """Initialize database connection and return session maker."""
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session

# Custom table model for dynamic tables
def create_custom_table(table_name, columns):
    """
    Dynamically create a SQLAlchemy model for a custom table.
    Args:
        table_name (str): Name of the table
        columns (list): List of column definitions [(name, type, constraints)]
    Returns:
        type: A new SQLAlchemy model class
    """
    attrs = {
        '__tablename__': table_name,
        '__table_args__': {'extend_existing': True},
        'id': Column(Integer, primary_key=True)
    }

    for col_name, col_type, constraints in columns:
        if col_type.lower() == 'integer':
            col = Column(Integer)
        elif col_type.lower() == 'float':
            col = Column(Float)
        elif col_type.lower() == 'date':
            col = Column(SQLDate)
        else:
            col = Column(String)

        if 'not null' in constraints.lower():
            col.nullable = False

        attrs[col_name] = col

    return type(table_name, (Base,), attrs)
