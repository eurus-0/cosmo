import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from routes import init_routes
# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure the database - use SQLite if no DATABASE_URL is provided
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    database_url = "sqlite:///pinspire.db"
    logging.warning(f"No DATABASE_URL found, using SQLite: {database_url}")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Set Supabase flags based on environment variables
app.config["SUPABASE_AVAILABLE"] = all([
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
])

if not app.config["SUPABASE_AVAILABLE"]:
    logging.warning("Supabase credentials not found, file uploads will be disabled")

# Initialize the database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

with app.app_context():
    # Import the models here so their tables are created
    import models  # noqa: F401
    
    # Create all tables
    db.create_all()
