from bucketbudget.BudgetHandler.budget_handler import (
    IncomeItem as _income_item, 
    ExpenseItem as _expense_item, 
    Frequency as _frequency
)

from bucketbudget import db
from bucketbudget.budget.forms import (
    CreateBudgetForm, 
    CreateIncomeItemForm,
    CreateExpenseItemForm,
    CreateBucketForm,
    JoinBudgetForm,
    DeleteBudgetMemberForm,
    ChangeBudgetOwnershipForm
)
from bucketbudget.budget.models import Budget, IncomeItem, ExpenseItem, Bucket, Frequency
from bucketbudget.budget_invite_code_maker import generate_unique_budget_name

from decimal import Decimal

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import session
from flask_security import auth_required, current_user

from werkzeug.exceptions import abort

from sqlalchemy import select

bp = Blueprint("budget", __name__)


@bp.route("/", methods=('GET', 'POST'))
def index():
    form = JoinBudgetForm(request.form)

    if request.method == 'POST' and form.validate():

        invite_code = form.invite_code.data
        budget = select(Budget).where(budget.invite_code == invite_code)
        print(budget)

        flash_message = None

        if budget is None:
            flash_message = f'No budget exists with invite code "{invite_code}"'
        else:
            members_in_budget = db.session.query(Budget).join(Budget.members).filter(Budget.id == budget.id).all()
            if not members_in_budget:
                db.execute(
                    'INSERT INTO budget_member (budget_id, user_id)'
                    'VALUES (?, ?)',
                    (budget['id'], g.user['id'],),
                )
                db.commit()
                flash_message = f'Successfully joined "{budget['title']}"'
            else:
                flash_message = f'You are already a member of "{budget.title}"'
        
        flash(flash_message)

    budgets = None
    print(current_user.is_authenticated)
    if current_user.is_authenticated:
        print("test")
        budgets = current_user.budgets
    return render_template("budget/index.html", budgets=budgets, form=form)


@bp.route('/budget/create', methods=('GET', 'POST'))
@auth_required()
def create():
    form = CreateBudgetForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        frequency = form.frequency.data

        budget = Budget(
            owner_id = current_user.id,
            title = form.title.data,
            invite_code = generate_unique_budget_name(form.title.data),
            frequency = form.frequency.data
        )

        budget.users.append(current_user)

        db.session.add(budget)
        db.session.commit()
        return redirect(url_for('index'))
        
    return render_template('budget/create.html', form=form)


@bp.route('/budget/<int:id>')
@auth_required()
def read(id):
    """View a budget."""
    budget = db.get_or_404(Budget, id)
    users_in_budget = db.session.query(Budget).join(Budget.users).filter(Budget.id == id).all()
    print(budget.users)
    print(users_in_budget)

    result = get_result(budget)

    context = {
        "budget": budget,
        "result": result,
    }

    return render_template('budget/read.html', context=context)


def get_result(budget) -> dict:
    income_money_items: list[_income_item] = _get_income_money_items(budget.income_items)
    expense_money_items: list[_expense_item] = _get_expense_money_items(budget.expense_items)
    result = create_result(
        budget, 
        income_money_items, 
        expense_money_items,
        budget.buckets
    )
    
    return result


def create_result(
        budget, 
        income_money_items: list[_income_item], 
        expense_money_items: list[_expense_item],
        buckets
        ) -> dict:
    
    # Get the budget frequency
    budget_frequency: Frequency = _get_frequency(budget.frequency)

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
            percent_to_decimal = Decimal(bucket.percent / 100)

            bucket_item = {
                "title": bucket.title,
                "amount": Decimal(percent_to_decimal * net_income).quantize(Decimal('0.01')),
                "percent": bucket.percent,
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


def _get_expense_money_items(expense_items) -> list[_expense_item]:
    expense_money_items = []
    for item in expense_items:
        frequency = _get_frequency(item.frequency)

        expense_money_items.append(
            _expense_item(
                item.title,
                Decimal(item.amount), 
                frequency,
                item.expense_bucket
            )
        )
    return expense_money_items


def _get_income_money_items(income_items) -> list[_income_item]:
    income_money_items = []
    for item in income_items:
        frequency = _get_frequency(item.frequency)

        income_money_items.append(
            _income_item(
                item.title,
                Decimal(item.amount), 
                frequency
            )
        )
    return income_money_items


def _get_frequency(frequency: str) -> _frequency:
    if frequency == 'Weekly':
        return _frequency.WEEKLY
    elif frequency == 'Fortnightly':
        return _frequency.FORTNIGHTLY
    elif frequency == 'FourWeekly':
        return _frequency.FOUR_WEEKLY
    elif frequency == 'Monthly':
        return _frequency.MONTHLY
    else:
        return _frequency.YEARLY


@bp.route('/budget/<int:id>/update', methods=('GET', 'POST'))
@auth_required()
def update(id):
    budget = db.get_or_404(Budget, id)
    form = CreateBudgetForm(request.form)

    if request.method == 'POST' and form.validate():
        budget.title = form.title.data
        budget.frequency = form.frequency.data

        db.session.add(budget)
        db.session.commit()
        return redirect(url_for('budget.read', id=id))

    form.title.data = budget.title
    form.frequency.data = budget.frequency.value

    return render_template('budget/update.html', budget=budget, form=form)


@bp.route('/budget/<int:id>/delete', methods=('POST',))
@auth_required()
def delete(id):
    """Delete a BucketBudget and all associated items."""
    budget = db.get_or_404(Budget, id)

    if request.method == "POST":
        db.session.delete(budget)
        db.session.commit()

    return redirect(url_for('budget.index'))


# ---------------------------------------------------------------------
#                 CRUD operations for budget items
# ---------------------------------------------------------------------

# --------------
# BUDGET MEMBERS
# --------------
@bp.route("/budget/<int:id>/budget_members", methods=("GET", "POST"))
@auth_required()
def view_budget_members(id):
    budget = get_budget(id)
    budget_members = get_budget_members(id)
    form = DeleteBudgetMemberForm(request.form)
    current_user_is_owner = (g.user['id'] == int(budget['owner_id']))

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


    return render_template("budget/budget_members.html", budget=budget, budget_members=budget_members, current_user_is_owner=current_user_is_owner, form=form)


@bp.route("/budget/<int:id>/budget_members/change_owner", methods=('GET', 'POST'))
@auth_required()
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
    
    current_user_is_owner = (g.user['id'] == int(budget['owner_id']))
    if not current_user_is_owner:
        flash("You are not the budger owner, you cannot access this page.")
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
@auth_required()
def create_income_item(id):
    form = CreateIncomeItemForm(request.form)
    if request.method == 'POST' and form.validate():
        budget = db.get_or_404(Budget, id)
        income_item = IncomeItem(
            budget_id = budget.id,
            title = form.title.data,
            amount = form.amount.data,
            frequency = form.frequency.data
        )
        db.session.add(income_item)
        db.session.commit()

        return redirect(url_for('budget.read', id=budget.id))

    
    return render_template("budget/income_item_create.html", form=form)


@bp.route('/budget/<int:budget_id>/income_item/<int:income_item_id>/update', methods=('GET', 'POST'))
@auth_required()
def update_income_item(budget_id, income_item_id):
    income_item = db.get_or_404(IncomeItem, income_item_id)
    form = CreateIncomeItemForm(request.form)

    if request.method == 'POST' and form.validate():
        income_item.title = form.title.data
        income_item.amount = form.amount.data
        income_item.frequency = form.frequency.data

        db.session.add(income_item)
        db.session.commit()
        return redirect(url_for('budget.read', id=budget_id))

    # Pre-populate form data
    form.title.data = income_item.title
    form.amount.data = income_item.amount
    form.frequency.data = income_item.frequency.value

    return render_template('budget/income_item_update.html', budget_id=budget_id, income_item=income_item, form=form)


@bp.route('/budget/<int:budget_id>/income_item/<int:income_item_id>/delete', methods=('POST',))
@auth_required()
def delete_income_item(budget_id, income_item_id):
    income_item = db.get_or_404(IncomeItem, income_item_id)

    if request.method == "POST":
        db.session.delete(income_item)
        db.session.commit()

    return redirect(url_for('budget.read', id=budget_id))


# -------------
# EXPENSE ITEMS
# -------------


@bp.route("/budget/<int:id>/expense_item/create", methods=('GET', 'POST'))
@auth_required()
def create_expense_item(id):
    form = CreateExpenseItemForm(request.form)

    if request.method == 'POST' and form.validate():
        budget = db.get_or_404(Budget, id)
        expense_item = ExpenseItem(
            budget_id = budget.id,
            title = form.title.data,
            amount = form.amount.data,
            frequency = form.frequency.data,
            expense_bucket = form.expense_bucket.data
        )
        db.session.add(expense_item)
        db.session.commit()

        return redirect(url_for('budget.read', id=budget.id))

    return render_template("budget/expense_item_create.html", form=form)


@bp.route('/budget/<int:budget_id>/expense_item/<int:expense_item_id>/update', methods=('GET', 'POST'))
@auth_required()
def update_expense_item(budget_id, expense_item_id):
    expense_item = db.get_or_404(ExpenseItem, expense_item_id)
    form = CreateExpenseItemForm(request.form)

    if request.method == 'POST' and form.validate():
        expense_item.title = form.title.data
        expense_item.amount = form.amount.data
        expense_item.frequency = form.frequency.data
        expense_item.expense_bucket = form.expense_bucket.data

        db.session.add(expense_item)
        db.session.commit()
        return redirect(url_for('budget.read', id=budget_id))

    # Pre-populate form data
    form.title.data = expense_item.title
    form.amount.data = expense_item.amount
    form.frequency.data = expense_item.frequency.value
    form.expense_bucket.data = expense_item.expense_bucket

    return render_template('budget/expense_item_update.html', budget_id=budget_id, expense_item=expense_item, form=form)


@bp.route('/budget/<int:budget_id>/expense_item/<int:expense_item_id>/delete', methods=('POST',))
@auth_required()
def delete_expense_item(budget_id, expense_item_id):
    expense_item = db.get_or_404(ExpenseItem, expense_item_id)

    if request.method == "POST":
        db.session.delete(expense_item)
        db.session.commit()   

    return redirect(url_for('budget.read', id=budget_id))


# -------
# BUCKETS
#--------

@bp.route("/budget/<int:id>/bucket/create", methods=('GET', 'POST'))
@auth_required()
def create_bucket(id):
    form = CreateBucketForm(request.form)

    if request.method == 'POST' and form.validate():
        budget = db.get_or_404(Budget, id)
        bucket = Bucket(
            budget_id = budget.id,
            title = form.title.data,
            percent = form.percent.data
        )
        db.session.add(bucket)
        db.session.commit()

        return redirect(url_for('budget.read', id=budget.id))


    return render_template("budget/bucket_create.html", form=form)

@bp.route('/budget/<int:budget_id>/bucket/<int:bucket_id>/update', methods=('GET', 'POST'))
@auth_required()
def bucket_update(budget_id, bucket_id):
    bucket = db.get_or_404(Bucket, bucket_id)
    form = CreateBucketForm(request.form)

    if request.method == 'POST' and form.validate():
        bucket.title = form.title.data
        bucket.percent = form.percent.data
        
        db.session.add(bucket)
        db.session.commit()
        return redirect(url_for('budget.read', id=budget_id))

    # Pre-populate form data
    form.title.data = bucket.title
    form.percent.data = bucket.percent

    return render_template('budget/bucket_update.html', budget_id=budget_id, bucket=bucket, form=form)


@bp.route('/budget/<int:budget_id>/bucket/<int:bucket_id>/delete', methods=('POST',))
@auth_required()
def delete_bucket_item(budget_id, bucket_id):
    bucket = db.get_or_404(Bucket, bucket_id)

    if request.method == "POST":
        db.session.delete(bucket)
        db.session.commit()   

    return redirect(url_for('budget.read', id=budget_id))