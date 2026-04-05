from bucketbudget.BudgetHandler.budget_handler import (
    IncomeItem as _income_item, 
    ExpenseItem as _expense_item, 
    Frequency as _frequency
)

from bucketbudget import db
from bucketbudget.auth.models import User
from bucketbudget.budget.models import Budget, IncomeItem, ExpenseItem, Bucket, Frequency
from bucketbudget.budget_invite_code_maker import generate_unique_budget_name
from bucketbudget.decorators import member_in_budget_required

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
from sqlalchemy.orm import joinedload

bp = Blueprint("auth", __name__)

@bp.route("/user/<int:user_id>", methods=["GET"])
@auth_required()
def view_account(user_id):
    user = User.query.options(joinedload(User.budgets)).filter_by(id=user_id).first_or_404()
    
    return render_template("auth/view_account.html", user=user)