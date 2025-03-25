from flask import Blueprint, render_template, jsonify, request
from datetime import datetime
from sqlalchemy import func, create_engine
from sqlalchemy.orm import sessionmaker
from .models import Date, Restriction, DailyRestriction, init_db
from ..config import PATHS
from .data_server import DataServer
import os

bp = Blueprint('restriction_distribution', __name__)

# Create engine and session factory
db_path = os.path.abspath(PATHS["covid.db"])
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)

# Initialize DataServer
data_server = DataServer(
    db_path=PATHS["covid.db"],
    graph_path=PATHS["graph.db"],
    custom_path=PATHS["custom.db"]
)

def format_restriction_name(name):
    """Format restriction name for display."""
    return name.replace('_', ' ').title()

@bp.route('/restriction-distribution')
def restriction_distribution():
    """Render the restriction distribution page."""
    end_date = request.args.get('end_date', '2021-06-15')
    try:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        end_date = datetime.strptime('2021-06-15', '%Y-%m-%d').date()

    # Initialize default values for empty chart
    labels = []
    data = []
    total_restrictions = 0
    most_common = "No data available"
    most_common_count = 0
    error = None

    session = Session()
    try:
        print(f"Attempting to query database at: {db_path}")  # Debug print
        
        # Get the date_id for the end date
        date_record = session.query(Date).filter(Date.date <= end_date).order_by(Date.date.desc()).first()
        
        if date_record is None:
            print(f"No date record found for date: {end_date}")  # Debug print
            error = "No data available for the selected date"
        else:
            print(f"Found date record: {date_record.date}")  # Debug print
            
            # Get restriction counts up to the end date
            restriction_counts = session.query(
                Restriction.restriction,
                func.count(DailyRestriction.restriction_id).label('count')
            ).join(
                DailyRestriction,
                DailyRestriction.restriction_id == Restriction.restriction_id
            ).join(
                Date,
                DailyRestriction.date_id == Date.date_id
            ).filter(
                Date.date <= end_date,
                DailyRestriction.in_place == True
            ).group_by(
                Restriction.restriction
            ).order_by(
                func.count(DailyRestriction.restriction_id).desc()
            ).all()

            print(f"Query returned {len(restriction_counts)} restrictions")  # Debug print

            if restriction_counts:
                # Prepare data for the template
                labels = [format_restriction_name(r.restriction) for r in restriction_counts]
                data = [r.count for r in restriction_counts]
                
                # Calculate statistics
                total_restrictions = sum(data)
                most_common = labels[0] if labels else "No data available"
                most_common_count = data[0] if data else 0
            else:
                print("No restrictions found")  # Debug print
                error = "No restriction data found for the selected date"

    except Exception as e:
        print(f"Error in restriction_distribution: {str(e)}")  # Debug print
        error = "An error occurred while processing the data"
        # Keep empty chart data in case of error
    finally:
        session.close()

    # Debug print final values
    print(f"Final values - labels: {labels}, data: {data}, error: {error}")

    # Create a list of bar data by zipping labels and data
    bars = list(zip(labels, data))
    max_value = max(data) if data else 0

    return render_template('restriction_distribution.html',
                         bars=bars,
                         max_value=max_value,
                         total_restrictions=total_restrictions,
                         most_common=most_common,
                         most_common_count=most_common_count,
                         end_date=end_date.strftime('%Y-%m-%d'),
                         error=error)

@bp.route('/timeline')
def timeline():
    """Render the timeline page."""
    try:
        # Get timeline data from DataServer
        timeline_data = data_server.serve_timeline()
        
        # Sort events by date
        timeline_data.sort(key=lambda x: x[0])
        
        return render_template('timeline.html', events=timeline_data)
    except Exception as e:
        print(f"Error in timeline: {str(e)}")
        return render_template('timeline.html', events=[], error="An error occurred while loading the timeline data.") 