from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    device = db.Column(db.String(100), nullable=False)
    # profile = db.Column(db.String(255), nullable=True)
    country = db.Column(db.String(100), nullable=False)
    # ios_device = db.Column(db.Boolean, default=False)

    automations = db.relationship(
        'Automation', backref='user', cascade="all, delete-orphan")
    recommendations = db.relationship(
        'Recommendation', backref='user', cascade="all, delete-orphan")


class Automation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)

    # how often to run MM prediction/check
    interval = db.Column(db.Integer, nullable=False)

    # last time MM prediction was executed for this automation
    last_checked_at = db.Column(db.DateTime, nullable=True)

    # previous predicted MM class
    last_mm_class = db.Column(db.Integer, nullable=True, default=None)

    created_at = db.Column(db.DateTime, default=datetime.now)

    recommendations = db.relationship(
        'Recommendation', backref='automation', cascade="all, delete-orphan")


class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    automation_id = db.Column(db.Integer, db.ForeignKey(
        'automation.id'), nullable=False)

    message = db.Column(db.String(500), nullable=False)
    mm_class = db.Column(db.Integer, default=0)

    # True if action is pending
    action_required = db.Column(db.Boolean, default=True)
    # "accepted" or "rejected"
    action_taken = db.Column(db.String(20), nullable=True)
    generated_time = db.Column(db.DateTime, default=datetime.now)
    # Time action was taken
    action_time = db.Column(db.DateTime, nullable=True)

    def accept(self):
        """Mark the recommendation as accepted."""
        self.action_required = False
        self.action_taken = "accepted"
        self.action_time = datetime.now()

    def reject(self):
        """Mark the recommendation as rejected."""
        self.action_required = False
        self.action_taken = "rejected"
        self.action_time = datetime.now()


class RelayStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.Boolean, default=True)  # True = ON, False = OFF
    updated_at = db.Column(db.DateTime, default=datetime.now)

    def turn_on(self):
        """Mark the recommendation as accepted."""
        self.state = True
        self.updated_at = datetime.now()

    def turn_off(self):
        """Mark the recommendation as rejected."""
        self.state = False
        self.updated_at = datetime.now()
