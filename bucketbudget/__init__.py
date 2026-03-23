import os

import click
from flask import Flask
from flask.cli import with_appcontext
from flask_wtf.csrf import CSRFProtect
from flask_security import Security, SQLAlchemyUserDatastore
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

    app.config['SECURITY_USERNAME_ENABLE'] = True
    app.config['SECURITY_USERNAME_REQUIRED'] = True
    app.config['SECURITY_PASSWORD_SALT'] = os.environ['SECURITY_PASSWORD_SALT']
    app.config['SECURITY_REGISTERABLE'] = True
    app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
    app.config['SECURITY_USE_REGISTER_V2'] = True
    app.config['SECURITY_RECOVERABLE'] = True
    app.config['SECURITY_CHANGEABLE'] = True
    app.config['SECURITY_CONFIRMABLE'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
    app.config['REMEMBER_COOKIE_SAMESITE'] = os.environ['REMEMBER_COOKIE_SAMESITE'] 
    app.config['SESSION_COOKIE_SAMESITE'] = os.environ['SESSION_COOKIE_SAMESITE']
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

    db.init_app(app)
    app.cli.add_command(init_db_command)

    with app.app_context():
        db.create_all()
    
    app.register_blueprint(budget.views.bp)
    app.register_blueprint(auth.views.bp)

    user_datastore = SQLAlchemyUserDatastore(db, auth_models.User, auth_models.Role)
    app.security = Security(app, user_datastore)

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