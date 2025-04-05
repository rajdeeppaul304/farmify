from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from datetime import datetime
db_name = "databasefile.db"
# for now using sqlite. Later will use postgreSQL.
app = Flask(__name__)
app.config['SECRET_KEY'] = "omaiwamoushindeiru"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_name}"


def datetime_format(value, format='%Y-%m-%d %H:%M:%S'):
    if isinstance(value, datetime):
        return value.strftime(format)
    return value

# Register the custom filter with Flask's Jinja environment
app.jinja_env.filters['datetime_format'] = datetime_format


db = SQLAlchemy(app)
def start():
    global app, db
    # FOR the standard user routes
    from .views import view_routes
    app.register_blueprint(view_routes)
    # FOR The Consumer
    from .consumer import consumer_routes
    app.register_blueprint(consumer_routes, url_prefix="/consumer")
    # Can make another blueprint for another level of user.
    from .auth import auth_routes, initialize_login
    with app.app_context():
        if not path.exists(db_name):
            db.create_all()
    initialize_login(app)
    app.register_blueprint(auth_routes)
    return app