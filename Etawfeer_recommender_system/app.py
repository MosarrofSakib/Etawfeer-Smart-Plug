from flask_migrate import Migrate
from models import db
from routes.home import home_bp
from routes.user_routes import user_bp
from routes.automation_routes import automation_bp
from routes.recommendation_routes import recommendation_bp
from routes.visualize_routes import visualize_bp
from routes.relay_routes import relay_bp
from utils import update_relay_state_to_on

# ✅ Import Celery from celery_app.py
from celery_app import app
from utils import get_url


# app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'supersecretkey')

migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

# To fix the bug of relay in case of reboot
update_relay_state_to_on()

# ✅ Register Blueprints
app.register_blueprint(home_bp)
app.register_blueprint(user_bp, url_prefix=f'/users')
app.register_blueprint(
    automation_bp, url_prefix=f'/automations')
app.register_blueprint(recommendation_bp)
app.register_blueprint(visualize_bp, url_prefix='/visualize')
app.register_blueprint(relay_bp, url_prefix='/relay')


@app.context_processor
def inject_ingress_url():
    """Inject get_url() function into templates."""
    return {"get_url": get_url, "home_bp": home_bp, "user_bp": user_bp}


if __name__ == '__main__':
    PORT = 5000
    app.run(host='0.0.0.0', port=PORT, debug=True)
