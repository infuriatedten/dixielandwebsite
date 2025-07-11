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
    return render_template('admin/dashboard.html', title='Admin Dashboard')

@main_bp.route('/officer-area')
@officer_required
def officer_area():
    return render_template('officer/area.html', title='Officer Area')

@main_bp.route('/rules', endpoint='view_rules')
def view_rules():
    rules_entry = RulesContent.query.first()
    rules_content_html = ""
    if rules_entry and rules_entry.content_markdown:
        # Ensure mistune is initialized if it's a class, or direct call if function
        # Assuming mistune.html() is the correct usage based on previous context
        markdown_parser = mistune.create_markdown(escape=False) # Basic usage, ensure it's safe if content can be malicious
        rules_content_html = markdown_parser(rules_entry.content_markdown)
    else:
        rules_content_html = "<p>The rules have not been set yet. Please check back later.</p>"
        if current_user.is_authenticated and hasattr(current_user, 'role') and current_user.role == UserRole.ADMIN:
            rules_content_html += f'<p><a href="{url_for("admin.edit_rules")}">Set the rules now.</a></p>'


    # Pass UserRole to the template to allow conditional display of "Edit" button
    # Also pass current_user to check authentication and role in the template.
    return render_template('main/rules.html', title='Rules',
                           rules_content_html=rules_content_html,
                           current_user=current_user, UserRole=UserRole)
