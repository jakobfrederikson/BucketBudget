from wtforms import Form, BooleanField, StringField, DecimalField, SelectField, PasswordField, validators


class RegistrationForm(Form):
    username = StringField('Username', [
        validators.DataRequired(),
        validators.Length(min=3, max=25),
    ])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match.')
    ])
    confirm = PasswordField('Repeat Password')


class LoginForm(Form):
    username = StringField('Username', [
        validators.DataRequired(),
        validators.Length(min=3, max=25),
    ])
    password = PasswordField('New Password', [
        validators.DataRequired()
    ])


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