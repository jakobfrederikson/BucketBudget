import functools

from flask import (
    flash, redirect, url_for, abort
)

from bucketbudget import db
from bucketbudget.budget.models import Budget
from flask_security import current_user

def member_in_budget_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('security.login'))
        
        budget = db.get_or_404(Budget, kwargs['budget_id'])

        if current_user not in budget.users:
            abort(403)

        return view(**kwargs)

    return wrapped_view