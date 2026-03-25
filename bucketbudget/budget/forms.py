from wtforms import (Form, BooleanField, StringField, DecimalField, 
    SelectField, PasswordField, EmailField, HiddenField, validators)

class CreateBudgetForm(Form):
    title = StringField('Title', [
        validators.DataRequired(),
        validators.Length(min=3, max=25),
    ])
    frequency = SelectField(u'Frequency',
        [validators.DataRequired()],
        choices=[
            'Weekly', 
            'Fortnightly', 
            'Monthly', 
            'Four-Weekly', 
            'Yearly',
            ])


class CreateIncomeItemForm(Form):
    title = StringField('Title', [
        validators.DataRequired(),
        validators.Length(min=3, max=25),
    ])
    amount = DecimalField('Amount',
        [validators.DataRequired()],
        places=2,
    )
    frequency = SelectField(u'Frequency',
        [validators.DataRequired()],
        choices=[
            'Weekly', 
            'Fortnightly', 
            'Monthly', 
            'Four-Weekly', 
            'Yearly',
            ])


class CreateExpenseItemForm(Form):
    title = StringField('Title', [
        validators.DataRequired(),
        validators.Length(min=3, max=25),
    ])
    amount = DecimalField('Amount',
        [validators.DataRequired()],
        places=2,
    )
    frequency = SelectField(u'Frequency',
        [validators.DataRequired()],
        choices=[
            'Weekly', 
            'Fortnightly', 
            'Monthly', 
            'Four-Weekly', 
            'Yearly',
            ])
    expense_bucket = BooleanField('Expense Bucket')


class CreateBucketForm(Form):
    title = StringField('Title', [
        validators.DataRequired(),
        validators.Length(min=3, max=25),
    ])
    percent = DecimalField('Percent',
        [validators.DataRequired(),
        validators.NumberRange(min=0, max=100)],
        places=2,
    )


class JoinBudgetForm(Form):
    invite_code = StringField('Invite Code', [
        validators.DataRequired(),
    ])


class ChangeBudgetOwnershipForm(Form):
    members = SelectField('Budget Members', [validators.DataRequired()])


class DeleteBudgetMemberForm(Form):
    member_id = HiddenField(validators=[validators.DataRequired()])


