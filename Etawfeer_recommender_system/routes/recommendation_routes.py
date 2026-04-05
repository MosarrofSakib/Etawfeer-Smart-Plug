from flask import Blueprint, redirect, render_template, jsonify, request
from models import db, User, Recommendation, RelayStatus
from datetime import datetime, timedelta
from utils import get_url
from ha_rec import trigger_relay

recommendation_bp = Blueprint(
    'recommendation_bp', __name__, url_prefix='/recommendations')


@recommendation_bp.route('/<int:user_id>')
def view_recommendations(user_id):
    """View all recommendations for a user."""
    user = User.query.get_or_404(user_id)
    pending_recommendations = Recommendation.query.filter_by(
        user_id=user.id, action_required=True).order_by(Recommendation.generated_time.desc()).all()
    processed_recommendations = Recommendation.query.filter_by(
        user_id=user.id, action_required=False).order_by(Recommendation.action_time.desc()).all()

    return render_template('recommendations.html', user=user, pending_recommendations=pending_recommendations, processed_recommendations=processed_recommendations, now=datetime.now, timedelta=timedelta)


@recommendation_bp.route('/accept/<int:recommendation_id>', methods=['POST'])
def accept_recommendation(recommendation_id):
    """Accept a recommendation (mark as accepted)."""
    recommendation = Recommendation.query.get_or_404(recommendation_id)
    # ✅ Turn off relay for MM Class 3 or 4
    if recommendation.mm_class in [3, 4]:
        print("Turning off relay due to MM Class 3 or 4...")
        result = trigger_relay("relay_off")

        # result = False     #For local testing

        if isinstance(result, dict) and "error" in result:
            print("Error sending relay command:", result["error"])
        else:
            print("Relay turned OFF successfully.")

            # ✅ Update or create RelayStatus in DB
            relay = RelayStatus.query.get(1)
            relay.turn_off()
    recommendation.accept()
    db.session.commit()
    return redirect(get_url('recommendation_bp.view_recommendations', user_id=recommendation.user_id))


@recommendation_bp.route('/reject/<int:recommendation_id>', methods=['POST'])
def reject_recommendation(recommendation_id):
    """Reject a recommendation (mark as rejected)."""
    recommendation = Recommendation.query.get_or_404(recommendation_id)
    recommendation.reject()
    db.session.commit()
    return redirect(get_url('recommendation_bp.view_recommendations', user_id=recommendation.user_id))


@recommendation_bp.route("/delete/<int:recommendation_id>", methods=["POST"])
def delete_recommendation(recommendation_id):
    """Deletes a recommendation by ID and returns a JSON response"""
    try:
        recommendation = Recommendation.query.get_or_404(recommendation_id)

        db.session.delete(recommendation)
        db.session.commit()

        return jsonify({"success": True, "message": "Recommendation deleted"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error {e}"})


######### HA handle ########
@recommendation_bp.route("/action", methods=["POST"])
def handle_recommendation_action():
    """ Handles Accept/Reject action from Home Assistant """
    data = request.get_json()
    recommendation_id = data.get("recommendation_id")
    action_taken = data.get("action_taken")

    if not recommendation_id or not action_taken:
        return jsonify({"error": "Missing parameters"}), 400

    recommendation = Recommendation.query.get(recommendation_id)
    if not recommendation:
        return jsonify({"error": "Recommendation not found"}), 404

    # Update Recommendation
    if action_taken == 'accepted':
        recommendation.accept()

        # ✅ Turn off relay for MM Class 3 or 4
        if recommendation.mm_class in [3, 4]:
            print("Turning off relay due to MM Class 3 or 4...")
            result = trigger_relay("relay_off")

            # result = False     #For local testing

            if isinstance(result, dict) and "error" in result:
                print("Error sending relay command:", result["error"])
            else:
                print("Relay turned OFF successfully.")

                # ✅ Update or create RelayStatus in DB
                relay = RelayStatus.query.get(1)
                relay.turn_off()

    elif action_taken == 'rejected':
        recommendation.reject()
    else:
        return jsonify({"error": "Invalid action parameters"}), 400

    db.session.commit()

    return jsonify({
        "message": f"Recommendation {recommendation_id} marked as {action_taken}"
    }), 200
