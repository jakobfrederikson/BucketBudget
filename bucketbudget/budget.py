from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import session
from werkzeug.exceptions import abort

from bucketbudget.auth import login_required
from bucketbudget.db import get_db

bp = Blueprint("budget", __name__)


@bp.route("/")
def index():
    """Dislay an empty budget."""
    print(f"Attempting to get session id: {session['user_id']}")
    return render_template("budget/index.html")

@bp.route('/budgets')
@login_required
def view_all_budgets():
    db = get_db()
    user_id = session.get('user_id')
    if user_id is not None:
        budgets = db.execute(
                'SELECT * FROM budget WHERE owner_id is ?', (user_id,)
            ).fetchall()
    else:
        budgets = None
    return render_template('budget/view_all.html', budgets=budgets)


@bp.route('/budget/create', methods=('GET', 'POST'))
@login_required
def create_budget():
    if request.method == 'POST':
        title = request.form['title']
        
        error = None
        
        if not title:
            error = 'Title is required'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO budget (owner_id, title)'
                'VALUES (?, ?)',
                (g.user['id'], title),
            )
            db.commit()
            return redirect(url_for('index'))
        
    return render_template('budget/create.html')