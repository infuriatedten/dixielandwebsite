from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField,
    SelectField, DecimalField, TextAreaField, IntegerField,
    RadioField
)
from wtforms.fields import DateField
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, ValidationError, NumberRange, Optional, URL
)
from datetime import datetime
from decimal import Decimal
from app.models import (
    User, UserRole, TransactionType, TaxBracket, TicketStatus,
    PermitApplicationStatus, MarketplaceListingStatus, VehicleRegion
)
from app.custom_validators import must_be_positive


class AccountForm(FlaskForm):
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    name = StringField('Account Name (Optional)', validators=[Optional(), Length(max=100)]) # Added
    balance = DecimalField('Initial Balance', places=2, validators=[DataRequired()])
    is_company = BooleanField('Is Company Account?', default=False) # Added
    currency = StringField('Currency', default='GDC', validators=[DataRequired(), Length(min=3, max=10)])
    submit = SubmitField('Create Account')

    def __init__(self, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        self.user_id.choices = [(u.id, u.username) for u in User.query.order_by(User.username).all()]


class ApplyPermitForm(FlaskForm):
    vehicle_type = StringField('Vehicle Type/Description', validators=[DataRequired(), Length(min=5, max=150)])
    route_details = TextAreaField('Proposed Route Details (From, Via, To)', validators=[DataRequired(), Length(min=10, max=1000)])
    travel_start_date = DateField('Travel Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    travel_end_date = DateField('Travel End Date', format='%Y-%m-%d', validators=[DataRequired()])
    user_notes = TextAreaField('Additional Notes for Your Application (Optional)', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Submit Permit Application')

    def validate_travel_end_date(self, field):
        if self.travel_start_date.data and field.data:
            if field.data < self.travel_start_date.data:
                raise ValidationError('Travel End Date cannot be before Travel Start Date.')
            if field.data == self.travel_start_date.data: # Or some minimum duration
                pass # Same day travel is allowed

    def validate_travel_start_date(self, field):
        if field.data and field.data < datetime.date(datetime.utcnow()): # Using datetime.date for comparison with DateField
             raise ValidationError('Travel Start Date cannot be in the past.')


class ApproveAuctionItemForm(FlaskForm):
    actual_starting_bid = DecimalField('Actual Starting Bid', places=2, validators=[DataRequired()])
    minimum_bid_increment = DecimalField('Minimum Bid Increment (Optional)', places=2, validators=[Optional(),])
    admin_notes = TextAreaField('Admin Notes (e.g., for rejection, or internal)', validators=[Optional(), Length(max=2000)])
    submit_approve = SubmitField('Approve & Start Auction')
    submit_reject = SubmitField('Reject Submission')

    def __init__(self, *args, **kwargs):
        super(ApproveAuctionItemForm, self).__init__(*args, **kwargs)
        if self.minimum_bid_increment.data is None:
            from flask import current_app
            self.minimum_bid_increment.data = current_app.config.get('AUCTION_DEFAULT_MIN_BID_INCREMENT', 1.00)


    def validate_actual_starting_bid(self, field):
        if field.data is not None and field.data <= 0:
            raise ValidationError('Actual starting bid must be a positive value.')

    def validate_minimum_bid_increment(self, field):
        if field.data is not None and field.data <= 0:
            raise ValidationError('Minimum bid increment must be a positive value if set.')


class CompanyForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired(), Length(min=3, max=128)])
    details = TextAreaField('Company Details', validators=[Optional(), Length(max=1024)])
    submit = SubmitField('Add Company')


class ContestTicketForm(FlaskForm):
    user_contest_reason = TextAreaField('Reason for Contesting (Please be specific)', validators=[DataRequired(), Length(min=20, max=2000)])
    submit = SubmitField('Submit Contestation')


class CreateListingForm(FlaskForm):
    item_name = StringField('Item Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description (Optional)', validators=[Optional(), Length(max=1000)])
    price = DecimalField('Price', places=2, validators=[DataRequired()])
    quantity = DecimalField('Quantity', places=2, validators=[DataRequired()])
    unit = StringField('Unit (e.g., items, liters, kg)', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Create Listing')


class EditBalanceForm(FlaskForm):
    amount = DecimalField('Amount to Add/Subtract (+/-)', places=2, validators=[DataRequired()])
    description = TextAreaField('Reason/Description', validators=[DataRequired(), Length(min=5, max=255)])
    submit = SubmitField('Update Balance')


class EditListingForm(FlaskForm):
    item_name = StringField('Item Name', validators=[DataRequired(), Length(min=3, max=150)])
    description = TextAreaField('Item Description', validators=[Optional(), Length(max=1000)])
    price = DecimalField('Price (per unit)', places=2, validators=[DataRequired()])
    quantity = DecimalField('Quantity Available', places=2, validators=[DataRequired()])
    unit = StringField('Unit', validators=[DataRequired(), Length(min=1, max=50)])
    submit = SubmitField('Update Listing')

    def validate_price(self, field):
        if field.data is not None and field.data <= 0:
            raise ValidationError('Price must be a positive value.')

    def validate_quantity(self, field):
        if field.data is not None and field.data <= 0:
            raise ValidationError('Quantity must be a positive value.')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Save')

    def __init__(self, original_email, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_email = original_email

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('This email is already in use.')


class EditRulesForm(FlaskForm):
    content_markdown = TextAreaField('Rules Content (Markdown Format)',
                                     validators=[DataRequired(), Length(min=20)],
                                     render_kw={'rows': 25, 'class': 'form-control'})
    submit = SubmitField('Save Rules')


class EditUserRoleForm(FlaskForm):
    role = SelectField('Role', choices=[(role.name, role.value) for role in UserRole], validators=[DataRequired()])
    submit = SubmitField('Update Role')


class FarmerForm(FlaskForm):
    submit = SubmitField('Register as Farmer')


class IssueTicketForm(FlaskForm):
    user_search = StringField('Username of Person to Ticket', validators=[DataRequired(), Length(min=3)])
    vehicle_id = StringField('Vehicle ID / License Plate', validators=[Optional(), Length(max=100)])
    violation_details = TextAreaField('Violation Details', validators=[DataRequired(), Length(min=10, max=1000)])
    fine_amount = DecimalField('Fine Amount', places=2, validators=[DataRequired()])
    submit = SubmitField('Issue Ticket')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class NewConversationForm(FlaskForm): # Admin to User
    user_search = StringField('Recipient Username', validators=[DataRequired(), Length(min=3)])
    subject = StringField('Subject', validators=[DataRequired(), Length(min=5, max=255)])
    message_body = TextAreaField('Message', validators=[DataRequired(), Length(min=10)], render_kw={'rows': 5})
    submit = SubmitField('Send Message')


class ParcelForm(FlaskForm):
    location = StringField('Parcel Location', validators=[DataRequired(), Length(min=3, max=256)])
    size = DecimalField('Parcel Size (in acres)', validators=[DataRequired()])
    submit = SubmitField('Add Parcel')


class PlaceBidForm(FlaskForm):
    bid_amount = DecimalField('Your Bid Amount', places=2, validators=[DataRequired()])
    submit = SubmitField('Place Bid')

    def __init__(self, current_highest_bid=None, starting_bid=None, min_increment=None, *args, **kwargs):
        super(PlaceBidForm, self).__init__(*args, **kwargs)
        self.current_highest_bid = current_highest_bid if current_highest_bid is not None else Decimal('0.00')
        self.starting_bid = starting_bid if starting_bid is not None else Decimal('0.00')
        self.min_increment = min_increment if min_increment is not None else Decimal('0.01')

    def validate_bid_amount(self, field):
        min_next_bid = self.current_highest_bid + self.min_increment
        if self.current_highest_bid == Decimal('0.00') and self.starting_bid > Decimal('0.00'):
            min_next_bid = self.starting_bid

        if field.data is None:
            raise ValidationError('Bid amount is required.')
        if field.data < min_next_bid:
            raise ValidationError(f'Your bid must be at least {min_next_bid:.2f} (current highest/starting + increment).')


class ProductForm(FlaskForm):
    price = DecimalField('Price', validators=[must_be_positive])
    quantity = IntegerField('Quantity', validators=[must_be_positive])


class RecordInspectionForm(FlaskForm):
    inspected_user_search = StringField('Inspected User\'s Username (Optional, if registered)', validators=[Optional(), Length(min=3)])
    vehicle_id = StringField('Vehicle ID / License Plate', validators=[DataRequired(), Length(min=3, max=100)])
    pass_status = RadioField('Inspection Result', choices=[('True', 'Pass'), ('False', 'Fail')],
                             validators=[DataRequired(message="Must select Pass or Fail.")], default='True')
    notes = TextAreaField('Inspection Notes (Required if Fail, details, reasons)', validators=[Optional(), Length(max=2000)])
    submit = SubmitField('Record Inspection')

    def validate_notes(self, field):
        if self.pass_status.data == 'False' and (not field.data or len(field.data.strip()) < 10):
            raise ValidationError('Detailed notes are required if the inspection result is Fail (min 10 characters).')


class RegisterVehicleForm(FlaskForm):
    vehicle_make = StringField('Vehicle Make (e.g., Ford, Volvo)', validators=[DataRequired(), Length(max=100)])
    vehicle_model = StringField('Vehicle Model (e.g., F-150, FH16)', validators=[DataRequired(), Length(max=100)])
    vehicle_type = StringField('Vehicle Type (e.g., Sedan, Truck, Tractor)', validators=[DataRequired(), Length(min=3, max=100)])
    vehicle_description = TextAreaField('Vehicle Description/Details (Optional)', validators=[Optional(), Length(max=255)])
    region_format = SelectField('License Plate Region',
                                choices=[(region.name, region.value) for region in VehicleRegion],
                                validators=[DataRequired()])
    submit = SubmitField('Register Vehicle')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class ReplyMessageForm(FlaskForm): # For both User and Admin
    message_body = TextAreaField('Your Reply', validators=[DataRequired(), Length(min=1)], render_kw={'rows': 5})
    submit = SubmitField('Send Reply')


class ResolveTicketForm(FlaskForm):
    new_status = SelectField('New Ticket Status',
                             choices=[
                                 (TicketStatus.RESOLVED_UNPAID.value, "Resolve: Fine Upheld (Unpaid)"),
                                 (TicketStatus.RESOLVED_DISMISSED.value, "Resolve: Dismiss Ticket"),
                                 (TicketStatus.CANCELLED.value, "Cancel Ticket (e.g., error in issuance)")
                             ],
                             validators=[DataRequired()])
    resolution_notes = TextAreaField('Admin Resolution Notes', validators=[DataRequired(), Length(min=10, max=2000)])
    submit = SubmitField('Update Ticket Status')


class ReviewPermitApplicationForm(FlaskForm):
    new_status = SelectField('Application Status', choices=[], validators=[DataRequired()]) # Choices populated in route
    permit_fee = DecimalField('Permit Fee (if approving)', places=2, validators=[Optional()])
    officer_notes = TextAreaField('Officer/Admin Notes (feedback to user or internal)', validators=[Optional(), Length(max=2000)])
    submit = SubmitField('Update Application Status')

    def __init__(self, *args, **kwargs):
        super(ReviewPermitApplicationForm, self).__init__(*args, **kwargs)
        from app.models import PermitApplicationStatus
        self.new_status.choices = [
            (PermitApplicationStatus.APPROVED_PENDING_PAYMENT.value, "Approve (Pending Payment)"),
            (PermitApplicationStatus.REQUIRES_MODIFICATION.value, "Requires Modification (Send back to user)"),
            (PermitApplicationStatus.REJECTED.value, "Reject Application"),
            (PermitApplicationStatus.CANCELLED_BY_ADMIN.value, "Cancel Application (Admin Action)")
        ]

    def validate_permit_fee(self, field):
        if self.new_status.data == PermitApplicationStatus.APPROVED_PENDING_PAYMENT.value:
            if field.data is None or field.data <= 0:
                raise ValidationError('A positive Permit Fee is required when approving an application.')
        elif field.data is not None and field.data < 0:
             raise ValidationError('Permit Fee cannot be negative.')


class SendMessageForm(FlaskForm):
    body = TextAreaField('Message', validators=[DataRequired(), Length(min=1, max=5000)])
    submit = SubmitField('Send Message')


class StartConversationForm(FlaskForm):
    user_search = StringField('Recipient Username', validators=[DataRequired(), Length(min=3)])
    subject = StringField('Subject', validators=[Optional(), Length(max=255)])
    initial_message_body = TextAreaField('Initial Message', validators=[DataRequired(), Length(min=5, max=5000)])
    submit = SubmitField('Start Conversation')


class SubmitAuctionItemForm(FlaskForm):
    item_name = StringField('Item Name', validators=[DataRequired(), Length(min=3, max=200)])
    item_description = TextAreaField('Item Description', validators=[DataRequired(), Length(min=10, max=2000)])
    suggested_starting_bid = DecimalField('Suggested Starting Bid (Optional, e.g., 10.00)', places=2, validators=[Optional()])
    image_url = StringField('Image URL (Optional, e.g., https://.../image.png)', validators=[Optional(), URL(message="Please enter a valid URL for the image."), Length(max=512)])
    submit = SubmitField('Submit Item for Auction Approval')

    def validate_suggested_starting_bid(self, field):
        if field.data is not None and field.data < 0:
            raise ValidationError('Suggested starting bid cannot be negative.')


class TaxBracketForm(FlaskForm):
    name = StringField('Bracket Name', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[Length(max=255)])
    min_balance = DecimalField('Minimum Balance (Inclusive)', places=2, validators=[DataRequired()])
    max_balance = DecimalField('Maximum Balance (Exclusive, leave blank for top tier)', places=2, validators=[Optional()])
    tax_rate = DecimalField('Tax Rate (Percentage, e.g., 1.5 for 1.5%)', places=2, validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Tax Bracket')


    def validate_max_balance(self, field):
        if field.data is not None and self.min_balance.data is not None:
            if field.data <= self.min_balance.data:
                raise ValidationError('Max Balance must be greater than Min Balance.')

    def validate_name(self, name):
        existing_bracket = TaxBracket.query.filter_by(name=name.data).first()
        if existing_bracket:
            if hasattr(self, 'obj') and self.obj and hasattr(self.obj, 'id') and existing_bracket.id != self.obj.id:
                 raise ValidationError('This tax bracket name is already in use.')
            elif not (hasattr(self, 'obj') and self.obj and hasattr(self.obj, 'id')):
                 raise ValidationError('This tax bracket name is already in use.')


class TransactionForm(FlaskForm):
    sender_account_id = IntegerField('Sender Account ID', validators=[DataRequired()])
    receiver_account_id = IntegerField('Receiver Account ID', validators=[DataRequired()])
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    transaction_type = SelectField(
        'Transaction Type',
        choices=[(t.name, t.value) for t in TransactionType],
        validators=[DataRequired()]
    )
    description = StringField('Description')
    submit = SubmitField('Submit')
