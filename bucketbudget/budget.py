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
from bucketbudget.BudgetHandler.budget_handler import MoneyItem, Frequency

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

    expense_items = db.execute(
        'SELECT * FROM expense_item WHERE budget_id IS ?',
        (budget['id'],),
    ).fetchall()

    buckets = db.execute(
        'SELECT * FROM bucket WHERE budget_id IS ?',
        (budget['id'],),
    ).fetchall()

    result = get_result(budget, income_items, expense_items, buckets)

    context = {
        "budget": budget,
        "income_items": income_items,
        "expense_items": expense_items,
        "buckets": buckets,
        "result": result,
    }
    return render_template('budget/read.html', context=context)


def get_result(budget, income_items, expense_items, buckets) -> dict:
    income_money_items: list[MoneyItem] = _get_income_money_items(income_items)
    expense_money_items = _get_expense_money_items(expense_items)
    expense_bucket_money_items = _get_expense_bucket_money_items(expense_items)
    result = create_result(
        budget, 
        income_money_items, 
        expense_money_items, 
        expense_bucket_money_items, 
        buckets
    )
    
    return result


def create_result(
        budget, 
        income_money_items: list[MoneyItem], 
        expense_money_items: list[MoneyItem], 
        expense_bucket_money_items: list[MoneyItem],
        buckets
        ) -> dict:
    
    # Get the budget frequency
    budget_frequency: Frequency = _get_frequency(budget['frequency'])

    # Get total income, all amounts converted to the budget frequency
    total_income = 0
    for item in income_money_items:
        print(f"Income prior to conversion: {item.get_amount()}")
        print(f"Current income freq: {item.get_frequency()}")
        print(f"New freq: {budget_frequency}")
        item.convert_frequency_to(budget_frequency)
        print(f"Converting income to budget freq: {item.get_amount()}")
        total_income += item.get_amount()

    # Get total expenses, all amounts converted to the budget frequency
    total_expenses = 0
    for item in expense_money_items:
        item.convert_frequency_to(budget_frequency)
        total_expenses += item.get_amount()

    # Convert all expense bucket money items to the budget frequency
    for item in expense_bucket_money_items:
        item.convert_frequency_to(budget_frequency)
        total_expenses += item.get_amount()

    net_income = total_income - total_expenses

    all_buckets = []

    # Convert each expense bucket to a bucket item
    for item in expense_bucket_money_items:
        bucket_item = {
            "title": item.get_name(),
            "amount": item.get_amount(),
            "percent": "(fixed amount)",
        }
        all_buckets.append(bucket_item)

    # Get the percentage of net income for each bucket item
    # And get the total percentages of all buckets
    total_bucket_percentage = Decimal(0)
    for bucket in buckets:
        total_bucket_percentage += bucket['percent']

        percent_to_decimal = Decimal(bucket['percent'] / 100)

        bucket_item = {
            "title": bucket['title'],
            "amount": Decimal(percent_to_decimal * net_income).quantize(Decimal('0.01')),
            "percent": f"{bucket['percent']}%"
        }

        all_buckets.append(bucket_item)

    leftover_income = None
    leftover_bucket_percentage = Decimal(100 - total_bucket_percentage)
    if leftover_bucket_percentage != 0:
        decimal_from_percent = Decimal(leftover_bucket_percentage / 100)
        leftover_income = Decimal(decimal_from_percent * net_income).quantize(Decimal('0.01'))

    result = {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_income": net_income,
        "total_bucket_percentage": total_bucket_percentage,
        "leftover_income": leftover_income,
        "buckets": all_buckets
    }

    print(result)

    return result
    

def _get_expense_bucket_money_items(expense_items) -> list[MoneyItem]:
    expense_buckets: list[MoneyItem] = []

    for item in expense_items:
        if item['expense_bucket'] == 1:
            frequency = _get_frequency(item['frequency'])
            expense_buckets.append(
                MoneyItem(item['title'], Decimal(item['amount']), frequency)
            )
    
    return expense_buckets


def _get_expense_money_items(expense_items) -> list[MoneyItem]:
    expense_money_items = []
    for item in expense_items:
        if item['expense_bucket'] == 0:
            frequency = _get_frequency(item['frequency'])
            expense_money_items.append(
                MoneyItem(item['title'], Decimal(item['amount']), frequency)
            )
    return expense_money_items


def _get_income_money_items(income_items) -> list[MoneyItem]:
    income_money_items = []
    for item in income_items:
        frequency = _get_frequency(item['frequency'])
        income_money_items.append(
            MoneyItem(item['title'], Decimal(item['amount']), frequency)
        )
    return income_money_items


def _get_frequency(frequency: str) -> Frequency:
    if frequency == 'Weekly':
        return Frequency.WEEKLY
    elif frequency == 'Fortnightly':
        return Frequency.FORTNIGHTLY
    elif frequency == 'Four-Weekly':
        return Frequency.FOUR_WEEKLY
    elif frequency == 'Monthly':
        return Frequency.MONTHLY
    else:
        return Frequency.YEARLY


@bp.route('/budget/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    budget = get_budget(id)

    if request.method == 'POST':
        title = request.form['title']
        frequency = request.form['frequency']
        errors = []

        if not title:
            errors.append("Title is required.")
        if not frequency:
            errors.append("Frequency is required")

        if errors:
            for error in errors:
                flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE budget SET title = ?, frequency = ?'
                'WHERE id = ?',
                (title, frequency, id,)
            )
            db.commit()
            return redirect(url_for('budget.read', id=id))

    return render_template('budget/update.html', budget=budget)


@bp.route('/budget/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    """Delete a BucketBudget and all associated items."""
    get_budget(id)
    db = get_db()
    db.execute('DELETE FROM budget WHERE id = ?', (id,))
    db.commit()

    db.execute('DELETE FROM budget_member WHERE budget_id =?', (id,))
    db.commit()

    db.execute('DELETE FROM income_item WHERE budget_id =?', (id,))
    db.commit()

    db.execute('DELETE FROM expense_item WHERE budget_id =?', (id,))
    db.commit()

    db.execute('DELETE FROM bucket WHERE budget_id =?', (id,))
    db.commit()

    return redirect(url_for('budget.index'))


# ----------------------------
#           GETTERS
# ----------------------------

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


def get_income_item(id):
    income_item = get_db().execute(
        'SELECT * FROM income_item WHERE id = ?',
        (id,)
    ).fetchone()

    if income_item is None:
        abort(404, f"Income item id {id} doesn't exist.")

    return income_item


def get_expense_item(id):
    expense_item = get_db().execute(
        'SELECT * FROM expense_item WHERE id = ?',
        (id,)
    ).fetchone()

    if expense_item is None:
        abort(404, f"Expense item id {id} doesn't exist.")

    return expense_item


def get_bucket(id):
    bucket = get_db().execute(
        'SELECT * FROM bucket WHERE id = ?',
        (id,)
    ).fetchone()

    if bucket is None:
        abort(404, f"Budget id {id} doesn't exist.")

    return bucket


# ---------------------------------------------------------------------
#                 CRUD operations for budget items
# ---------------------------------------------------------------------

# ------------
# INCOME ITEMS
# ------------

@bp.route("/budget/<int:id>/income_item/create", methods=('GET', 'POST'))
@login_required
def create_income_item(id):
    if request.method == 'POST':
        budget = get_budget(id)
        title = request.form['title']
        amount = request.form['amount']
        frequency = request.form['frequency']
        split_income_decision = request.form.getlist('split_income')

        split_income = None

        if not split_income_decision:
            split_income = 0
        else:
            split_income = 1

        errors = []

        if not title:
            errors.append('Title is required')
        if not amount:
            errors.append('Amount is required')
        if not frequency:
            errors.append('Frequency is required')
            
        if errors:
            for error in errors:
                flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO income_item (budget_id, title, amount, frequency, split_income)'
                'VALUES (?, ?, ?, ?, ?)',
                (budget['id'], title, amount, frequency, split_income,),
            )
            db.commit()
            return redirect(url_for('budget.read', id=budget['id']))

    return render_template("budget/income_item_create.html")


@bp.route('/budget/<int:budget_id>/income_item/<int:income_item_id>/update', methods=('GET', 'POST'))
@login_required
def update_income_item(budget_id, income_item_id):
    income_item = get_income_item(income_item_id)

    if request.method == 'POST':
        title = request.form['title']
        amount = request.form['amount']
        frequency = request.form['frequency']
        split_income_decision = request.form.getlist('split_income')

        split_income = None

        if not split_income_decision:
            split_income = 0
        else:
            split_income = 1

        errors = []

        if not title:
            errors.append("Title is required.")
        if not amount:
            errors.append("Amount is required")
        if not frequency:
            errors.append("Frequency is required")

        if errors:
            for error in errors:
                flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE income_item SET title = ?, amount = ?, frequency = ?, split_income = ?'
                'WHERE id = ?',
                (title, amount, frequency, split_income, income_item_id,)
            )
            db.commit()
            return redirect(url_for('budget.read', id=budget_id))

    return render_template('budget/income_item_update.html', budget_id=budget_id, income_item=income_item)


@bp.route('/budget/<int:budget_id>/income_item/<int:income_item_id>/delete', methods=('POST',))
@login_required
def delete_income_item(budget_id, income_item_id):
    get_income_item(income_item_id)
    db = get_db()
    db.execute('DELETE FROM income_item WHERE id = ?', (income_item_id,))
    db.commit()
    return redirect(url_for('budget.read', id=budget_id))


# -------------
# EXPENSE ITEMS
# -------------


@bp.route("/budget/<int:id>/expense_item/create", methods=('GET', 'POST'))
@login_required
def create_expense_item(id):
    if request.method == 'POST':
        budget = get_budget(id)
        title = request.form['title']
        amount = request.form['amount']
        frequency = request.form['frequency']
        expense_bucket_decision = request.form.getlist('expense_bucket')

        expense_bucket = None

        if not expense_bucket_decision:
            expense_bucket = 0
        else:
            expense_bucket = 1

        errors = []

        if not title:
            errors.append('Title is required.')
        if not amount:
            errors.append('Amount is required.')
        if not frequency:
            errors.append('Frequency is required.')
        if expense_bucket is None:
            errors.append('Declare if this is an expense bucket or not.')
            
        if errors:
            for error in errors:
                flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO expense_item (budget_id, title, amount, frequency, expense_bucket)'
                'VALUES (?, ?, ?, ?, ?)',
                (budget['id'], title, amount, frequency, expense_bucket,),
            )
            db.commit()
            return redirect(url_for('budget.read', id=budget['id']))

    return render_template("budget/expense_item_create.html")


@bp.route('/budget/<int:budget_id>/expense_item/<int:expense_item_id>/update', methods=('GET', 'POST'))
@login_required
def update_expense_item(budget_id, expense_item_id):
    expense_item = get_expense_item(expense_item_id)

    if request.method == 'POST':
        title = request.form['title']
        amount = request.form['amount']
        frequency = request.form['frequency']
        expense_bucket_decision = request.form.getlist('expense_bucket')

        expense_bucket = None

        if not expense_bucket_decision:
            expense_bucket = 0
        else:
            expense_bucket = 1

        errors = []

        if not title:
            errors.append("Title is required.")
        if not amount:
            errors.append("Amount is required")
        if not frequency:
            errors.append("Frequency is required")
        if expense_bucket is None:
            errors.append('Declare if this is an expense bucket or not.')

        if errors:
            for error in errors:
                flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE expense_item SET title = ?, amount = ?, frequency = ?, expense_bucket = ?'
                'WHERE id = ?',
                (title, amount, frequency, expense_bucket, expense_item_id,)
            )
            db.commit()
            return redirect(url_for('budget.read', id=budget_id))

    return render_template('budget/expense_item_update.html', budget_id=budget_id, expense_item=expense_item)


@bp.route('/budget/<int:budget_id>/expense_item/<int:expense_item_id>/delete', methods=('POST',))
@login_required
def delete_expense_item(budget_id, expense_item_id):
    get_expense_item(expense_item_id)
    db = get_db()
    db.execute('DELETE FROM expense_item WHERE id = ?', (expense_item_id,))
    db.commit()
    return redirect(url_for('budget.read', id=budget_id))


# -------
# BUCKETS
#--------

@bp.route("/budget/<int:id>/bucket/create", methods=('GET', 'POST'))
@login_required
def create_bucket(id):
    if request.method == 'POST':
        budget = get_budget(id)
        title = request.form['title']
        percent = request.form['percent']

        errors = []

        if not title:
            errors.append('Title is required.')
        if not percent:
            errors.append('Percent is required.')
            
        if errors:
            for error in errors:
                flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO bucket (budget_id, title, percent)'
                'VALUES (?, ?, ?)',
                (budget['id'], title, percent,),
            )
            db.commit()
            return redirect(url_for('budget.read', id=budget['id']))


    return render_template("budget/bucket_create.html")

@bp.route('/budget/<int:budget_id>/bucket/<int:bucket_id>/update', methods=('GET', 'POST'))
@login_required
def bucket_update(budget_id, bucket_id):
    bucket = get_bucket(bucket_id)

    if request.method == 'POST':
        title = request.form['title']
        percent = request.form['percent']
        errors = []

        if not title:
            errors.append("Title is required.")
        if not percent:
            errors.append("Percent is required")

        if errors:
            for error in errors:
                flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE bucket SET title = ?, percent = ?'
                ' WHERE id = ?',
                (title, percent, bucket_id)
            )
            db.commit()
            return redirect(url_for('budget.read', id=budget_id))

    return render_template('budget/bucket_update.html', budget_id=budget_id, bucket=bucket)


@bp.route('/budget/<int:budget_id>/bucket/<int:bucket_id>/delete', methods=('POST',))
@login_required
def delete_bucket_item(budget_id, bucket_id):
    get_bucket(bucket_id)
    db = get_db()
    db.execute('DELETE FROM bucket WHERE id = ?', (bucket_id,))
    db.commit()
    return redirect(url_for('budget.read', id=budget_id))