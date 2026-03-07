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

    budgets = None
    if g.user is not None:
        db = get_db()
        budgets = db.execute(
                'SELECT * FROM budget WHERE id IN'
                 '(SELECT budget_id FROM budget_member WHERE user_id IS ?)', (g.user['id'],)
            ).fetchall()
        print(budgets)
    return render_template("budget/index.html", budgets=budgets)


@bp.route('/budget/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        frequency = request.form['frequency']
        
        error = None
        
        if not title:
            error = 'Title is required'
        if not frequency:
            error = 'Frequency is required'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO budget (owner_id, title, frequency)'
                'VALUES (?, ?, ?)',
                (g.user['id'], title, frequency),
            )
            db.commit()

            just_created_budget = db.execute(
                'SELECT * FROM budget ' \
                'WHERE owner_id IS ?' \
                'AND title IS ?' \
                'AND frequency IS ?', 
                (g.user['id'], title, frequency),
            ).fetchone()

            db.execute(
                'INSERT INTO budget_member (user_id, budget_id)'
                'VALUES (?, ?)',
                (g.user['id'], just_created_budget['id']),
            )
            db.commit()
            return redirect(url_for('index'))
        
    return render_template('budget/create.html')