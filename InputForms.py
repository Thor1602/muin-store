from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import DataRequired, Email

class LoginForm(FlaskForm):
    email = StringField(label='Email', validators=[DataRequired(), Email(granular_message=True)])
    password = PasswordField(label='Password')
    remember_me = BooleanField(label='Remember Me')
    submit = SubmitField(label="Log In")

class ContactForm(FlaskForm):
    email = StringField(validators=[DataRequired()])
    name = StringField(validators=[DataRequired()])
    address = StringField()
    phone = TelField(validators=[DataRequired()])
    subject = StringField(validators=[DataRequired()])
    message = TextAreaField(validators=[DataRequired()])
    submit = SubmitField()
