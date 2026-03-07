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

from decimal import Decimal

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


@bp.route('/budget/<int:id>')
@login_required
def read(id):
    """View a budget."""
    budget = get_budget(id)
    db = get_db()
    income_items = db.execute(
        'SELECT * FROM income_item WHERE budget_id IS ?',
        (budget['id'],),
    ).fetchall()

    context = {
        "budget": budget,
        "income_items": income_items,
        "expense_items": "expense_items",
        "buckets": "buckets",
        "result": "result"
    }
    return render_template('budget/read.html', context=context)


def get_budget(id):
    budget = get_db().execute(
        'SELECT * FROM budget b WHERE b.id = '
        '(SELECT budget_id FROM budget_member bm ' \
        'WHERE bm.budget_id = ? AND bm.user_id = ?)',
        (id, g.user['id'],)
    ).fetchone()

    if budget is None:
        abort(404, f"Budget id {id} doesn't exist.")

    return budget

@bp.route("/budget/<int:id>/income/create", methods=('GET', 'POST'))
@login_required
def create_income_item(id):
    if request.method == 'POST':
        budget = get_budget(id)
        title = request.form['title']
        amount = request.form['amount']
        frequency= request.form['frequency']

        errors = []

        if not title:
            errors.append('Title is required')
        if not amount:
            errors.append('Amount is required')
        if not frequency:
            errors.append('Frequency is required')

        print(f"{title}, {amount}, {frequency}")
            
        if errors:
            for error in errors:
                flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO income_item (budget_id, title, amount, frequency)'
                'VALUES (?, ?, ?, ?)',
                (budget['id'], title, amount, frequency,),
            )
            db.commit()
            return redirect(url_for('budget.read', id=budget['id']))


    return render_template("budget/income_item_create.html")