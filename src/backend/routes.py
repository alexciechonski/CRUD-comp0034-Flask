"""
Backend routes for the Flask application.

This module defines routes for handling restriction distribution and timeline views.
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request
from sqlalchemy import func, create_engine
from sqlalchemy.orm import sessionmaker
import plotly.graph_objects as go
from src.utils import get_db_path
from src.forms.end_date_form import RestrictionForm
from .models import Date, Restriction, DailyRestriction
from .data_server import DataServer

bp = Blueprint('restriction_distribution', __name__)

# Create engine and session factory
db_path = get_db_path("covid.db")
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)

# Initialize DataServer
data_server = DataServer("covid.db")

def format_restriction_name(name):
    """Format restriction name for display."""
    return name.replace('_', ' ').title()

@bp.route('/restriction-distribution', methods=['GET', 'POST'])
def restriction_distribution():
    form = RestrictionForm()

    if form.validate_on_submit():
        end_date = form.end_date.data
    else:
        # Handle GET or invalid POST
        raw_date = request.args.get('end_date', '2021-06-15')
        try:
            end_date = datetime.strptime(raw_date, '%Y-%m-%d').date()
            form.end_date.data = end_date  # pre-fill form
        except ValueError:
            end_date = date(2021, 6, 15)
            form.end_date.data = end_date

    # Default values
    labels, data = [], []
    total_restrictions = most_common_count = 0
    most_common, error, plot_html = "No data available", None, None

    session = Session()
    try:
        date_record = session.query(Date).filter(Date.date <= end_date).order_by(Date.date.desc()).first()

        if date_record is None:
            error = "No data available for the selected date"
        else:
            restriction_counts = session.query(
                Restriction.restriction,
                func.count(DailyRestriction.restriction_id).label('count')
            ).join(
                DailyRestriction, DailyRestriction.restriction_id == Restriction.restriction_id
            ).join(
                Date, DailyRestriction.date_id == Date.date_id
            ).filter(
                Date.date <= end_date,
                DailyRestriction.in_place.is_(True)
            ).group_by(
                Restriction.restriction
            ).order_by(
                func.count(DailyRestriction.restriction_id).desc()
            ).all()

            if restriction_counts:
                labels = [format_restriction_name(r.restriction) for r in restriction_counts]
                data = [r.count for r in restriction_counts]
                total_restrictions = sum(data)
                most_common = labels[0]
                most_common_count = data[0]

                fig = go.Figure(data=[
                    go.Bar(
                        x=labels,
                        y=data,
                        marker_color='rgba(75, 192, 192, 0.6)',
                        marker_line_color='rgb(75, 192, 192)',
                        marker_line_width=1,
                        text=data,
                        textposition='auto'
                    )
                ])
                fig.update_layout(
                    title='Global Restriction Patterns',
                    xaxis_title='Restriction Type',
                    yaxis_title='Number of Applications',
                    showlegend=False,
                    height=400,
                    margin=dict(l=60, r=20, t=40, b=100),
                    xaxis=dict(tickangle=-45, tickfont=dict(size=10)),
                    yaxis=dict(tickfont=dict(size=10)),
                    paper_bgcolor='white',
                    plot_bgcolor='white',
                )
                plot_html = fig.to_html(full_html=False, include_plotlyjs=True)
            else:
                error = "No restriction data found for the selected date"

    except Exception as e:
        print(f"Error: {e}")
        error = "An error occurred while processing the data"
    finally:
        session.close()

    return render_template('restriction_distribution.html',
                           form=form,
                           plot_html=plot_html,
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
