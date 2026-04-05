from flask import Blueprint, render_template, request, jsonify, redirect
from models import db, User, Automation
from ha_rec import get_entities, add_ha_automation, get_sersor_data
from utils import get_url

user_bp = Blueprint('user_bp', __name__)

# Route to show the user creation form


@user_bp.route('')
def users():
    all_users = User.query.all()  # Assuming you are using SQLAlchemy
    return render_template('users.html', users=all_users)


@user_bp.route('/create_user_form')
def create_user_form():
    notify, persons, switches, lights, sensors = get_entities()
    return render_template('create_user.html', notify=notify)

# Route to handle user creation


@user_bp.route('/create_user', methods=['POST'])
def create_user():
    try:
        name = request.form['name']
        device = request.form['device']
        country = request.form['country']
        new_user = User(name=name, device=device,
                        country=country)
        db.session.add(new_user)
        db.session.commit()

        add_ha_automation()

        # ✅ Redirect to the users page after creation
        # Make sure the endpoint is correct
        return redirect(get_url('user_bp.users'))
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@user_bp.route('/<int:user_id>')
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    view = request.args.get('view', 'automations')  # Default to "automations"
    automations = Automation.query.filter_by(user_id=user.id).all()
    power = get_sersor_data('power')
    notify, persons, switches, lights, sensors = get_entities()
    return render_template('user_detail.html', user=user, automations=automations, power=power, view=view, notify=notify)


@user_bp.route('/<int:user_id>/edit', methods=['POST'])
def edit_user(user_id):
    user = User.query.get(user_id)
    user.name = request.form['name']
    user.device = request.form['device']
    user.country = request.form['country']

    db.session.commit()
    return redirect(get_url('user_bp.users'))


@user_bp.route("/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    print(f"Do you want to delete the user: {user.id}")
    db.session.delete(user)
    db.session.commit()
    return redirect(get_url("user_bp.users"))
