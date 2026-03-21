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
from bucketbudget.forms import (CreateBudgetForm, CreateIncomeItemForm, 
CreateExpenseItemForm, CreateBucketForm, JoinBudgetForm, DeleteBudgetMemberForm,
ChangeBudgetOwnershipForm)
from bucketbudget.budget_invite_code_maker import generate_unique_budget_name

from decimal import Decimal
from bucketbudget.BudgetHandler.budget_handler import IncomeItem, ExpenseItem, Frequency

bp = Blueprint("budget", __name__)


@bp.route("/", methods=('GET', 'POST'))
def index():
    form = JoinBudgetForm(request.form)

    if request.method == 'POST' and form.validate():
        db = get_db()

        invite_code = form.invite_code.data
        budget = db.execute(
            'SELECT * FROM budget WHERE invite_code = ?',
            (invite_code,),
        ).fetchone()

        flash_message = None

        if budget is None:
            flash_message = f'No budget exists with invite code "{invite_code}"'
        else:
            bm_iem = db.execute(
                'SELECT * FROM budget_member WHERE budget_id = ? AND user_id = ?',
                (budget['id'], g.user['id'],),
            ).fetchone()
            if not bm_iem:
                db.execute(
                    'INSERT INTO budget_member (budget_id, user_id)'
                    'VALUES (?, ?)',
                    (budget['id'], g.user['id'],),
                )
                db.commit()
                flash_message = f'Successfully joined "{budget['title']}"'
            else:
                flash_message = f'You are already a member of "{budget['title']}"'
        
        flash(flash_message)

    budgets = None
    if g.user is not None:
        db = get_db()
        budgets = db.execute(
                'SELECT * FROM budget WHERE id IN'
                 '(SELECT budget_id FROM budget_member WHERE user_id IS ?)', (g.user['id'],)
            ).fetchall()
    return render_template("budget/index.html", budgets=budgets, form=form)


@bp.route('/budget/create', methods=('GET', 'POST'))
@login_required
def create():
    form = CreateBudgetForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        frequency = form.frequency.data

        db = get_db()
        db.execute(
            'INSERT INTO budget (owner_id, title, invite_code, frequency)'
            'VALUES (?, ?, ?, ?)',
            (g.user['id'], title, generate_unique_budget_name(title), frequency),
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
        
    return render_template('budget/create.html', form=form)


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
    income_money_items: list[IncomeItem] = _get_income_money_items(income_items)
    expense_money_items: list[ExpenseItem] = _get_expense_money_items(expense_items)
    result = create_result(
        budget, 
        income_money_items, 
        expense_money_items,
        buckets
    )
    
    return result


def create_result(
        budget, 
        income_money_items: list[IncomeItem], 
        expense_money_items: list[ExpenseItem],
        buckets
        ) -> dict:
    
    # Get the budget frequency
    budget_frequency: Frequency = _get_frequency(budget['frequency'])

    all_income_buckets = []
    for income in income_money_items:
        income.convert_frequency_to(budget_frequency)
        net_income = income.get_amount()
        total_expenses = 0
        for expense in expense_money_items:
            expense.convert_frequency_to(budget_frequency)
            net_income -= expense.get_amount()
            total_expenses += expense.get_amount()

        income_to_buckets = []
        expense_buckets = []
        for item in expense_money_items:
            if item.is_expense_bucket():
                expense_buckets.append(item)
        for bucket in expense_buckets:
            bucket_item = {
                "title": bucket.get_name(),
                "amount": bucket.get_amount(),
                "percent": "(fixed amount)",
            }
            income_to_buckets.append(bucket_item)

        for bucket in buckets:
            percent_to_decimal = Decimal(bucket['percent'] / 100)

            bucket_item = {
                "title": bucket['title'],
                "amount": Decimal(percent_to_decimal * net_income).quantize(Decimal('0.01')),
                "percent": bucket['percent'],
            }
            income_to_buckets.append(bucket_item)

        all_income_buckets.append({
            "income_name": income.get_name(),
            "net_income": net_income,
            "total_expenses": total_expenses,
            "buckets": income_to_buckets,
        })
    

    result = {
        "all_income_buckets": all_income_buckets
    }

    print(result)

    return result


def _get_expense_money_items(expense_items) -> list[ExpenseItem]:
    expense_money_items = []
    for item in expense_items:
        frequency = _get_frequency(item['frequency'])

        expense_money_items.append(
            ExpenseItem(
                item['title'],
                Decimal(item['amount']), 
                frequency,
                item['expense_bucket']
            )
        )
    return expense_money_items


def _get_income_money_items(income_items) -> list[IncomeItem]:
    income_money_items = []
    for item in income_items:
        frequency = _get_frequency(item['frequency'])

        income_money_items.append(
            IncomeItem(
                item['title'],
                Decimal(item['amount']), 
                frequency
            )
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
    form = CreateBudgetForm(request.form)

    if request.method == 'POST' and form.validate():
        title = form.title.data
        frequency = form.frequency.data

        db = get_db()
        db.execute(
            'UPDATE budget SET title = ?, frequency = ?'
            'WHERE id = ?',
            (title, frequency, id,)
        )
        db.commit()
        return redirect(url_for('budget.read', id=id))

    form.title.data = budget['title']
    form.frequency.data = budget['frequency']

    return render_template('budget/update.html', budget=budget, form=form)


@bp.route('/budget/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    """Delete a BucketBudget and all associated items."""
    get_budget(id)
    db = get_db()

    # Delete budget
    db.execute('DELETE FROM budget WHERE id = ?', (id,))
    db.commit()

    # Delete associated budget_member rows with budget
    db.execute('DELETE FROM budget_member WHERE budget_id =?', (id,))
    db.commit()

    # Delete associated income_item rows with budget
    db.execute('DELETE FROM income_item WHERE budget_id =?', (id,))
    db.commit()

    # Delete associated expense_item rows with budget
    db.execute('DELETE FROM expense_item WHERE budget_id =?', (id,))
    db.commit()

    # Delete associated bucket rows with budget
    db.execute('DELETE FROM bucket WHERE budget_id =?', (id,))
    db.commit()

    return redirect(url_for('budget.index'))


# ----------------------------
#           GETTERS
# ----------------------------

def get_user(id):
    user = get_db().execute(
        'SELECT * FROM user WHERE id = ?',
        (id,),
    ).fetchone()

    if user is None:
        abort(404, f"User id {id} doesn't exist.")

    return user


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


def get_budget_members(id):
    budget_members = get_db().execute(
        'SELECT * FROM user u WHERE u.id IN'
        '(SELECT user_id FROM budget_member bm WHERE bm.budget_id = ?)',
        (id,),
    ).fetchall()

    if budget_members is None:
        abort(404, f"Budget id {id} doesn't exist.")
    
    return budget_members


def get_budget_member(budget_id, user_id):
    budget_member = get_db().execute(
        'SELECT * FROM budget_member bm WHERE bm.budget_id = ? AND bm.user_id = ?',
        (budget_id, user_id,),
    ).fetchone()

    if budget_member is None:
        abort(404, f"Budget member in budget {budget_id} with ID {user_id} doesn't exist.")

    return budget_member


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
        abort(404, f"Bucket id {id} doesn't exist.")

    return bucket


# ---------------------------------------------------------------------
#                 CRUD operations for budget items
# ---------------------------------------------------------------------

# --------------
# BUDGET MEMBERS
# --------------
@bp.route("/budget/<int:id>/budget_members", methods=("GET", "POST"))
@login_required
def view_budget_members(id):
    budget = get_budget(id)
    budget_members = get_budget_members(id)
    form = DeleteBudgetMemberForm(request.form)
    if request.method == 'POST' and form.validate():
        error = None
        member_id = int(form.member_id.data)

        if g.user['id'] != int(budget['owner_id']):
            flash('You cannot remove members.')
            error = True

        if int(member_id) == g.user['id']:
            flash('You cannot remove yourself.')
            error = True

        if not error:
            db = get_db()
            user = db.execute(
                'SELECT * FROM user WHERE id = ?',
                (member_id,),
            ).fetchone()

            db.execute(
                'DELETE FROM budget_member WHERE user_id = ?',
                (member_id,),
            )
            db.commit()
            flash(f"{user['username']} has been removed from the budget.")
            return redirect(url_for('budget.view_budget_members', id=id))


    return render_template("budget/budget_members.html", budget=budget, budget_members=budget_members, form=form)


@bp.route("/budget/<int:id>/budget_members/change_owner", methods=('GET', 'POST'))
@login_required
def change_budget_owner(id):
    budget = get_budget(id)
    budget_members = get_budget_members(id)
    form = ChangeBudgetOwnershipForm(request.form)
    form.members.choices = [(bm['id'], bm['username']) for bm in budget_members]
    
    if request.method == 'POST' and form.validate():
        error = None
        user_id = form.members.data
        chosen_user = get_user(user_id)

        if g.user['id'] != int(budget['owner_id']):
            flash('You cannot remove members.')
            error = True

        if int(chosen_user['id']) == g.user['id']:
            flash('You cannot choose yourself.')
            error = True

        if not error:
            db = get_db()
            user = db.execute(
                'SELECT * FROM user WHERE id = ?',
                (int(chosen_user['id']),),
            ).fetchone()

            db.execute(
                'UPDATE budget SET owner_id = ?'
                'WHERE id = ?',
                (user['id'], id,),
            )
            db.commit()
            flash(f"{user['username']} is now the onwer of the budget.")
            return redirect(url_for('budget.view_budget_members', id=id))
    

    return render_template("budget/budget_member_change_owner.html", budget=budget, form=form)

# change budget owner
# - check if current user is budget owner
# > if yes, then change the budget owner to whoever the selected user is
# > if selected user doesn't exist, stop and flash user not exist
# -- if no, then do nothing and flash you must be the owner

# leave budget
# - check if current user is budget owner
# > if yes, have they selected a user to transfer ownership
# > > if yes, then change budget owner and remove user from budget
# > - if no, flash that a user must selected as owner
# -- if not user selected for transfer, then flash user must be selected

# ------------
# INCOME ITEMS
# ------------

@bp.route("/budget/<int:id>/income_item/create", methods=('GET', 'POST'))
@login_required
def create_income_item(id):
    form = CreateIncomeItemForm(request.form)
    if request.method == 'POST':
        budget = get_budget(id)
        title = form.title.data
        amount = form.amount.data
        frequency = form.frequency.data
            
        if form.validate():
            db = get_db()
            db.execute(
                'INSERT INTO income_item (budget_id, title, amount, frequency)'
                'VALUES (?, ?, ?, ?)',
                (budget['id'], title, float(amount), frequency,),
            )
            db.commit()
            return redirect(url_for('budget.read', id=budget['id']))

    
    return render_template("budget/income_item_create.html", form=form)


@bp.route('/budget/<int:budget_id>/income_item/<int:income_item_id>/update', methods=('GET', 'POST'))
@login_required
def update_income_item(budget_id, income_item_id):
    income_item = get_income_item(income_item_id)
    form = CreateIncomeItemForm(request.form)

    if request.method == 'POST' and form.validate():
        title = form.title.data
        amount = form.amount.data
        frequency = form.frequency.data

        db = get_db()
        db.execute(
            'UPDATE income_item SET title = ?, amount = ?, frequency = ?'
            'WHERE id = ?',
            (title, float(amount), frequency, income_item_id,)
        )
        db.commit()
        return redirect(url_for('budget.read', id=budget_id))

    # Pre-populate form data
    form.title.data = income_item['title']
    form.amount.data = income_item['amount']
    form.frequency.data = income_item['frequency']

    return render_template('budget/income_item_update.html', budget_id=budget_id, income_item=income_item, form=form)


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
    form = CreateExpenseItemForm(request.form)
    if request.method == 'POST':
        budget = get_budget(id)
        title = form.title.data
        amount = form.amount.data
        frequency = form.frequency.data
        expense_bucket = form.expense_bucket.data

        if form.validate():
            db = get_db()
            db.execute(
                'INSERT INTO expense_item (budget_id, title, amount, frequency, expense_bucket)'
                'VALUES (?, ?, ?, ?, ?)',
                (budget['id'], title, float(amount), frequency, expense_bucket,),
            )
            db.commit()
            return redirect(url_for('budget.read', id=budget['id']))

    return render_template("budget/expense_item_create.html", form=form)


@bp.route('/budget/<int:budget_id>/expense_item/<int:expense_item_id>/update', methods=('GET', 'POST'))
@login_required
def update_expense_item(budget_id, expense_item_id):
    expense_item = get_expense_item(expense_item_id)
    form = CreateExpenseItemForm(request.form)

    if request.method == 'POST' and form.validate():
        title = form.title.data
        amount = form.amount.data
        frequency = form.frequency.data
        expense_bucket = form.expense_bucket.data

        db = get_db()
        db.execute(
            'UPDATE expense_item SET title = ?, amount = ?, frequency = ?, expense_bucket = ?'
            'WHERE id = ?',
            (title, float(amount), frequency, expense_bucket, expense_item_id,)
        )
        db.commit()
        return redirect(url_for('budget.read', id=budget_id))

    # Pre-populate form data
    form.title.data = expense_item['title']
    form.amount.data = expense_item['amount']
    form.frequency.data = expense_item['frequency']
    form.expense_bucket.data = expense_item['expense_bucket']

    return render_template('budget/expense_item_update.html', budget_id=budget_id, expense_item=expense_item, form=form)


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
    form = CreateBucketForm(request.form)
    if request.method == 'POST':
        budget = get_budget(id)
        title = form.title.data
        percent = form.percent.data

        if form.validate():
            db = get_db()
            db.execute(
                'INSERT INTO bucket (budget_id, title, percent)'
                'VALUES (?, ?, ?)',
                (budget['id'], title, float(percent),),
            )
            db.commit()
            return redirect(url_for('budget.read', id=budget['id']))


    return render_template("budget/bucket_create.html", form=form)

@bp.route('/budget/<int:budget_id>/bucket/<int:bucket_id>/update', methods=('GET', 'POST'))
@login_required
def bucket_update(budget_id, bucket_id):
    bucket = get_bucket(bucket_id)
    form = CreateBucketForm(request.form)

    if request.method == 'POST' and form.validate():
        title = form.title.data
        percent = form.percent.data
        
        db = get_db()
        db.execute(
            'UPDATE bucket SET title = ?, percent = ?'
            ' WHERE id = ?',
            (title, float(percent), bucket_id)
        )
        db.commit()
        return redirect(url_for('budget.read', id=budget_id))

    # Pre-populate form data
    form.title.data = bucket['title']
    form.percent.data = bucket['percent']

    return render_template('budget/bucket_update.html', budget_id=budget_id, bucket=bucket, form=form)


@bp.route('/budget/<int:budget_id>/bucket/<int:bucket_id>/delete', methods=('POST',))
@login_required
def delete_bucket_item(budget_id, bucket_id):
    get_bucket(bucket_id)
    db = get_db()
    db.execute('DELETE FROM bucket WHERE id = ?', (bucket_id,))
    db.commit()
    return redirect(url_for('budget.read', id=budget_id))