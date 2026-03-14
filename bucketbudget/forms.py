from wtforms import Form, BooleanField, StringField, DecimalField, SelectField, PasswordField, validators

frequency = SelectField(u'Frequency',
        [validators.DataRequired()],
        choices=[
            'Weekly', 
            'Fortnightly', 
            'Monthly', 
            'Four-Weekly', 
            'Yearly',
            ])


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