from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import DataRequired, Email, InputRequired

class LoginForm(FlaskForm):
    email = StringField(label='Email', validators=[InputRequired(), Email(granular_message=True)])
    password = PasswordField(label='Password',validators=[InputRequired()])
    remember_me = BooleanField(label='Remember Me')
    submit = SubmitField(label="Log In")

class ContactForm(FlaskForm):
    email = StringField(validators=[InputRequired()])
    name = StringField(validators=[InputRequired()])
    address = StringField()
    phone = TelField(validators=[InputRequired()])
    subject = StringField(validators=[InputRequired()])
    message = TextAreaField(validators=[InputRequired()])
    submit = SubmitField()
