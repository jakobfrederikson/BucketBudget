import os

from flask import Flask

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, 'bucketbudget.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    from . import budget, auth
    
    app.register_blueprint(budget.bp)
    app.register_blueprint(auth.bp)

    app.add_url_rule("/", endpoint="index")

    from . import db
    db.init_app(app)

    return app