from flask_security.signals import user_registered
from flask import flash
from bucketbudget import db
from bucketbudget.budget.models import Frequency, Budget, IncomeItem, ExpenseItem, Bucket
from bucketbudget.budget_invite_code_maker import generate_unique_budget_name

from decimal import Decimal

# signals tut: https://www.compilenrun.com/docs/framework/flask/flask-advanced-features/flask-signals/
# Decorator Based Signal Subscriptions: https://flask.palletsprojects.com/en/stable/signals/#decorator-based-signal-subscriptions
# connect_via(app) doesn't even work? Why is it in Flask documentation? 

@user_registered.connect
def on_user_registration_create_default_budget(sender, user, **extra):
    """Create a default budget for the user on registration"""
    # Default Budget
    default_budget = Budget(
        owner = user,
        title = "Default Budget",
        invite_code = generate_unique_budget_name("Default Budget"),
        frequency_enum = Frequency.Fortnightly
    )
    default_budget.users.append(user)
    db.session.add(default_budget)
    
    db.session.flush()

    budget = Budget.query.filter_by(owner_id = user.id).first_or_404()
    default_income_item = IncomeItem(
        budget_id = budget.id,
        title = "Salary",
        amount = Decimal(1000),
        frequency_enum = Frequency.Fortnightly
    )
    db.session.add(default_income_item)
    default_expense_item = ExpenseItem(
        budget_id = budget.id,
        title = "Example Expense (Power)",
        amount = Decimal(200),
        frequency_enum = Frequency.FourWeekly,
        expense_bucket=True
    )
    db.session.add(default_expense_item)
    default_expense_item_2 = ExpenseItem(
        budget_id = budget.id,
        title = "Example Expense (Phone)",
        amount = Decimal(30),
        frequency_enum = Frequency.Monthly,
        expense_bucket=False
    )
    db.session.add(default_expense_item_2)
    bucket_de = Bucket(
        budget_id = budget.id,
        title = "Daily Expenses",
        percent = Decimal(60)
    )
    db.session.add(bucket_de)
    bucket_splurge = Bucket(
        budget_id = budget.id,
        title = "Splurge",
        percent = Decimal(10)
    )
    db.session.add(bucket_splurge)
    bucket_fe = Bucket(
        budget_id = budget.id,
        title = "Fire Extinguisher",
        percent = Decimal(20)
    )
    db.session.add(bucket_fe)
    bucket_smile = Bucket(
        budget_id = budget.id,
        title = "Smile",
        percent = Decimal(10)
    )
    db.session.add(bucket_smile)
    db.session.commit()
    flash("A default budget has been created for you.")