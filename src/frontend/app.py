"""
Main entry point for the Flask web application.

This module initializes and configures a Flask app, setting up its routes
and template rendering. It handles page-based navigation and serves
static assets.

Dependencies:
- Flask: Web framework for building web applications
- Jinja2: Template engine for rendering HTML
"""
import os
import sys
from pathlib import Path
from flask import Flask
from src.backend.routes import bp
from src.frontend.dash_app import create_dash_app

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize Dash app
dash_app = create_dash_app(app)

# Register blueprints
app.register_blueprint(bp, url_prefix='')

if __name__ == '__main__':
    app.run(debug=True)
