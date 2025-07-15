from flask import Blueprint, render_template, url_for # Added url_for
from flask_login import current_user
from app.decorators import admin_required, officer_required
from app.models import UserRole, RulesContent # Consolidated imports
import mistune # For Markdown to HTML conversion

main_bp = Blueprint('main', __name__)

@main_bp.route('/', endpoint='index')
def main_index():
    return render_template('main/index.html', title='Home')

@main_bp.route('/admin-dashboard')
@admin_required
def admin_dashboard():
    stats = {
        'total_users': 0,
        'pending_permits': 0,
        'open_tickets': 0,
        'revenue': 0
    }
    return render_template('admin/dashboard.html', title='Admin Dashboard', stats=stats)

@main_bp.route('/officer-area')
@officer_required
def officer_area():
    return render_template('officer/area.html', title='Officer Area')

@main_bp.route('/rules', endpoint='view_rules')
def view_rules():
    rules_entry = RulesContent.query.first()
    rules_content_html = ""
    if rules_entry and rules_entry.content_markdown:
        markdown_parser = mistune.create_markdown(escape=False) 
        rules_content_html = markdown_parser(rules_entry.content_markdown)
    else:
        rules_content_html = "<p>The rules have not been set yet. Please check back later.</p>"
        # Check if current_user is authenticated and is an admin before suggesting to set rules
        if current_user.is_authenticated and hasattr(current_user, 'role') and current_user.role.value == UserRole.ADMIN.value:
            rules_content_html += f'<p><a href="{url_for("admin.edit_rules")}">Set the rules now.</a></p>'

    return render_template('main/rules.html', title='Rules',
                           rules_content_html=rules_content_html,
                           current_user=current_user, UserRole=UserRole)
