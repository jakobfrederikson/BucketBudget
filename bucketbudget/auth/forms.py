from flask_security import LoginForm, RegisterFormV2 
from wtforms import StringField, validators

class CustomLoginForm(LoginForm):
    username = StringField("Username", validators=[validators.DataRequired()])

    def validate(self, **kwargs):
        self.user = look

class CustomRegisterForm(RegisterFormV2):
    username = StringField("Username", validators=[validators.DataRequired()])