from database.database import db

class Simulation(db.Model):
    __tablename__ = "simulations"

    id = db.Column(db.Integer, primary_key=True)
    scenario_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.String(20), nullable=False)  # Format: YYYY-MM-DD
    
    # Baseline prediction reference
    prediction_id = db.Column(db.Integer, db.ForeignKey("predictions.id"), nullable=False)
    
    # Baseline details
    baseline_score = db.Column(db.Float, nullable=False)
    
    # Simulated values
    study_hours = db.Column(db.Float, nullable=False)
    attendance = db.Column(db.Float, nullable=False)
    sleep_hours = db.Column(db.Float, nullable=False)
    internet_usage = db.Column(db.Float, nullable=False)
    average_subject_score = db.Column(db.Float, nullable=False)
    stress_level = db.Column(db.Integer, nullable=False)  # 1-10 scale
    exercise_hours = db.Column(db.Float, nullable=False)  # Hours per week
    
    # Output score
    simulated_score = db.Column(db.Float, nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Establish relationships
    prediction = db.relationship("Prediction", backref="simulations", lazy=True)
    user = db.relationship("User", backref="simulations", lazy=True)
