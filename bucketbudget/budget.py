from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
# from flask import send_file
from flask import session
from werkzeug.exceptions import abort

# from io import BytesIO

# import json

bp = Blueprint("budget", __name__)


@bp.route("/")
def index():
    """Dislay an empty budget."""
    return render_template("budget/index.html")

# This is a test function
# @bp.route("/download")
# def create_and_download_json_file():
#     """Download a JSON file."""
#     file_name = f'{session['cookie']}-budget.json'
#     file = open(file_name, "rb")    
#     return send_file(file, download_name="budget.json", as_attachment=True)

# def create_test_json_file():
#     data = {
#         "Income": {
#             "Person1": 100,
#             "Person2": 100,
#             "SideHustle": 25,
#         },
#     }

#     file = open(f'{session['cookie']}-budget.json', 'w')
#     file.write(json.dumps(data, indent=4))
#     file.close()