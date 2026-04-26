from wtforms import (Form, BooleanField, StringField, DecimalField, 
    SelectField, PasswordField, EmailField, HiddenField, validators,
    ValidationError)

class CreateBudgetForm(Form):
    title = StringField('Title', [
        validators.DataRequired(),
        validators.Length(min=3, max=25),
    ])
    frequency = SelectField(u'Frequency',
        [validators.DataRequired()],
        choices=[
            ('Weekly', 'Weekly'), 
            ('Fortnightly', 'Fortnightly'), 
            ('Monthly', 'Monthly'), 
            ('FourWeekly', 'Four-Weekly'), 
            ('Yearly', 'Yearly'),
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
            ('Weekly', 'Weekly'), 
            ('Fortnightly', 'Fortnightly'), 
            ('Monthly', 'Monthly'), 
            ('FourWeekly', 'Four-Weekly'), 
            ('Yearly', 'Yearly'),
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
            ('Weekly', 'Weekly'), 
            ('Fortnightly', 'Fortnightly'), 
            ('Monthly', 'Monthly'), 
            ('FourWeekly', 'Four-Weekly'), 
            ('Yearly', 'Yearly'),
        ])


class CreateBucketForm(Form):
    title = StringField('Title', [
        validators.DataRequired(),
        validators.Length(min=3, max=25),
    ])
    percent = DecimalField('Percent',
        [validators.Optional(),
        validators.NumberRange(min=0, max=100)],
        places=2,
    )
    is_expense_bucket = BooleanField('Is this an expense bucket?')

    def validate_percent(self, field):
        if not self.is_expense_bucket.data and field.data is None:
            raise ValidationError('Percentage is required for standard buckets.')


class JoinBudgetForm(Form):
    invite_code = StringField('Invite Code', [
        validators.DataRequired(),
    ])


class ChangeBudgetOwnershipForm(Form):
    members = SelectField('Budget Members', [validators.DataRequired()])


class DeleteBudgetMemberForm(Form):
    member_id = HiddenField(validators=[validators.DataRequired()])


