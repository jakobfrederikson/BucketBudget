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
    
    app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

    # Flask Security - Enable version 2 of the registration form
    app.config['SECURITY_USE_REGISTER_V2'] = True

    # Flask Security - Set the password salt
    app.config['SECURITY_PASSWORD_SALT'] = os.environ['SECURITY_PASSWORD_SALT']

    # Flask Security - Enable user registration endpoint
    app.config['SECURITY_REGISTERABLE'] = True

    # Flask Security - Enable usernames
    app.config['SECURITY_USERNAME_ENABLE'] = True
    app.config['SECURITY_USERNAME_REQUIRED'] = True

    # Flask Security - Email verification
    app.config['SECURITY_CONFIRMABLE'] = True
    app.config['SECURITY_SEND_REGISTER_EMAIL'] = True    

    # Flask Security - Password endpoints (change password + recover/reset password)
    app.config['SECURITY_RECOVERABLE'] = True
    app.config['SECURITY_CHANGEABLE'] = True

    # Flask Security - 2FA
    # app.config['SECURITY_TWO_FACTOR_ENABLED_METHODS'] = ['email', 'authenticator']
    # app.config['SECURITY_TWO_FACTOR'] = True
    # app.config['SECURITY_TWO_FACTOR_ALWAYS_VALIDATE'] = False
    # app.config['SECURITY_TWO_FACTOR_LOGIN_VALIDITY'] = "1 week"    
    # app.config['SECURITY_TOTP_SECRETS'] = {"1": "TjQ9Qa31VOrfEzuPy4VHQWPCTmRzCnFzMKLxXYiZu9B"}
    # app.config['SECURITY_TOTP_ISSUER'] = "bucketbudget"

    # Flask Mail
    app.config['MAIL_SERVER'] = os.environ['MAIL_SERVER']
    app.config['MAIL_PORT'] = os.environ['MAIL_PORT']
    app.config['MAIL_USE_SSL'] = os.environ['MAIL_USE_SSL']
    app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
    app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
    app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

    # Flask Security - set email sender after Mail setup
    app.config['SECURITY_EMAIL_SENDER'] = app.config['MAIL_DEFAULT_SENDER']
    # app.config['SECURITY_TWO_FACTOR_RESCUE_MAIL'] = app.config['MAIL_DEFAULT_SENDER']

    mail = Mail(app)
    
    app.config['REMEMBER_COOKIE_SAMESITE'] = os.environ['REMEMBER_COOKIE_SAMESITE'] 
    app.config['SESSION_COOKIE_SAMESITE'] = os.environ['SESSION_COOKIE_SAMESITE']
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}

    csrf = CSRFProtect(app)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    from . import auth, budget
    from .auth import models as auth_models
    from .budget import models as budget_models
    from .auth.forms import CustomLoginForm, CustomRegisterForm

    # Init the db
    db.init_app(app)
    app.cli.add_command(init_db_command)

    # Create the tables
    with app.app_context():
        db.create_all()
    
    app.register_blueprint(budget.views.bp)

    user_datastore = SQLAlchemyUserDatastore(db, auth_models.User, auth_models.Role)
    app.security = Security(app, user_datastore)

    from bucketbudget.error_handlers import page_not_found
    app.register_error_handler(404, page_not_found)

    app.add_url_rule("/", endpoint="index")

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