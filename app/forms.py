from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SubmitField, BooleanField, DecimalField,
    IntegerField, SelectField, HiddenField, PasswordField, FloatField
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, EqualTo

# ------------- Account Management ------------- #

class EditAccountForm(FlaskForm):
    balance = FloatField('Balance', validators=[DataRequired()])
    is_company = BooleanField('Is Company')
    submit = SubmitField('Save Changes')

class EditBalanceForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    submit = SubmitField('Submit')

class EditBankForm(FlaskForm):
    bank_name = StringField('Bank Name', validators=[DataRequired()])
    account_number = StringField('Account Number', validators=[DataRequired()])
    routing_number = StringField('Routing Number', validators=[DataRequired()])
    submit = SubmitField('Update Bank Info')

# ------------- Inspection Management ------------- #

class EditInspectionForm(FlaskForm):
    pass_status = BooleanField('Passed Inspection')
    notes = TextAreaField('Inspection Notes')
    submit = SubmitField('Save Changes')

# ------------- Insurance Claim Management ------------- #

class EditInsuranceClaimForm(FlaskForm):
    status = SelectField('Status', choices=[], validators=[DataRequired()])
    payout_amount = FloatField('Payout Amount', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Changes')

# ------------- Permit Application Management ------------- #

class EditPermitForm(FlaskForm):
    status = SelectField('Status', choices=[], validators=[DataRequired()])
    permit_fee = FloatField('Permit Fee', validators=[Optional()])
    submit = SubmitField('Save Changes')

# ------------- Rules Management ------------- #

class EditRulesForm(FlaskForm):
    content_markdown = TextAreaField('Rules Content (Markdown)', validators=[DataRequired()])
    submit = SubmitField('Save Changes')

# ------------- Tax Bracket Management ------------- #

class EditTaxBracketForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    min_balance = FloatField('Minimum Balance', validators=[DataRequired()])
    max_balance = FloatField('Maximum Balance', validators=[DataRequired()])
    tax_rate = FloatField('Tax Rate (%)', validators=[DataRequired(), NumberRange(min=0, max=100)])
    is_active = BooleanField('Active')
    submit = SubmitField('Save Changes')

# ------------- Ticket Management ------------- #

class EditTicketForm(FlaskForm):
    fine_amount = FloatField('Fine Amount', validators=[DataRequired()])
    status = SelectField('Status', choices=[], validators=[DataRequired()])
    submit = SubmitField('Save Changes')

# ------------- User Management ------------- #
class DeleteUserForm(FlaskForm):
    submit = SubmitField('Delete')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField('Update')

class EditUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    role_id = SelectField('Role', coerce=int)
    submit = SubmitField('Update User')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SubmitField, BooleanField, DecimalField,
    IntegerField, SelectField, HiddenField, PasswordField, FloatField
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, EqualTo

# ------------- Account Management ------------- #

class EditAccountForm(FlaskForm):
    balance = FloatField('Balance', validators=[DataRequired()])
    is_company = BooleanField('Is Company')
    submit = SubmitField('Save Changes')

class EditBalanceForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    submit = SubmitField('Submit')

class EditBankForm(FlaskForm):
    bank_name = StringField('Bank Name', validators=[DataRequired()])
    account_number = StringField('Account Number', validators=[DataRequired()])
    routing_number = StringField('Routing Number', validators=[DataRequired()])
    submit = SubmitField('Update Bank Info')

# ------------- Inspection Management ------------- #

class EditInspectionForm(FlaskForm):
    pass_status = BooleanField('Passed Inspection')
    notes = TextAreaField('Inspection Notes')
    submit = SubmitField('Save Changes')

# ------------- Insurance Claim Management ------------- #

class EditInsuranceClaimForm(FlaskForm):
    status = SelectField('Status', choices=[], validators=[DataRequired()])
    payout_amount = FloatField('Payout Amount', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Changes')

# ------------- Permit Application Management ------------- #

class EditPermitForm(FlaskForm):
    status = SelectField('Status', choices=[], validators=[DataRequired()])
    permit_fee = FloatField('Permit Fee', validators=[Optional()])
    submit = SubmitField('Save Changes')

# ------------- Rules Management ------------- #

class EditRulesForm(FlaskForm):
    content_markdown = TextAreaField('Rules Content (Markdown)', validators=[DataRequired()])
    submit = SubmitField('Save Changes')

# ------------- Tax Bracket Management ------------- #

class EditTaxBracketForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    min_balance = FloatField('Minimum Balance', validators=[DataRequired()])
    max_balance = FloatField('Maximum Balance', validators=[DataRequired()])
    tax_rate = FloatField('Tax Rate (%)', validators=[DataRequired(), NumberRange(min=0, max=100)])
    is_active = BooleanField('Active')
    submit = SubmitField('Save Changes')

# ------------- Ticket Management ------------- #

class EditTicketForm(FlaskForm):
    fine_amount = FloatField('Fine Amount', validators=[DataRequired()])
    status = SelectField('Status', choices=[], validators=[DataRequired()])
    submit = SubmitField('Save Changes')

# ------------- User Management ------------- #
class DeleteUserForm(FlaskForm):
    submit = SubmitField('Delete')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField('Update')

class EditUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    role_id = SelectField('Role', coerce=int)
    submit = SubmitField('Update User')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
