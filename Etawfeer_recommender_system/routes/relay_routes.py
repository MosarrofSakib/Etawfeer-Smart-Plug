from flask import Blueprint, jsonify, request
from models import db, RelayStatus
from ha_rec import trigger_relay

relay_bp = Blueprint("relay_bp", __name__)


@relay_bp.route("/<command>", methods=["POST"])
def control_relay(command):
    if command.upper() not in ["ON", "OFF"]:
        return jsonify({"error": "Invalid command"}), 400

    # Use trigger_relay with new command format
    relay_command = "relay_on" if command.upper() == "ON" else "relay_off"
    result = trigger_relay(relay_command)

    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 500

    # print(command.upper(), result)

    # Save to DB
    latest = RelayStatus.query.get(1)
    if not latest:
        latest = RelayStatus()
        db.session.add(latest)

    if command.upper() == "ON":
        latest.turn_on()
    else:
        latest.turn_off()

    # print(f"Before commit state: {latest.state}")
    db.session.commit()
    # print(f"Updated state: {latest.state}")

    return jsonify({"success": True, "state": bool(latest.state)})


@relay_bp.route("/status", methods=["GET"])
def get_relay_status():
    # Get the latest relay status (if any)
    latest = RelayStatus.query.get(1)

    if not latest:
        # If no entry exists, create a default one (assume OFF by default)
        latest = RelayStatus()
        db.session.add(latest)
        db.session.commit()

    print(latest.state)

    return jsonify({"state": latest.state})
