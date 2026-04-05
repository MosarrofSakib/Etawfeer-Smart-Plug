from flask import Blueprint, render_template, request, redirect
from models import db, Automation, User
from utils import get_url

automation_bp = Blueprint('automation_bp', __name__)


@automation_bp.route('/create/<int:user_id>', methods=['GET', 'POST'])
def create_automation(user_id):
    if request.method == 'POST':
        try:
            title = request.form['title']
            interval = request.form['interval']

            new_automation = Automation(
                title=title,
                interval=interval,
                user_id=user_id
            )

            db.session.add(new_automation)
            db.session.commit()

            # Redirect back to user's automation list
            return redirect(get_url('user_bp.user_detail', user_id=user_id, view='automations'))

        except Exception as e:
            return f"Error creating automation: {e}", 400

    return render_template('create_automation.html', user_id=user_id)


@automation_bp.route('/<int:user_id>')
def list_automations(user_id):
    user = User.query.get_or_404(user_id)
    automations = Automation.query.filter_by(user_id=user.id).all()
    return render_template('user_detail.html', user=user, automations=automations, view='automations')


@automation_bp.route('/automations/<int:automation_id>/edit', methods=['GET', 'POST'])
def edit_automation(automation_id):
    automation = Automation.query.get_or_404(automation_id)
    user = User.query.get_or_404(automation.user_id)

    if request.method == 'POST':
        try:
            # Update automation details
            automation.title = request.form['title']
            automation.interval = request.form['interval']

            db.session.commit()

            # Redirect back to user's automation list
            return redirect(get_url('user_bp.user_detail', user_id=automation.user_id, view='automations'))

        except Exception as e:
            return f"Error updating automation: {e}", 400

    # Pass user to template
    return render_template('edit_automation.html', automation=automation, user=user)


@automation_bp.route('/delete/<int:automation_id>', methods=['POST'])
def delete_automation(automation_id):
    automation = Automation.query.get(automation_id)
    db.session.delete(automation)
    db.session.commit()

    return redirect(get_url('user_bp.user_detail', user_id=automation.user_id, view='automations'))
