import enum
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.enums import ConversationStatus
from app.enums import ConversationStatus, MarketplaceListingStatus

class UserRole(enum.Enum):
    USER = "user"
    OFFICER = "officer"
    ADMIN = "admin"

class User(UserMixin, db.Model):
    __tablename__ = 'users' # Explicitly naming the table

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False) # Added email
    password_hash = db.Column(db.String(256), nullable=False) # Increased length for future hash algorithms
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)

    # Relationships (examples, will be built out in respective modules)
    # accounts = db.relationship('Account', backref='owner', lazy='dynamic')
    # tickets_issued = db.relationship('Ticket', foreign_keys='Ticket.issued_by_officer_id', backref='issuer', lazy='dynamic')
    # tickets_received = db.relationship('Ticket', foreign_keys='Ticket.issued_to_user_id', backref='recipient', lazy='dynamic')
    # permit_applications = db.relationship('PermitApplication', backref='applicant', lazy='dynamic')
    # marketplace_listings = db.relationship('MarketplaceListing', backref='seller', lazy='dynamic')
    # inspections_conducted = db.relationship('Inspection', foreign_keys='Inspection.officer_user_id', backref='inspecting_officer', lazy='dynamic')
    # inspections_on_user = db.relationship('Inspection', foreign_keys='Inspection.inspected_user_id', backref='inspected_party', lazy='dynamic')

    # Discord Integration fields
    discord_user_id = db.Column(db.String(100), nullable=True, unique=True, index=True) # Discord's Snowflake ID for bot interactions
    discord_username = db.Column(db.String(100), nullable=True) # Discord username#discriminator, for display or lookup

    # User Profile Region
    region = db.Column(db.Enum('US', 'EU', 'OTHER_DEFAULT', name='region_enum'), nullable=True, default='OTHER_DEFAULT')


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role.value})>'

from datetime import datetime

# Placeholder for other models to be added in future steps
class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=0.00, nullable=False) # Using Numeric for currency
    currency = db.Column(db.String(10), default="GDC", nullable=False) # Game Dollar Credits
    last_updated_on = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Potentially: admin_id who last updated, if needed for audit.
    # last_updated_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    user = db.relationship('User', backref=db.backref('accounts', lazy='dynamic'))
    transactions = db.relationship('Transaction', backref='account', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Account {self.id} for User {self.user_id} - {self.balance} {self.currency}>'

class TransactionType(enum.Enum):
    INITIAL_SETUP = "initial_setup"
    ADMIN_DEPOSIT = "admin_deposit"
    ADMIN_WITHDRAWAL = "admin_withdrawal"
    TICKET_PAYMENT = "ticket_payment"
    PERMIT_FEE = "permit_fee"
    MARKETPLACE_SALE = "marketplace_sale"
    MARKETPLACE_PURCHASE = "marketplace_purchase"
    TAX_PAYMENT = "tax_payment" # User-initiated tax payment (if we had that)
    AUTOMATED_TAX_DEDUCTION = "automated_tax_deduction" # For the new automated system
    PERMIT_FEE_PAYMENT = "permit_fee_payment" # For paying vehicle permits. This was already added in the previous step plan.
    AUCTION_WIN_DEBIT = "auction_win_debit" # Deduction from auction winner's account
    AUCTION_SALE_CREDIT = "auction_sale_credit" # Credit to auction seller's account
    # Add other transaction types as needed for new features
    OTHER = "other"

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    type = db.Column(db.Enum(TransactionType), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False) # Positive for deposits/credits, negative for withdrawals/debits
    description = db.Column(db.String(255))

    # Potentially: admin_id who processed this, if it's an admin-initiated one
    # processed_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return f'<Transaction {self.id} ({self.type.value}) of {self.amount} for Account {self.account_id}>'


# Update User model to have a backref to accounts
User.accounts_collection = db.relationship('Account', backref='owner_user', lazy='dynamic', foreign_keys=[Account.user_id])
# If using admin_id fields in Account/Transaction:
# User.admin_account_updates = db.relationship('Account', backref='admin_updater', lazy='dynamic', foreign_keys=[Account.last_updated_by_admin_id])
# User.admin_transactions_processed = db.relationship('Transaction', backref='admin_processor', lazy='dynamic', foreign_keys=[Transaction.processed_by_admin_id])


# --- Tax System Models ---
class TaxType(db.Model):
    __tablename__ = 'tax_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    amount = db.Column(db.Numeric(10, 2), nullable=False) # Fixed amount for the tax
    frequency = db.Column(db.String(50)) # e.g., "One-Time", "Annual", "Monthly" - informational
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    payments = db.relationship('TaxPaymentLog', backref='tax_type', lazy='dynamic')

    def __repr__(self):
        return f'<TaxType {self.name} - {self.amount}>'

class TaxPaymentLog(db.Model):
    __tablename__ = 'tax_payment_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tax_type_id = db.Column(db.Integer, db.ForeignKey('tax_types.id'), nullable=False)
    amount_paid = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    banking_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), unique=True, nullable=False) # Link to the debit transaction

    user = db.relationship('User', backref=db.backref('tax_payments', lazy='dynamic'))
    banking_transaction = db.relationship('Transaction', backref=db.backref('tax_payment_log_entry', uselist=False)) # one-to-one

    def __repr__(self):
        return f'<TaxPaymentLog ID: {self.id} - User: {self.user_id} paid {self.amount_paid} for TaxType: {self.tax_type_id}>'

# Add backref to User model for tax payments
User.tax_payment_logs = db.relationship('TaxPaymentLog', backref='payer', lazy='dynamic', foreign_keys=[TaxPaymentLog.user_id])


# --- Tax System Models (Revised for Automated, Balance-Based Taxes) ---
class TaxBracket(db.Model):
    __tablename__ = 'tax_brackets'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    min_balance = db.Column(db.Numeric(10, 2), nullable=False, index=True)  # Minimum balance to qualify for this bracket (inclusive)
    max_balance = db.Column(db.Numeric(10, 2), nullable=True, index=True)   # Maximum balance for this bracket (exclusive). Null for top tier.
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False)  # Percentage, e.g., 1.5 for 1.5%
    # Frequency is implicitly weekly based on user requirement, managed by scheduler. Field could be added if more flexibility needed later.
    # frequency = db.Column(db.String(50), default='WEEKLY', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)

    deduction_logs = db.relationship('AutomatedTaxDeductionLog', backref='tax_bracket', lazy='dynamic')

    def __repr__(self):
        return f'<TaxBracket {self.name} ({self.tax_rate}%) for balances {self.min_balance} to {self.max_balance if self.max_balance else "infinity"}>'

class AutomatedTaxDeductionLog(db.Model):
    __tablename__ = 'automated_tax_deduction_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    tax_bracket_id = db.Column(db.Integer, db.ForeignKey('tax_brackets.id'), nullable=False)
    balance_before_deduction = db.Column(db.Numeric(10, 2), nullable=False)
    tax_rate_applied = db.Column(db.Numeric(5,2), nullable=False) # Store the rate at the time of deduction
    amount_deducted = db.Column(db.Numeric(10, 2), nullable=False)
    deduction_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    banking_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), unique=True, nullable=False)

    user = db.relationship('User', backref=db.backref('automated_tax_deductions', lazy='dynamic'))
    banking_transaction = db.relationship('Transaction', backref=db.backref('automated_tax_deduction_log_entry', uselist=False))

    def __repr__(self):
        return f'<AutomatedTaxDeductionLog ID: {self.id} - User: {self.user_id} deducted {self.amount_deducted}>'

# Update User model backref
User.automated_tax_deduction_logs = db.relationship('AutomatedTaxDeductionLog', backref='taxed_user', lazy='dynamic', foreign_keys=[AutomatedTaxDeductionLog.user_id])

# Remove old TaxType and TaxPaymentLog if they were committed and need replacing
# This would ideally be a migration. For now, we assume they might not have been if we are iterating quickly.
# If they were, running this will error if old tables exist. We'd need a migration script.
# For sandbox, we can assume we're redefining.

# --- DOT Ticket System Models ---
class TicketStatus(enum.Enum):
    OUTSTANDING = "Outstanding"         # Newly issued, awaiting payment or contest
    PAID = "Paid"                       # Fine has been paid
    CONTESTED = "Contested"             # User has chosen to fight the ticket
    CANCELLED = "Cancelled"             # Officer or Admin cancelled the ticket
    RESOLVED_UNPAID = "Resolved - Unpaid" # Contested, admin ruled fine is due
    RESOLVED_DISMISSED = "Resolved - Dismissed" # Contested, admin ruled in favor of user

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    issued_to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    issued_by_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    vehicle_id = db.Column(db.String(100), nullable=True) # e.g., license plate or in-game vehicle identifier
    violation_details = db.Column(db.Text, nullable=False)
    fine_amount = db.Column(db.Numeric(10, 2), nullable=False)

    issue_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False) # To be set at 72 hours from issue_date

    status = db.Column(db.Enum(TicketStatus), default=TicketStatus.OUTSTANDING, nullable=False, index=True)

    user_contest_reason = db.Column(db.Text, nullable=True) # Reason provided by user if contested
    resolution_notes = db.Column(db.Text, nullable=True)   # Notes from admin after reviewing a contested ticket
    resolved_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Admin who resolved it

    banking_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), unique=True, nullable=True) # Link to payment transaction

    # Relationships
    issued_to = db.relationship('User', foreign_keys=[issued_to_user_id], backref=db.backref('tickets_received', lazy='dynamic'))
    issued_by = db.relationship('User', foreign_keys=[issued_by_officer_id], backref=db.backref('tickets_issued', lazy='dynamic'))
    resolved_by_admin = db.relationship('User', foreign_keys=[resolved_by_admin_id], backref=db.backref('tickets_resolved', lazy='dynamic'))
    payment_transaction = db.relationship('Transaction', backref=db.backref('ticket_payment_entry', uselist=False))

    def __repr__(self):
        return f'<Ticket {self.id} for User {self.issued_to_user_id} - Status: {self.status.value}>'


# Update User model for ticket relationships
User.tickets_received_collection = db.relationship('Ticket', foreign_keys=[Ticket.issued_to_user_id], backref='recipient_user', lazy='dynamic')
User.tickets_issued_collection = db.relationship('Ticket', foreign_keys=[Ticket.issued_by_officer_id], backref='issuing_officer_user', lazy='dynamic')
User.tickets_resolved_collection = db.relationship('Ticket', foreign_keys=[Ticket.resolved_by_admin_id], backref='resolving_admin_user', lazy='dynamic')


from datetime import datetime
from enum import Enum
from app import db

class PermitApplicationStatus(Enum):
    PENDING_REVIEW = "Pending Review"
    REQUIRES_MODIFICATION = "Requires Modification"
    APPROVED_PENDING_PAYMENT = "Approved - Pending Payment"
    PAID_AWAITING_ISSUANCE = "Paid - Awaiting Issuance"
    ISSUED = "Issued"
    REJECTED = "Rejected"
    CANCELLED_BY_USER = "Cancelled by User"
    CANCELLED_BY_ADMIN = "Cancelled by Admin"

from datetime import datetime
from app import db
from app.enums import PermitApplicationStatus  # Ensure this enum is imported properly

class PermitApplication(db.Model):
    __tablename__ = 'permit_applications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    vehicle_type = db.Column(db.String(150), nullable=False)
    route_details = db.Column(db.Text, nullable=False)

    travel_start_date = db.Column(db.Date, nullable=False)
    travel_end_date = db.Column(db.Date, nullable=False)

    user_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Correct name

    status = db.Column(db.Enum(PermitApplicationStatus), default=PermitApplicationStatus.PENDING_REVIEW, nullable=False, index=True)

    permit_fee = db.Column(db.Numeric(10, 2), nullable=True)
    officer_notes = db.Column(db.Text, nullable=True)

    reviewed_by_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    banking_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), unique=True, nullable=True)

    issued_permit_id_str = db.Column(db.String(100), nullable=True, unique=True)
    issued_on_date = db.Column(db.DateTime, nullable=True)
    issued_by_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    applicant = db.relationship('User', foreign_keys=[user_id], backref=db.backref('permit_applications', lazy='dynamic'))
    reviewer_officer = db.relationship('User', foreign_keys=[reviewed_by_officer_id], backref=db.backref('permits_reviewed', lazy='dynamic'))
    issuer_officer = db.relationship('User', foreign_keys=[issued_by_officer_id], backref=db.backref('permits_issued', lazy='dynamic'))
    payment_transaction = db.relationship('Transaction', backref=db.backref('permit_fee_payment_entry', uselist=False))

    def __repr__(self):
        return f'<PermitApplication {self.id} for User {self.user_id} - Status: {self.status.value}>'


# Add relationships to User model (assuming User is defined elsewhere)
User.permit_applications_collection = db.relationship(
    'PermitApplication', foreign_keys=[PermitApplication.user_id],
    backref='applicant_user', lazy='dynamic'
)
User.permits_reviewed_collection = db.relationship(
    'PermitApplication', foreign_keys=[PermitApplication.reviewed_by_officer_id],
    backref='reviewing_officer_user', lazy='dynamic'
)
User.permits_issued_collection = db.relationship(
    'PermitApplication', foreign_keys=[PermitApplication.issued_by_officer_id],
    backref='issuing_permit_officer_user', lazy='dynamic'
)


# --- Marketplace Models ---
class MarketplaceItemStatus(enum.Enum):
    AVAILABLE = "Available"
    SOLD_PENDING_RELIST = "Sold - More Available (Relist Soon)"  # User indicated more stock, but this item instance sold
    SOLD_OUT = "Sold Out"  # All stock sold
    CANCELLED = "Cancelled"  # Seller removed listing

class MarketplaceListing(db.Model):
    __tablename__ = 'marketplace_listings'
    id = db.Column(db.Integer, primary_key=True)
    seller_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    item_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)  # e.g., 0.5 for half liter
    unit = db.Column(db.String(50), nullable=False)  # e.g., "liters", "item(s)"

    status = db.Column(db.Enum(MarketplaceItemStatus), default=MarketplaceItemStatus.AVAILABLE, nullable=False, index=True)

    creation_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_update_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    discord_message_id = db.Column(db.String(100), nullable=True)  # Optional: Discord message ID

    # Relationships
    seller = db.relationship('User', backref=db.backref('marketplace_listings', lazy='dynamic'))

    def __repr__(self):
        return f'<MarketplaceListing {self.id}: {self.quantity} {self.unit} of {self.item_name} by User {self.seller_user_id} for {self.price}>'

# Optionally in User model:
# User.marketplace_listings_collection = db.relationship(
#     'MarketplaceListing', foreign_keys=[MarketplaceListing.seller_user_id],
#     backref='listing_seller_user', lazy='dynamic'
# )


# --- DOT Inspection System Models ---
class Inspection(db.Model):
    __tablename__ = 'inspections'
    id = db.Column(db.Integer, primary_key=True)

    officer_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    inspected_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)

    vehicle_id = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    pass_status = db.Column(db.Boolean, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    officer = db.relationship('User', foreign_keys=[officer_user_id], backref=db.backref('inspections_conducted', lazy='dynamic'))
    inspected_user = db.relationship('User', foreign_keys=[inspected_user_id], backref=db.backref('inspections_received', lazy='dynamic'))

    def __repr__(self):
        status_str = "Pass" if self.pass_status else "Fail"
        return f'<Inspection {self.id} on Vehicle {self.vehicle_id} by Officer {self.officer_user_id} - Result: {status_str}>'

class VehicleRegion(enum.Enum):
    US = "United States"
    EURO = "Europe"

class UserVehicle(db.Model):
    __tablename__ = 'user_vehicles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    vehicle_make = db.Column(db.String(100), nullable=True)   # e.g., "Ford", "Volvo", "Peterbilt"
    vehicle_model = db.Column(db.String(100), nullable=True)  # e.g., "F-150", "FH16", "379"
    vehicle_type = db.Column(db.String(100), nullable=True)   # e.g., "Truck", "Combine Harvester", "Sedan"
    vehicle_description = db.Column(db.String(255), nullable=True)  # e.g., "Red Sports Car", "Log Hauling Truck"

    license_plate = db.Column(db.String(20), unique=True, nullable=False, index=True)
    region_format = db.Column(db.Enum(VehicleRegion), nullable=False)  # Plate formatting region enum

    registration_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)   # If user wants to deactivate a vehicle

    # Relationship to User (owner)
    owner = db.relationship('User', backref=db.backref('vehicles', lazy='dynamic'))

    def __repr__(self):
        return (
            f'<UserVehicle {self.id}: {self.license_plate} '
            f'({self.vehicle_make} {self.vehicle_model}) for User {self.user_id}>'
        )

# No need for a separate User.vehicles_collection relationship since backref 'vehicles' already covers it.



# --- Messaging System Models ---
from datetime import datetime
from app.enums import ConversationStatus  # make sure this enum is defined somewhere

class Conversation(db.Model):
    __tablename__ = 'conversations'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), default="Message", nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)  # Non-admin participant
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)  # Admin participant

    creation_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_message_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    # Unread status and counts
    user_unread_count = db.Column(db.Integer, default=0)
    admin_unread_count = db.Column(db.Integer, default=0)
    user_has_unread = db.Column(db.Boolean, default=False)
    admin_has_unread = db.Column(db.Boolean, default=False)

    # Conversation state
    status = db.Column(db.Enum(ConversationStatus), default=ConversationStatus.OPEN, nullable=False)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('conversations_as_user_participant', lazy='dynamic'))
    admin = db.relationship('User', foreign_keys=[admin_id], backref=db.backref('conversations_as_admin_participant', lazy='dynamic'))
    messages = db.relationship(
        'Message',
        backref='conversation',
        lazy='dynamic',
        cascade="all, delete-orphan",
        order_by="Message.timestamp"
    )

    def __repr__(self):
        return f'<Conversation {self.id}: "{self.subject}" between User {self.user_id} and Admin {self.admin_id}>'


from datetime import datetime
from app import db

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)  # User who sent this message
    
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_read_by_recipient = db.Column(db.Boolean, default=False)  # Optional, if you want to track read status explicitly
    
    # Relationship
    sender = db.relationship(
        'User',
        foreign_keys=[sender_id],
        backref=db.backref('sent_messages', lazy='dynamic')
    )

    # Conversation backref assumed defined on Conversation model: messages = db.relationship('Message', backref='conversation')

    def __repr__(self):
        return f'<Message {self.id} in Conv {self.conversation_id} by User {self.sender_id}>'


User.initiated_conversations_as_user = db.relationship('Conversation', foreign_keys=[Conversation.user_id], backref='user_initiator', lazy='dynamic')
User.participated_conversations_as_admin = db.relationship('Conversation', foreign_keys=[Conversation.admin_id], backref='admin_participant', lazy='dynamic')
User.all_sent_messages = db.relationship('Message', foreign_keys=[Message.sender_id], backref='message_sender', lazy='dynamic')


# --- Notification System Model ---
class NotificationType(enum.Enum):
    GENERAL_INFO = "general_info"
    # Add more types here if needed, e.g.:
    # TICKET_UPDATE = "ticket_update"
    # ALERT = "alert"

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)  # Recipient user
    message_text = db.Column(db.String(512), nullable=False)  # Notification content
    link_url = db.Column(db.String(512), nullable=True)  # Optional URL to related page
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    notification_type = db.Column(db.Enum(NotificationType), default=NotificationType.GENERAL_INFO, nullable=False)

    # Relationship to User, with backref 'notifications'
    user = db.relationship(
        'User',
        backref=db.backref('notifications', lazy='dynamic', order_by="desc(Notification.created_at)")
    )

    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id} - Read: {self.is_read}>'
import enum

class AuctionStatus(enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"


from datetime import datetime
from app import db

class AuctionItem(db.Model):
    __tablename__ = 'auction_items'

    id = db.Column(db.Integer, primary_key=True)
    submitter_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    admin_approver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)

    item_name = db.Column(db.String(200), nullable=False)
    item_description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(512), nullable=True)

    suggested_starting_bid = db.Column(db.Numeric(10, 2), nullable=True)
    actual_starting_bid = db.Column(db.Numeric(10, 2), nullable=True)
    minimum_bid_increment = db.Column(db.Numeric(10, 2), default=1.00, nullable=True)

    submission_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    approval_time = db.Column(db.DateTime, nullable=True)
    start_time = db.Column(db.DateTime, nullable=True, index=True)
    original_end_time = db.Column(db.DateTime, nullable=True)
    current_end_time = db.Column(db.DateTime, nullable=True, index=True)

    status = db.Column(db.Enum(AuctionStatus), default=AuctionStatus.PENDING_APPROVAL, nullable=False, index=True)
    admin_notes = db.Column(db.Text, nullable=True)

    winning_bid_id = db.Column(db.Integer, db.ForeignKey('auction_bids.id', use_alter=True, name='fk_auction_item_winning_bid_id'), nullable=True)
    winner_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)

    winner_payment_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)
    seller_payout_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)

    # Relationships
    submitter = db.relationship('User', foreign_keys=[submitter_user_id], backref=db.backref('submitted_auction_items', lazy='dynamic'))
    admin_approver = db.relationship('User', foreign_keys=[admin_approver_id], backref=db.backref('approved_auction_items', lazy='dynamic'))

    bids = db.relationship(
        'AuctionBid',
        back_populates='auction_item',
        lazy='dynamic',
        cascade="all, delete-orphan",
        order_by="desc(AuctionBid.bid_amount)",
        foreign_keys='AuctionBid.auction_item_id'  # use string to avoid NameError
    )

    winning_bid_ref = db.relationship(
        'AuctionBid',
        foreign_keys=[winning_bid_id],
        post_update=True,
        uselist=False
    )

    winner_user_ref = db.relationship('User', foreign_keys=[winner_user_id], backref=db.backref('auctions_won', lazy='dynamic'))

    winner_payment_tx = db.relationship('Transaction', foreign_keys=[winner_payment_transaction_id], backref=db.backref('auction_winner_payment_tx', uselist=False))
    seller_payout_tx = db.relationship('Transaction', foreign_keys=[seller_payout_transaction_id], backref=db.backref('auction_seller_payout_tx', uselist=False))

    def __repr__(self):
        return f'<AuctionItem {self.id}: {self.item_name} - Status: {self.status.value}>'


class AuctionBid(db.Model):
    __tablename__ = 'auction_bids'

    id = db.Column(db.Integer, primary_key=True)
    auction_item_id = db.Column(db.Integer, db.ForeignKey('auction_items.id'), nullable=False, index=True)
    bidder_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    bid_amount = db.Column(db.Numeric(10, 2), nullable=False)
    bid_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationship back to AuctionItem
    auction_item = db.relationship(
        'AuctionItem',
        back_populates='bids',
        foreign_keys=[auction_item_id]
    )

    bidder = db.relationship('User', foreign_keys=[bidder_user_id], backref=db.backref('auction_bids_placed', lazy='dynamic'))

    def __repr__(self):
        return f'<AuctionBid {self.id} for Item {self.auction_item_id} by User {self.bidder_user_id} for {self.bid_amount}>'

# --- Messaging System Models ---
class ConversationStatus(enum.Enum):
    OPEN = "Open"
    CLOSED_BY_USER = "Closed by User"
    CLOSED_BY_ADMIN = "Closed by Admin"
# --- Notification System Models ---
class NotificationType(enum.Enum):
    NEW_TICKET_ISSUED = "New Ticket Issued"
    PERMIT_APP_APPROVED = "Permit Application Approved"
    PERMIT_APP_DENIED = "Permit Application Denied"
    NEW_MESSAGE_RECEIVED = "New Message Received"
    # Add more types as needed: AUCTION_OUTBID, AUCTION_WON, AUCTION_SOLD (for seller), etc.
    GENERAL_INFO = "General Information"

# --- User Vehicle Registration Models ---
class VehicleRegion(enum.Enum):
    US = "United States" # Format: 123-ABC
    EURO = "Europe"      # Format: ABC-123

# Update User model for vehicles (covered by backref)
# User.vehicles


# Finalizing User model relationships for this phase
User.conversations_as_user_participant_rel = db.relationship('Conversation', foreign_keys=[Conversation.user_id], backref='user_conv_obj', lazy='dynamic')
User.conversations_as_admin_participant_rel = db.relationship('Conversation', foreign_keys=[Conversation.admin_id], backref='admin_conv_obj', lazy='dynamic')
User.sent_messages_rel = db.relationship('Message', foreign_keys=[Message.sender_id], backref='message_sender_obj', lazy='dynamic')
User.notifications_rel = db.relationship('Notification', foreign_keys=[Notification.user_id], backref='notified_user_obj', lazy='dynamic', order_by="desc(Notification.created_at)")
User.user_vehicles_rel = db.relationship('UserVehicle', foreign_keys=[UserVehicle.user_id], backref='vehicle_owner_obj', lazy='dynamic')

# Ensure all backrefs in User for existing models are also consistently named or reviewed
# (e.g., accounts, tickets_received, tickets_issued, etc. already exist)

# etc.
