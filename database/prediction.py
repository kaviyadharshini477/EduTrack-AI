from database.database import db

class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    prediction_date = db.Column(db.String(20))
    predicted_score = db.Column(db.Float)
    previous_score = db.Column(db.Float)
    stream = db.Column(db.String(100))

    study_hours = db.Column(db.Float)
    attendance = db.Column(db.Float)
    sleep_hours = db.Column(db.Float)
    internet_usage = db.Column(db.Float)

    # JSON string of dynamic subjects: [{"name": "Math", "score": 90}, ...]
    subjects_data = db.Column(db.Text)

    # New statistical columns
    number_of_subjects = db.Column(db.Integer)
    average_subject_score = db.Column(db.Float)
    highest_subject_score = db.Column(db.Float)
    lowest_subject_score = db.Column(db.Float)
    score_consistency = db.Column(db.Float)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )