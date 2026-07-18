from database.database import db
from datetime import datetime

class Goal(db.Model):
    __tablename__ = "goals"

    id = db.Column(db.Integer, primary_key=True)
    target_score = db.Column(db.Float, nullable=False)
    target_study_hours = db.Column(db.Float, nullable=False)
    target_attendance = db.Column(db.Float, nullable=False)
    target_date = db.Column(db.String(20), nullable=False)  # Format: YYYY-MM-DD
    completed = db.Column(db.Boolean, default=False, nullable=False)
    progress = db.Column(db.Integer, default=0, nullable=False)
    current_study_hours = db.Column(db.Float, default=0.0, nullable=False)
    current_attendance = db.Column(db.Float, default=0.0, nullable=False)
    target_assignments = db.Column(db.Integer, default=5, nullable=False)
    completed_assignments = db.Column(db.Integer, default=0, nullable=False)
    target_tests = db.Column(db.Integer, default=3, nullable=False)
    completed_tests = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.String(20), default=lambda: datetime.now().strftime("%Y-%m-%d"), nullable=False)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    def __repr__(self):
        return f"<Goal id={self.id} user_id={self.user_id} target_score={self.target_score}>"
