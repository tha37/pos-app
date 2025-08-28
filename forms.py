from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FloatField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    shop_name = StringField('Shop Name', validators=[DataRequired(), Length(min=2, max=120)])
    owner_password = PasswordField('Owner Password', validators=[DataRequired()])
    confirm_owner_password = PasswordField('Confirm Owner Password', validators=[DataRequired(), EqualTo('owner_password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired(), Length(max=120)])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    unit_price = FloatField('Unit Price', validators=[DataRequired()])
    submit = SubmitField('Add Item')

class SaleForm(FlaskForm):
    item_name = StringField('Item Name', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Sell Item')

class OwnerPasswordForm(FlaskForm):
    owner_password = PasswordField('Owner Password', validators=[DataRequired()])
    submit = SubmitField('Unlock Sales Report')