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
    # Hardcoded rules as per user request
    rules_content_html = """
    <div class="container mt-4">
        <h1>Game Rules</h1>
        <p><em>Last Updated: 2023-10-27</em></p>
        
        <h2>1. General Conduct & Respect</h2>
        <ul>
            <li><strong>1.1 Respect All Players:</strong> Treat all members of the community, including players, staff, and guests, with respect and courtesy. Harassment, discrimination, hate speech, or any form of bullying will not be tolerated.</li>
            <li><strong>1.2 No Offensive Content:</strong> Do not use offensive language, names, or symbols. This includes, but is not limited to, content that is sexually explicit, graphically violent, racist, sexist, or otherwise discriminatory.</li>
            <li><strong>1.3 Staff Authority:</strong> Server staff (Administrators, Moderators) have the final say in all rule interpretations and enforcement. Arguing with staff decisions publicly is discouraged; use designated channels or private messages for disputes.</li>
            <li><strong>1.4 Impersonation:</strong> Do not impersonate other players, staff members, or any real-world individuals.</li>
        </ul>

        <h2>2. Gameplay & Fair Play</h2>
        <ul>
            <li><strong>2.1 No Cheating or Exploiting:</strong> The use of third-party programs (cheats, hacks), exploiting game bugs, or any unfair advantages is strictly prohibited. If you find a bug, report it to staff immediately.</li>
            <li><strong>2.2 Account Security:</strong> You are responsible for the security of your account. Do not share your account details. Staff will never ask for your password.</li>
            <li><strong>2.3 Fair Play in PvP/PvE:</strong> Engage in Player vs. Player (PvP) or Player vs. Environment (PvE) content according to established server norms (if any). Griefing, spawn camping (excessively), or intentionally disrupting others' gameplay outside of accepted PvP conflict may be against the rules depending on context.</li>
            <li><strong>2.4 Economy and Trading:</strong> Do not engage in real-money trading (RMT) for in-game items or currency. Scamming other players in trades is prohibited.</li>
        </ul>

        <h2>3. Roleplaying (RP) Server Specifics (If Applicable)</h2>
        <p><em>If this is a roleplaying server, the following rules apply in designated RP areas/contexts:</em></p>
        <ul>
            <li><strong>3.1 Stay In Character (IC):</strong> Maintain character consistency. Out-of-character (OOC) communication should be minimized and use designated OOC channels (e.g., (( OOC text )) or /ooc chat).</li>
            <li><strong>3.2 Metagaming:</strong> Do not use OOC information that your character would not know IC to influence your actions or decisions.</li>
            <li><strong>3.3 Powergaming/Godmodding:</strong> Do not force actions upon another player's character without their consent, or act as if your character is invincible or all-powerful. Roleplay should be cooperative.</li>
            <li><strong>3.4 New Life Rule (NLR):</strong> If your character "dies" or is incapacitated in RP, they should not remember the events leading up to their death/incapacitation or seek immediate revenge unless specific server lore/rules allow for it.</li>
            <li><strong>3.5 Value of Life:</strong> Act in a way that shows your character values their life and well-being. Avoid reckless or suicidal actions without strong IC reasoning.</li>
        </ul>
        
        <h2>4. Communication & Community</h2>
        <ul>
            <li><strong>4.1 Appropriate Language:</strong> Keep chat and voice communication clean and respectful. Excessive profanity, especially when directed at others, may result in warnings or mutes.</li>
            <li><strong>4.2 No Spamming:</strong> Do not spam chat channels, voice communications, or server forums with repetitive messages, advertisements (for non-server related things), or meaningless content.</li>
            <li><strong>4.3 Advertising:</strong> Do not advertise other game servers, Discord servers, or external services without explicit permission from server administration.</li>
            <li><strong>4.4 Discord/Forum Usage:</strong> Follow any specific rules posted for Discord channels or forum sections. Use channels for their intended purposes.</li>
        </ul>

        <h2>5. Consequences of Rule Violations</h2>
        <ul>
            <li>Violations of these rules may result in warnings, temporary mutes/bans, permanent bans, or other disciplinary actions as deemed appropriate by server staff.</li>
            <li>The severity of the consequence will depend on the severity of the violation and the player's history.</li>
            <li>Ignorance of the rules is not an excuse for violating them.</li>
        </ul>

        <hr>
        <p class="text-muted small">These rules are subject to change. Please check back regularly for updates. By playing on this server, you agree to abide by these rules.</p>
    </div>
    """
    # Pass UserRole to the template to allow conditional display of "Edit" button (though it will be removed from template next)
    # Also pass current_user to check authentication and role in the template.
    return render_template('main/rules.html', title='Rules', 
                           rules_content_html=rules_content_html, 
                           current_user=current_user, UserRole=UserRole)
