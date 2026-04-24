import os

import click
from flask import Flask
from flask.cli import with_appcontext
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_security import Security, SQLAlchemyUserDatastore

# Create the SQLAlchemy object
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base (DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

from dotenv import load_dotenv
load_dotenv()

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ['SECRET_KEY'],
        SECURITY_PASSWORD_SALT=os.environ['SECURITY_PASSWORD_SALT'],
        SQLALCHEMY_DATABASE_URI=os.environ['DATABASE_URL'],
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        SECURITY_USE_REGISTER_V2=True,
        SECURITY_REGISTERABLE=True,
        SECURITY_USERNAME_ENABLE=True,
        SECURITY_USERNAME_REQUIRED=True,
        SECURITY_CONFIRMABLE=False,
        SECURITY_SEND_REGISTER_EMAIL=False,
        SECURITY_RECOVERABLE=True,
        SECURITY_CHANGEABLE=True,
        SECURITY_PASSWORD_COMPLEXITY_CHECKER=os.environ['SECURITY_PASSWORD_COMPLEXITY_CHECKER'],
        MAIL_SERVER=os.environ['MAIL_SERVER'],
        MAIL_PORT=os.environ['MAIL_PORT'],
        MAIL_USE_SSL=os.environ['MAIL_USE_SSL'],
        MAIL_USERNAME=os.environ['MAIL_USERNAME'],
        MAIL_PASSWORD=os.environ['MAIL_PASSWORD'],
        MAIL_DEFAULT_SENDER=os.environ['MAIL_USERNAME'],
        SECURITY_EMAIL_SENDER=os.environ['MAIL_USERNAME'],
        SECURITY_CHANGE_EMAIL=True,
        # SECURITY_TWO_FACTOR_ENABLED_METHODS = ['email', 'authenticator'],
        # SECURITY_TWO_FACTOR=True,
        # SECURITY_TWO_FACTOR_ALWAYS_VALIDATE=False,
        # SECURITY_TWO_FACTOR_LOGIN_VALIDITY="1 Week",
        # SECURITY_TOTP_SECRETS={"": ""},
        # SECURITY_TOTP_ISSUER="bucketbudget",
        # SECURITY_TWO_FACTOR_RESCUE_MAIL=os.environ['MAIL_USERNAME'],
        REMEMBER_COOKIE_SAMESITE=os.environ["REMEMBER_COOKIE_SAMESITE"],
        SESSION_COOKIE_SAMESITE=os.environ['SESSION_COOKIE_SAMESITE']
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    mail = Mail(app)
    csrf = CSRFProtect(app)
    db.init_app(app)
    app.cli.add_command(init_db_command)

    from . import auth, budget
    from .auth import models as auth_models
    from .budget import models as budget_models
    from .auth.forms import CustomLoginForm, CustomRegisterForm

    user_datastore = SQLAlchemyUserDatastore(db, auth_models.User, auth_models.Role)
    app.security = Security(app, user_datastore)
    
    app.register_blueprint(budget.views.bp)
    app.register_blueprint(auth.views.bp)

    # Create the tables
    with app.app_context():
        db.create_all()    

    from bucketbudget.error_handlers import page_not_found, forbidden
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(403, forbidden)

    app.add_url_rule("/", endpoint="index")

    with app.app_context():
        from .budget import signals

    return app


def init_db():
    db.drop_all()
    db.create_all()


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")