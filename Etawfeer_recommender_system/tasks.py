from celery.schedules import crontab
from datetime import datetime
from celery_app import celery
from app import app
from models import db, Automation, Recommendation
from message import generate_mm_message
import random
from ha_rec import send_notification, get_sersor_data
from read_data import predict


@celery.task
def generate_recommendations():
    """
    Run MM prediction according to each automation interval.
    Send a recommendation only when the MM class changes.
    """
    with app.app_context():
        try:
            automations = Automation.query.all()
            print(f"🔄 Checking {len(automations)} automations...")

            for automation in automations:
                now = datetime.now()
                interval_minutes = automation.interval

                should_check = False

                if automation.last_checked_at is None:
                    should_check = True
                else:
                    elapsed_minutes = (
                        now - automation.last_checked_at).total_seconds() / 60
                    should_check = elapsed_minutes >= interval_minutes

                if not should_check:
                    print(
                        f"⏳ Skipping '{automation.title}' - waiting for next MM check.")
                    continue

                # Run MM prediction now
                mm_class = predict()
                # mm_class = 2

                # If prediction failed, skip safely
                if not isinstance(mm_class, int):
                    print(
                        f"❌ Invalid MM prediction for '{automation.title}': {mm_class}")
                    automation.last_checked_at = now
                    db.session.commit()
                    continue

                previous_mm_class = automation.last_mm_class

                # Always update check time and latest MM class
                automation.last_checked_at = now
                automation.last_mm_class = mm_class

                # First run: store baseline only, do not notify
                if previous_mm_class is None:
                    db.session.commit()
                    print(
                        f"🟡 Baseline MM class set for '{automation.title}': {mm_class}")
                    continue

                # Send notification only if MM class changed
                if mm_class != previous_mm_class:
                    data_power = get_sersor_data('power')
                    if data_power is None:
                        data_power = 0

                    message = generate_mm_message(
                        mm_class=mm_class,
                        power_watt_per_sec=data_power,
                        dev_name=automation.title,
                        country=automation.user.country
                    )

                    new_recommendation = Recommendation(
                        user_id=automation.user_id,
                        automation_id=automation.id,
                        message=message,
                        mm_class=mm_class,
                        generated_time=now,
                        action_required=True,
                    )

                    db.session.add(new_recommendation)
                    db.session.commit()

                    send_notification(new_recommendation)
                    print(
                        f"✅ MM class changed for '{automation.title}': "
                        f"{previous_mm_class} -> {mm_class}. Notification sent."
                    )
                else:
                    db.session.commit()
                    print(
                        f"ℹ️ No MM class change for '{automation.title}' ({mm_class}). No notification sent.")

            return "Recommendations Updated"

        except Exception as e:
            db.session.rollback()
            print(f"❌ Failed to generate recommendations: {str(e)}")
            return f"Error: {str(e)}"


@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Schedules periodic execution of `generate_recommendations`
    at the automation-defined interval.
    """
    print("🔄 Setting up periodic task for recommendations...")
    sender.add_periodic_task(
        crontab(minute="*/1"),  # Runs every 1 minute
        generate_recommendations.s(),
        name="Generate recommendations every 1 minute"
    )
