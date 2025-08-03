from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User, UserRole, Farmer, Company, Account
from app.forms import LoginForm, RegistrationForm
from urllib.parse import urlparse, urljoin

bp = Blueprint('auth', __name__)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=UserRole.USER # Default role for self-registration
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # Create a bank account with a balance of 1,000,000
        account = Account(user_id=user.id, balance=1000000)
        db.session.add(account)

        if form.account_type.data == 'farmer':
            farmer = Farmer(user_id=user.id)
            db.session.add(farmer)
        elif form.account_type.data == 'company':
            company = Company(user_id=user.id, name=f"{user.username}'s Company")
            db.session.add(company)

        db.session.commit()

        from app.email import send_email
        from itsdangerous import URLSafeTimedSerializer
        from flask import current_app

        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = s.dumps(user.email, salt='email-confirm')

        confirm_url = url_for('auth.confirm_email', token=token, _external=True)
        html = render_template('auth/confirm_email.html', confirm_url=confirm_url)
        send_email(user.email, 'Confirm Your Email Address', html)

        flash('A confirmation email has been sent to your email address. Please check your inbox to complete the registration.', 'info')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        if not user.email_confirmed:
            flash('Please confirm your email address before logging in.', 'warning')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not is_safe_url(next_page):
            next_page = url_for('main.index')
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@bp.route('/confirm/<token>')
def confirm_email(token):
    from itsdangerous import URLSafeTimedSerializer
    from flask import current_app

    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('main.index'))

    user = User.query.filter_by(email=email).first_or_404()
    if user.email_confirmed:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.email_confirmed = True
        db.session.add(user)
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('auth.login'))

# Example of a protected route
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.routes.auth import bp
from app.forms import EditProfileForm
from app.models import Company, Farmer, Parcel

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = EditProfileForm(
        original_username=current_user.username,
        original_email=current_user.email,
        obj=current_user
    )

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.about_me = form.about_me.data

        # Handle optional fields
        if hasattr(form, 'region') and form.region.data:
            current_user.region = form.region.data

        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('auth.profile'))

    # Pre-fill optional fields only on GET
    if request.method == 'GET' and hasattr(form, 'region'):
        form.region.data = current_user.region or 'OTHER_DEFAULT'

    return render_template(
        'auth/profile.html',
        title='My Profile',
        form=form,
        user=current_user
    )
