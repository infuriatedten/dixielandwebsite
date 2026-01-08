import enum
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from sqlalchemy import Enum as SqlEnum

class UserRole(enum.Enum):
    USER = "user"
    OFFICER = "officer"
    ADMIN = "admin"

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    discord_user_id = db.Column(db.String(100), nullable=True, unique=True, index=True)
    discord_username = db.Column(db.String(100), nullable=True)
    region = db.Column(db.Enum('US', 'EU', 'OTHER_DEFAULT', name='region_enum'), nullable=True, default='OTHER_DEFAULT')
    pay_rate = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    is_clocked_in = db.Column(db.Boolean, default=False, nullable=False)
    current_session_start = db.Column(db.DateTime, nullable=True)
    accounts = db.relationship('Account', back_populates='user', lazy='dynamic', cascade="all, delete-orphan")
    company = db.relationship('Company', uselist=False, back_populates='user', cascade="all, delete-orphan")
    farmer = db.relationship('Farmer', uselist=False, back_populates='user', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role.value})>'

from datetime import datetime
from sqlalchemy import Numeric

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    currency = db.Column(db.String(10), default="GDC", nullable=False)
    name = db.Column(db.String(100), nullable=True)
    is_company = db.Column(db.Boolean, default=False, nullable=False)
    last_updated_on = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship('User', back_populates='accounts')
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
    TAX_PAYMENT = "tax_payment"
    AUTOMATED_TAX_DEDUCTION = "automated_tax_deduction"
    PERMIT_FEE_PAYMENT = "permit_fee_payment"
    AUCTION_WIN_DEBIT = "auction_win_debit"
    AUCTION_SALE_CREDIT = "auction_sale_credit"
    FS25_SYNC = "fs25_sync"
    OTHER = "other"

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    type = db.Column(db.Enum(TransactionType), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(255))

    def __repr__(self):
        return f'<Transaction {self.id} ({self.type.value}) of {self.amount} for Account {self.account_id}>'

class TaxBracket(db.Model):
    __tablename__ = 'tax_brackets'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    min_balance = db.Column(db.Numeric(10, 2), nullable=False, index=True)
    max_balance = db.Column(db.Numeric(10, 2), nullable=True, index=True)
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False)
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
    tax_rate_applied = db.Column(db.Numeric(5,2), nullable=False)
    amount_deducted = db.Column(db.Numeric(10, 2), nullable=False)
    deduction_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    banking_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), unique=True, nullable=False)
    user = db.relationship('User', backref=db.backref('automated_tax_deductions', lazy='dynamic'))
    banking_transaction = db.relationship('Transaction', backref=db.backref('automated_tax_deduction_log_entry', uselist=False))

    def __repr__(self):
        return f'<AutomatedTaxDeductionLog ID: {self.id} - User: {self.user_id} deducted {self.amount_deducted}>'

class TicketStatus(enum.Enum):
    OUTSTANDING = "Outstanding"
    PAID = "Paid"
    CONTESTED = "Contested"
    CANCELLED = "Cancelled"
    RESOLVED_UNPAID = "Resolved - Unpaid"
    RESOLVED_DISMISSED = "Resolved - Dismissed"

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    issued_to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    issued_by_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    vehicle_id = db.Column(db.String(100), nullable=True)
    violation_details = db.Column(db.Text, nullable=False)
    fine_amount = db.Column(db.Numeric(10, 2), nullable=False)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum(TicketStatus), default=TicketStatus.OUTSTANDING, nullable=False, index=True)
    user_contest_reason = db.Column(db.Text, nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    resolved_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    banking_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), unique=True, nullable=True)
    issued_to = db.relationship('User', foreign_keys=[issued_to_user_id], backref=db.backref('tickets_received', lazy='dynamic', cascade="all, delete-orphan"))
    issued_by = db.relationship('User', foreign_keys=[issued_by_officer_id], backref=db.backref('tickets_issued', lazy='dynamic', cascade="all, delete-orphan"))
    resolved_by_admin = db.relationship('User', foreign_keys=[resolved_by_admin_id], backref=db.backref('tickets_resolved', lazy='dynamic', cascade="all, delete-orphan"))
    payment_transaction = db.relationship('Transaction', backref=db.backref('ticket_payment_entry', uselist=False))

    def __repr__(self):
        return f'<Ticket {self.id} for User {self.issued_to_user_id} - Status: {self.status.value}>'

class PermitApplicationStatus(enum.Enum):
    PENDING_REVIEW = "Pending Review"
    REQUIRES_MODIFICATION = "Requires Modification"
    APPROVED_PENDING_PAYMENT = "Approved - Pending Payment"
    PAID_AWAITING_ISSUANCE = "Paid - Awaiting Issuance"
    ISSUED = "Issued"
    REJECTED = "Rejected"
    CANCELLED_BY_USER = "Cancelled by User"
    CANCELLED_BY_ADMIN = "Cancelled by Admin"

class PermitApplication(db.Model):
    __tablename__ = 'permit_applications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    vehicle_type = db.Column(db.String(150), nullable=False)
    route_details = db.Column(db.Text, nullable=False)
    travel_start_date = db.Column(db.Date, nullable=False)
    travel_end_date = db.Column(db.Date, nullable=False)
    user_notes = db.Column(db.Text, nullable=True)
    application_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.Enum(PermitApplicationStatus), default=PermitApplicationStatus.PENDING_REVIEW, nullable=False, index=True)
    permit_fee = db.Column(db.Numeric(10, 2), nullable=True)
    officer_notes = db.Column(db.Text, nullable=True)
    reviewed_by_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    banking_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), unique=True, nullable=True)
    issued_permit_id_str = db.Column(db.String(100), nullable=True, unique=True)
    issued_on_date = db.Column(db.DateTime, nullable=True)
    issued_by_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    applicant = db.relationship('User', foreign_keys=[user_id], backref=db.backref('permit_applications', lazy='dynamic', cascade="all, delete-orphan"))
    reviewer_officer = db.relationship('User', foreign_keys=[reviewed_by_officer_id], backref=db.backref('permits_reviewed', lazy='dynamic', cascade="all, delete-orphan"))
    issuer_officer = db.relationship('User', foreign_keys=[issued_by_officer_id], backref=db.backref('permits_issued', lazy='dynamic', cascade="all, delete-orphan"))
    payment_transaction = db.relationship('Transaction', backref=db.backref('permit_fee_payment_entry', uselist=False))

    def __repr__(self):
        return f'<PermitApplication {self.id} for User {self.user_id} - Status: {self.status.value}>'

class MarketplaceListingStatus(enum.Enum):
    AVAILABLE = "Available"
    SOLD_PENDING_RELIST = "Sold - More Available (Relist Soon)"
    SOLD_OUT = "Sold Out"
    CANCELLED = "Cancelled"

class MarketplaceListing(db.Model):
    __tablename__ = 'marketplace_listings'
    id = db.Column(db.Integer, primary_key=True)
    seller_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    item_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    status = db.Column(SqlEnum(MarketplaceListingStatus, name="marketplaceitemstatus"), default=MarketplaceListingStatus.AVAILABLE, nullable=False, index=True)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_update_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    discord_message_id = db.Column(db.String(100), nullable=True)
    seller = db.relationship('User', backref=db.backref('marketplace_listings', lazy='dynamic', cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<MarketplaceListing {self.id}: {self.quantity} {self.unit} of {self.item_name} by User {self.seller_user_id} for {self.price}>'

class Inspection(db.Model):
    __tablename__ = 'inspections'
    id = db.Column(db.Integer, primary_key=True)
    officer_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    inspected_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    vehicle_id = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    pass_status = db.Column(db.Boolean, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    officer = db.relationship('User', foreign_keys=[officer_user_id], backref=db.backref('inspections_conducted', lazy='dynamic', cascade="all, delete-orphan"))
    inspected_user = db.relationship('User', foreign_keys=[inspected_user_id], backref=db.backref('inspections_received', lazy='dynamic', cascade="all, delete-orphan"))

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
    vehicle_make = db.Column(db.String(100), nullable=True)
    vehicle_model = db.Column(db.String(100), nullable=True)
    vehicle_type = db.Column(db.String(100), nullable=True)
    vehicle_description = db.Column(db.String(255), nullable=True)
    license_plate = db.Column(db.String(20), unique=True, nullable=False, index=True)
    region_format = db.Column(db.Enum(VehicleRegion), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    owner = db.relationship('User', backref=db.backref('vehicles', lazy='dynamic', cascade="all, delete-orphan"))

    def __repr__(self):
        return (
            f'<UserVehicle {self.id}: {self.license_plate} '
            f'({self.vehicle_make} {self.vehicle_model}) for User {self.user_id}>'
        )

class ConversationStatus(enum.Enum):
    OPEN = "Open"
    CLOSED_BY_USER = "Closed by User"
    CLOSED_BY_ADMIN = "Closed by Admin"

class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), default="Message", nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    creation_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_message_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    user_unread_count = db.Column(db.Integer, default=0)
    admin_unread_count = db.Column(db.Integer, default=0)
    user_has_unread = db.Column(db.Boolean, default=False)
    admin_has_unread = db.Column(db.Boolean, default=False)
    status = db.Column(db.Enum(ConversationStatus), default=ConversationStatus.OPEN, nullable=False)
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('conversations_as_user_participant', lazy='dynamic', cascade="all, delete-orphan"))
    admin = db.relationship('User', foreign_keys=[admin_id], backref=db.backref('conversations_as_admin_participant', lazy='dynamic', cascade="all, delete-orphan"))
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade="all, delete-orphan", order_by="Message.timestamp")

    def is_unread_for_admin(self, admin_user_id):
        """Check if there are any unread messages for the admin in this conversation."""
        return any(
            not m.is_read_by_recipient and m.sender_id != admin_user_id
            for m in self.messages
        )

    def __repr__(self):
        return f'<Conversation {self.id}: "{self.subject}" between User {self.user_id} and Admin {self.admin_id}>'

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_read_by_recipient = db.Column(db.Boolean, default=False)
    sender = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy='dynamic', cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<Message {self.id} in Conv {self.conversation_id} by User {self.sender_id}>'

class NotificationType(enum.Enum):
    GENERAL_INFO = "general_info"
    NEW_TICKET_ISSUED = "New Ticket Issued"
    PERMIT_APP_APPROVED = "Permit Application Approved"
    PERMIT_APP_DENIED = "Permit Application Denied"
    NEW_MESSAGE_RECEIVED = "New Message Received"

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    message_text = db.Column(db.String(512), nullable=False)
    link_url = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    notification_type = db.Column(db.Enum(NotificationType), default=NotificationType.GENERAL_INFO, nullable=False)
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic', order_by="desc(Notification.created_at)", cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id} - Read: {self.is_read}>'

class AuctionStatus(enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    CANCELLED_BY_ADMIN = "cancelled_by_admin"

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
    submitter = db.relationship('User', foreign_keys=[submitter_user_id], backref=db.backref('submitted_auction_items', lazy='dynamic', cascade="all, delete-orphan"))
    admin_approver = db.relationship('User', foreign_keys=[admin_approver_id], backref=db.backref('approved_auction_items', lazy='dynamic', cascade="all, delete-orphan"))
    bids = db.relationship('AuctionBid', back_populates='auction_item', lazy='dynamic', cascade="all, delete-orphan", order_by="desc(AuctionBid.bid_amount)", foreign_keys='AuctionBid.auction_item_id')
    winning_bid_ref = db.relationship('AuctionBid', foreign_keys=[winning_bid_id], post_update=True, uselist=False)
    winner_user_ref = db.relationship('User', foreign_keys=[winner_user_id], backref=db.backref('auctions_won', lazy='dynamic', cascade="all, delete-orphan"))
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
    auction_item = db.relationship('AuctionItem', back_populates='bids', foreign_keys=[auction_item_id])
    bidder = db.relationship('User', foreign_keys=[bidder_user_id], backref=db.backref('auction_bids_placed', lazy='dynamic', cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<AuctionBid {self.id} for Item {self.auction_item_id} by User {self.bidder_user_id} for {self.bid_amount}>'

class RulesContent(db.Model):
    __tablename__ = 'rules_content'
    id = db.Column(db.Integer, primary_key=True)
    content_markdown = db.Column(db.Text, nullable=False, default="Rules have not been set yet.")
    last_edited_on = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_edited_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    last_edited_by = db.relationship('User', foreign_keys=[last_edited_by_id], backref=db.backref('rules_edited', lazy='dynamic', cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<RulesContent last updated on {self.last_edited_on} by User ID {self.last_edited_by_id}>'

class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    details = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates='company')
    vehicles = db.relationship('CompanyVehicle', backref='company', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Company {self.name}>'

class CompanyVehicle(db.Model):
    __tablename__ = 'company_vehicles'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    vehicle_make = db.Column(db.String(100), nullable=True)
    vehicle_model = db.Column(db.String(100), nullable=True)
    vehicle_type = db.Column(db.String(100), nullable=True)
    vehicle_description = db.Column(db.String(255), nullable=True)
    license_plate = db.Column(db.String(20), unique=True, nullable=False, index=True)
    region_format = db.Column(db.Enum(VehicleRegion), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return (
            f'<CompanyVehicle {self.id}: {self.license_plate} '
            f'({self.vehicle_make} {self.vehicle_model}) for Company {self.company_id}>'
        )

class Farmer(db.Model):
    __tablename__ = 'farmers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)

    user = db.relationship('User', back_populates='farmer')
    parcels = db.relationship('Parcel', backref='farmer', lazy='dynamic', cascade="all, delete-orphan")

class FarmerStats(db.Model):
    __tablename__ = 'farmer_stats'
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False, unique=True)
    fields_owned = db.Column(db.Integer, default=0)
    total_yield = db.Column(db.Float, default=0)
    equipment_owned = db.Column(db.Integer, default=0)
    last_synced = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    farmer = db.relationship('Farmer', backref=db.backref('stats', uselist=False))
class TransactionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False)
    amount = db.Column(db.Float)
    description = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Parcel(db.Model):
    __tablename__ = 'parcels'
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(256), nullable=False)
    size = db.Column(db.Float, nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False)
    validated = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<Parcel {self.id}>'


class SiloStorage(db.Model):
    __tablename__ = 'silo_storage'
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False, index=True)
    crop_type = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=0)
    capacity = db.Column(db.Float, nullable=False, default=200000) # Default capacity, can be updated via API
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    farmer = db.relationship('Farmer', backref=db.backref('silo_contents', lazy='dynamic'))

    def __repr__(self):
        return f'<SiloStorage for Farmer {self.farmer_id}: {self.quantity}/{self.capacity} of {self.crop_type}>'


class InsuranceClaimStatus(enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class InsuranceClaim(db.Model):
    __tablename__ = 'insurance_claims'

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False)
    claim_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    reason = db.Column(db.String(100), nullable=False)  # Now uses predefined categories
    description = db.Column(db.Text, nullable=False)  # Detailed description
    estimated_loss = db.Column(db.Numeric(10, 2), nullable=False)  # Estimated loss amount
    status = db.Column(db.Enum(InsuranceClaimStatus), default=InsuranceClaimStatus.PENDING, nullable=False)

    farmer = db.relationship('Farmer', backref=db.backref('insurance_claims', lazy='dynamic'))

    def get_readable_reason(self):
        reason_map = {
            'crop_damage_weather': 'Crop Damage - Weather Related',
            'crop_damage_pest': 'Crop Damage - Pest/Disease',
            'equipment_breakdown': 'Equipment Breakdown',
            'livestock_injury': 'Livestock Injury/Death',
            'fire_damage': 'Fire Damage to Property',
            'theft_vandalism': 'Theft or Vandalism',
            'vehicle_accident': 'Farm Vehicle Accident',
            'building_damage': 'Building/Structure Damage',
            'contamination': 'Crop/Feed Contamination',
            'other_farm_related': 'Other Farm-Related Incident'
        }
        return reason_map.get(self.reason, self.reason)

    def __repr__(self):
        return f'<InsuranceClaim {self.id}: {self.get_readable_reason()}>'


import enum

class InsuranceRateType(enum.Enum):
    VEHICLE = "VEHICLE"
    FARM = "FARM"
    CROP = "CROP"
    ANIMAL = "ANIMAL"

class InsuranceRate(db.Model):
    __tablename__ = 'insurance_rates'
    id = db.Column(db.Integer, primary_key=True)
    rate_type = db.Column(db.Enum(InsuranceRateType), default=InsuranceRateType.VEHICLE, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    rate = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text, nullable=True)
    payout_requests = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return f'<InsuranceRate {self.name}: {self.rate}>'

class ContractStatus(enum.Enum):
    AVAILABLE = "Available"
    CLAIMED = "Claimed"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class Contract(db.Model):
    __tablename__ = 'contracts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    reward = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum(ContractStatus), default=ContractStatus.AVAILABLE, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    claimant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    creator = db.relationship('User', foreign_keys=[creator_id], backref=db.backref('created_contracts', lazy='dynamic', cascade="all, delete-orphan"))
    claimant = db.relationship('User', foreign_keys=[claimant_id], backref=db.backref('claimed_contracts', lazy='dynamic', cascade="all, delete-orphan"))
    creation_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    claimed_date = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Contract {self.id}: {self.title}>'

class CompanyContract(db.Model):
    __tablename__ = 'company_contracts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    reward = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum(ContractStatus), default=ContractStatus.AVAILABLE, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    claimant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    company = db.relationship('Company', foreign_keys=[company_id], backref=db.backref('contracts', lazy='dynamic', cascade="all, delete-orphan"))
    claimant = db.relationship('User', foreign_keys=[claimant_id], backref=db.backref('claimed_company_contracts', lazy='dynamic', cascade="all, delete-orphan"))
    creation_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    claimed_date = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<CompanyContract {self.id}: {self.title}>'

class Fine(db.Model):
    __tablename__ = 'fines'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f'<Fine {self.name}: {self.amount}>'

class CompanyInsuranceClaim(db.Model):
    __tablename__ = 'company_insurance_claims'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    claim_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum(InsuranceClaimStatus), default=InsuranceClaimStatus.PENDING, nullable=False)
    company = db.relationship('Company', backref=db.backref('insurance_claims', lazy='dynamic', cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<CompanyInsuranceClaim {self.id}>'

class StoreItem(db.Model):
    __tablename__ = 'store_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    brand = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    xml_filename = db.Column(db.String(255), nullable=False, unique=True, index=True)

    def __repr__(self):
        return f'<StoreItem {self.id}: {self.name}>'

class Vehicle(db.Model):
    __tablename__ = 'vehicle_locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    location = db.Column(db.String(256), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = db.relationship('User', backref=db.backref('vehicle_locations', lazy='dynamic'))

    def __repr__(self):
        return f'<Vehicle {self.name} at {self.location}>'
