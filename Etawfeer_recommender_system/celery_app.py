import subprocess
from celery import Celery
from flask import Flask
from models import db
from ha_rec import system_type

# Function to get WSL IP dynamically (optional)

HA_env = system_type


def get_wsl_ip():
    result = subprocess.run(
        ["wsl", "ip", "addr", "show", "eth0"], capture_output=True, text=True)
    for line in result.stdout.split("\n"):
        if "inet " in line:
            return line.split()[1].split("/")[0]
    return "172.22.76.241"  # Fallback to manually set IP


# Initialize Flask app
app = Flask(__name__)

app.config['SECRET_KEY'] = 'aaaaaaddddddddd!!!!!!!@@@@@@@###FFFFF525851515'

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'


if HA_env:
    # Use Redis inside Docker (Home Assistant Add-on)

    redis_broker_url = 'redis://localhost:6379/0'
    redis_result_backend = 'redis://localhost:6379/0'

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/mydatabase.db'

else:

    # Use the new Celery configuration format
    WSL_REDIS_IP = get_wsl_ip()  # Get WSL IP dynamically (or use hardcoded value)

    redis_broker_url = f'redis://{WSL_REDIS_IP}:6379/0'  # New format
    redis_result_backend = f'redis://{WSL_REDIS_IP}:6379/0'

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.update(broker_url=redis_broker_url,
                  result_backend=redis_result_backend)


def make_celery(app):
    """Initialize Celery with Flask app config."""
    celery = Celery(app.import_name, broker=redis_broker_url)
    celery.conf.update(app.config)
    return celery


# Initialize DB for Celery tasks
db.init_app(app)

# Create Celery instance
celery = make_celery(app)
