from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

bp = Blueprint("budget", __name__)


@bp.route("/")
def index():
    """Dislay an empty budget."""
    return render_template("budget/index.html")