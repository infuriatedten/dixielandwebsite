from flask import Blueprint, render_template
from app.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def index():
    return render_template('admin/dashboard.html', title='Admin Dashboard')

@admin_bp.route('/tickets')
@admin_required
def tickets():
    # This is a placeholder. You'll need to implement the logic to fetch and display tickets.
    return render_template('admin/tickets.html', title='Manage Tickets')

from app.forms import EditRulesForm
from app.models import RulesContent
from app import db

@admin_bp.route('/rules/edit', methods=['GET', 'POST'])
@admin_required
def edit_rules():
    rules = RulesContent.query.first()
    if not rules:
        rules = RulesContent(content_markdown='Initial rules content.')
        db.session.add(rules)
        db.session.commit()

    form = EditRulesForm(obj=rules)
    if form.validate_on_submit():
        rules.content_markdown = form.content_markdown.data
        db.session.commit()
        flash('Rules updated successfully.', 'success')
        return redirect(url_for('main.view_rules'))
    return render_template('admin/edit_rules.html', title='Edit Rules', form=form)
