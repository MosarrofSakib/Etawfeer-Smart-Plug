from flask import url_for
from ha_rec import INGRESS_PREFIX
from models import db, RelayStatus
from datetime import datetime
from celery_app import app


def get_url(destination, **kwargs):
    """Generate correct relative URL with Home Assistant ingress prefix."""
    global INGRESS_PREFIX  # Make sure Python uses the global variable

    if not INGRESS_PREFIX:
        print("⚠️ Warning: INGRESS_PREFIX is not set. Using default '/'")
        INGRESS_PREFIX = "/"

    # Generate relative URL
    url = url_for(destination, **kwargs)

    # Ensure there is no double slash when adding prefix
    if not INGRESS_PREFIX.endswith("/"):
        INGRESS_PREFIX += "/"

    if url.startswith("/"):
        url = url[1:]  # Remove leading slash to avoid "//"

    corrected_url = f"{INGRESS_PREFIX}{url}"  # Corrected relative URL

    # print(f"✅ The corrected URL is: {corrected_url}")
    return corrected_url


def update_relay_state_to_on():
    with app.app_context():
        relay = RelayStatus.query.get(1)
        if relay:
            if relay.state:
                print("Relay is alreay on!")
            else:
                relay.turn_on()
        else:
            print("No relay available!")
        db.session.commit()
        print("Relay state updated to ON on startup.")


""" def get_url(destination, **kwargs):
    url = url_for(destination, _external=True, **kwargs)
    url = url.replace(f'{destination}', f'{INGRESS_PREFIX}{destination}')

    print(f"The url is: {url}")
    return url
 """
