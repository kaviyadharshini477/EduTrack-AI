from flask import session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask import Flask, request, render_template

from backend.predict import predict_student_performance
from backend.ai import get_ai_guidance, get_goal_suggestions, get_mentor_response

# -----------------------------
# Database
# -----------------------------
from database.database import db
from database.user import User
from database.prediction import Prediction
from database.simulation import Simulation
from database.goal import Goal
from database.chat import ChatMessage

app = Flask(__name__)

# -----------------------------
# Flask Configuration
# -----------------------------
app.config["SECRET_KEY"] = "student_performance_secret_key"

import os

database_url = os.getenv("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///student.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize Database
db.init_app(app)

# Create database tables automatically
with app.app_context():
    db.create_all()

# -----------------------------
# Flask-Login Configuration
# -----------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------------------------------
# Home Page
# ---------------------------------------
@app.route("/")
def home():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    return render_template("home.html")

# ---------------------------------------
# Register
# ---------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["full_name"]

        email = request.form["email"].lower().strip()

        password = request.form["password"]

        confirm_password = request.form["confirm_password"]

        # Check password match
        if password != confirm_password:

            flash("Passwords do not match.")

            return redirect(url_for("register"))

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:

            flash("Email already exists.")

            return redirect(url_for("register"))

        # Create new user
        hashed_password = generate_password_hash(password)

        new_user = User(

            full_name=full_name,

            email=email,

            password=hashed_password

        )

        db.session.add(new_user)

        db.session.commit()

        flash("Registration successful! Please login.")

        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------------------------------
# Login
# ---------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form["email"].lower().strip()
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("login.html")


# ---------------------------------------
# Logout
# ---------------------------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


# ---------------------------------------
# Dashboard
# ---------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    predictions = Prediction.query.filter_by(user_id=current_user.id).all()
    
    total_predictions = len(predictions)
    
    if total_predictions > 0:
        avg_score = round(sum(p.predicted_score for p in predictions) / total_predictions, 2)
        highest_score = max(p.predicted_score for p in predictions)
        # Assuming last inserted is latest since we don't have a strict timestamp order, or we can sort by id
        latest_prediction = sorted(predictions, key=lambda x: x.id, reverse=True)[0]
    else:
        avg_score = 0
        highest_score = 0
        latest_prediction = None

    active_goal = Goal.query.filter_by(user_id=current_user.id, completed=False).order_by(Goal.id.desc()).first()
    goal_progress = None
    if active_goal:
        if latest_prediction:
            score_progress = min(100.0, round((latest_prediction.predicted_score / active_goal.target_score) * 100, 2)) if active_goal.target_score > 0 else 0
            study_progress = min(100.0, round((latest_prediction.study_hours / active_goal.target_study_hours) * 100, 2)) if active_goal.target_study_hours > 0 else 0
            attendance_progress = min(100.0, round((latest_prediction.attendance / active_goal.target_attendance) * 100, 2)) if active_goal.target_attendance > 0 else 0
            overall_progress = round((score_progress + study_progress + attendance_progress) / 3, 2)
            goal_progress = {
                "score_progress": score_progress,
                "study_progress": study_progress,
                "attendance_progress": attendance_progress,
                "overall_progress": overall_progress
            }
        else:
            goal_progress = {
                "score_progress": 0,
                "study_progress": 0,
                "attendance_progress": 0,
                "overall_progress": 0
            }
        
    return render_template(
        "dashboard.html",
        total=total_predictions,
        avg=avg_score,
        highest=highest_score,
        latest=latest_prediction,
        active_goal=active_goal,
        goal_progress=goal_progress
    )


# ---------------------------------------
# Profile
# ---------------------------------------
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        
        if not check_password_hash(current_user.password, current_password):
            flash("Current password is incorrect.", "danger")
        elif new_password != confirm_password:
            flash("New passwords do not match.", "danger")
        else:
            current_user.password = generate_password_hash(new_password)
            db.session.commit()
            flash("Password updated successfully.", "success")
            
        return redirect(url_for("profile"))
        
    total_predictions = Prediction.query.filter_by(user_id=current_user.id).count()
    return render_template("profile.html", total_predictions=total_predictions)


# ---------------------------------------
# History
# ---------------------------------------
@app.route("/history")
@login_required
def history():
    predictions = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.id.desc()).all()
    return render_template("history.html", predictions=predictions)

@app.route("/delete_prediction/<int:prediction_id>", methods=["POST"])
@login_required
def delete_prediction(prediction_id):
    prediction = Prediction.query.get_or_404(prediction_id)
    if prediction.user_id != current_user.id:
        flash("You do not have permission to delete this record.", "danger")
        return redirect(url_for("history"))
        
    db.session.delete(prediction)
    db.session.commit()
    flash("Prediction deleted successfully.", "success")
    return redirect(url_for("history"))


# ---------------------------------------
# Analytics
# ---------------------------------------
@app.route("/analytics")
@login_required
def analytics():
    import json
    predictions = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.id.asc()).all()
    
    # Prepare data for Chart.js
    dates = [p.prediction_date for p in predictions]
    scores = [p.predicted_score for p in predictions]
    previous_scores = [p.previous_score for p in predictions]
    avg_subject_scores = [p.average_subject_score for p in predictions]
    
    # Extract subjects from the most recent prediction for a detailed breakdown
    latest_subjects_data = []
    if predictions and predictions[-1].subjects_data:
        try:
            latest_subjects_data = json.loads(predictions[-1].subjects_data)
        except:
            latest_subjects_data = []
    
    return render_template("analytics.html", dates=dates, scores=scores, previous_scores=previous_scores, avg_scores=avg_subject_scores, latest_subjects=latest_subjects_data)


# ---------------------------------------
# Prediction Page
# ---------------------------------------
@app.route("/predict")
@login_required
def predict_page():
    return render_template("predict.html")


# ---------------------------------------
# Report Card Extraction API
# ---------------------------------------
@app.route("/api/extract-report-card", methods=["POST"])
@login_required
def extract_report_card():
    import base64
    import json
    
    if "file" not in request.files:
        return {"status": "error", "message": "No file uploaded"}, 400
        
    file = request.files["file"]
    if file.filename == "":
        return {"status": "error", "message": "No file selected"}, 400
        
    mime_type = file.content_type
    filename = file.filename.lower()
    
    try:
        if filename.endswith(".pdf") or mime_type == "application/pdf":
            # PDF Text Extraction
            pdf_text = ""
            from pypdf import PdfReader
            reader = PdfReader(file.stream)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    pdf_text += t + "\n"
            
            if not pdf_text.strip():
                return {"status": "error", "message": "Could not extract any text from the PDF. The PDF may be scanned (image-based). Please try uploading it as an image."}, 400
                
            prompt = f"""
Analyze the following text extracted from a student's report card or transcript.
Extract all subject names and their corresponding numerical scores or grades (convert letter grades to numerical percentages if possible: e.g. A=95, B=85, C=75, D=65, F=50, or use the actual score if present).
Return ONLY a JSON object containing a "subjects" key with a list of subjects, where each subject has a "name" and "score" (a float or integer between 0 and 100).
Do not include any formatting, explanation, or markdown code blocks.
Response format:
{{
  "subjects": [
    {{"name": "Math", "score": 85.0}},
    {{"name": "Science", "score": 90.0}}
  ]
}}
If no subjects or scores are found, return {{"subjects": []}}.

Report Card Text:
{pdf_text}
"""
            from backend.ai import client
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
        else:
            # Image Extraction (using Scout Vision Model)
            image_bytes = file.read()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            prompt = """
Analyze this report card, transcript, or academic document image.
Extract all subject names and their corresponding numerical scores or grades (convert letter grades to numerical percentages if possible: e.g. A=95, B=85, C=75, D=65, F=50, or use the actual score if present).
Return ONLY a JSON object containing a "subjects" key with a list of subjects, where each subject has a "name" and "score" (a float or integer between 0 and 100).
Do not include any formatting, explanation, or markdown code blocks.
Response format:
{
  "subjects": [
    {"name": "Math", "score": 85.0},
    {"name": "Science", "score": 90.0}
  ]
}
If no subjects or scores are found, return {"subjects": []}.
"""
            from backend.ai import client
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}",
                                },
                            },
                        ],
                    }
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
        result_content = response.choices[0].message.content
        extracted_data = json.loads(result_content)
        
        return {
            "status": "success",
            "subjects": extracted_data.get("subjects", [])
        }
        
    except Exception as e:
        print("Report card extraction error:", e)
        return {"status": "error", "message": str(e)}, 500



# ---------------------------------------
# Prediction API
# ---------------------------------------
@app.route("/api/predict", methods=["POST"])
@login_required
def predict_api():

    import json
    import numpy as np
    from datetime import datetime

    name = current_user.full_name
    age = request.form.get("age", 18)
    date = datetime.now().strftime("%Y-%m-%d")
    stream = request.form.get("stream", "General")

    # ---------------------------------------
    # Study Details
    # ---------------------------------------
    try:
        study_hours = float(request.form.get("study_hours", 0))
        attendance = float(request.form.get("attendance", 0))
        sleep_hours = float(request.form.get("sleep_hours", 0))
        internet_usage = float(request.form.get("internet_usage", 0))
    except ValueError:
        flash("Invalid study details provided.", "danger")
        return redirect(url_for('predict_page'))

    # ---------------------------------------
    # Dynamic Subjects
    # ---------------------------------------
    try:
        subjects_json_str = request.form.get("subjects_json", "[]")
        subjects = json.loads(subjects_json_str)
    except:
        subjects = []
        
    if not subjects:
        flash("You must add at least one subject to predict.", "danger")
        return redirect(url_for('predict_page'))

    scores = [float(s.get("score", 0)) for s in subjects]

    # Calculate V2 generic features
    number_of_subjects = len(scores)
    average_subject_score = float(np.mean(scores))
    highest_subject_score = float(max(scores))
    lowest_subject_score = float(min(scores))
    score_consistency = float(np.std(scores))
    
    # In V2, previous overall score might be passed, or we default to average
    previous_score = request.form.get("previous_overall_score")
    if previous_score:
        previous_score = float(previous_score)
    else:
        previous_score = average_subject_score

    # ---------------------------------------
    # Predict Score
    # ---------------------------------------
    predicted_score = predict_student_performance(
        study_hours,
        attendance,
        sleep_hours,
        internet_usage,
        number_of_subjects,
        average_subject_score,
        highest_subject_score,
        lowest_subject_score,
        score_consistency,
        previous_score
    )

    predicted_score = max(0, min(100, round(float(predicted_score), 2)))

    # ---------------------------------------
    # Student Dictionary (For AI Prompt & Result Page)
    # ---------------------------------------
    student = {
        "name": name,
        "age": age,
        "date": date,
        "stream": stream,
        "study_hours": study_hours,
        "attendance": attendance,
        "sleep_hours": sleep_hours,
        "internet_usage": internet_usage,
        "subjects": subjects, # Passed dynamically
        "average_score": average_subject_score,
        "previous_score": previous_score
    }

    # ---------------------------------------
    # AI Guidance
    # ---------------------------------------
    ai_guidance = get_ai_guidance(student, predicted_score)

    # ---------------------------------------
    # Save Prediction to Database (V2 Format)
    # ---------------------------------------
    new_prediction = Prediction(
        prediction_date=date,
        predicted_score=predicted_score,
        previous_score=previous_score,
        stream=stream,
        study_hours=study_hours,
        attendance=attendance,
        sleep_hours=sleep_hours,
        internet_usage=internet_usage,
        subjects_data=json.dumps(subjects),
        number_of_subjects=number_of_subjects,
        average_subject_score=average_subject_score,
        highest_subject_score=highest_subject_score,
        lowest_subject_score=lowest_subject_score,
        score_consistency=score_consistency,
        user_id=current_user.id
    )
    
    db.session.add(new_prediction)
    db.session.commit()

    # ---------------------------------------
    # Result Page
    # ---------------------------------------

    return render_template(

        "result.html",

        student=student,

        predicted_score=predicted_score,

        previous_score=previous_score,

        ai_guidance=ai_guidance

    )


# ---------------------------------------
# What-If Simulator
# ---------------------------------------
@app.route("/simulator")
@login_required
def simulator():
    predictions = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.id.desc()).all()
    simulations = Simulation.query.filter_by(user_id=current_user.id).order_by(Simulation.id.desc()).all()
    return render_template(
        "simulator.html",
        predictions=predictions,
        simulations=simulations
    )

@app.route("/simulate", methods=["POST"])
@login_required
def api_simulate():
    import json
    import numpy as np
    
    data = request.get_json()
    if not data:
        return {"error": "Invalid request payload"}, 400
        
    prediction_id = data.get("prediction_id")
    study_hours = float(data.get("study_hours", 0))
    attendance = float(data.get("attendance", 0))
    sleep_hours = float(data.get("sleep_hours", 0))
    internet_usage = float(data.get("internet_usage", 0))
    average_subject_score = float(data.get("average_subject_score", 0))
    stress_level = int(data.get("stress_level", 5))
    exercise_hours = float(data.get("exercise_hours", 2))
    
    prediction = Prediction.query.get_or_404(prediction_id)
    if prediction.user_id != current_user.id:
        return {"error": "Unauthorized access to this prediction"}, 403
        
    # Scale subject marks proportionally
    try:
        subjects = json.loads(prediction.subjects_data)
    except:
        subjects = []
        
    baseline_avg = prediction.average_subject_score
    if baseline_avg > 0:
        scale_factor = average_subject_score / baseline_avg
        new_scores = [max(0.0, min(100.0, float(s.get("score", 0)) * scale_factor)) for s in subjects]
    else:
        new_scores = [average_subject_score] * len(subjects) if subjects else [average_subject_score]
        
    # Recompute statistics
    number_of_subjects = len(new_scores)
    highest_subject_score = float(max(new_scores)) if new_scores else 0
    lowest_subject_score = float(min(new_scores)) if new_scores else 0
    score_consistency = float(np.std(new_scores)) if new_scores else 0
    
    # Run ML prediction model
    ml_predicted_score = predict_student_performance(
        study_hours=study_hours,
        attendance=attendance,
        sleep_hours=sleep_hours,
        internet_usage=internet_usage,
        number_of_subjects=number_of_subjects,
        average_subject_score=average_subject_score,
        highest_subject_score=highest_subject_score,
        lowest_subject_score=lowest_subject_score,
        score_consistency=score_consistency,
        previous_overall_score=prediction.previous_score
    )
    
    # Lifestyle offsets
    # Stress Level Offset (Scale 1-10, Default: 5)
    if stress_level > 5:
        stress_delta = (stress_level - 5) * -0.6  # Up to -3%
    else:
        stress_delta = (5 - stress_level) * 0.3   # Up to +1.2%
        
    # Exercise Hours Offset (Hours/week, Default: 2)
    if exercise_hours > 2:
        if exercise_hours <= 6:
            exercise_delta = (exercise_hours - 2) * 0.4  # Up to +1.6%
        else:
            exercise_delta = 1.6 - (exercise_hours - 6) * 0.3  # Fatigue effect, drops beyond 6 hrs
    else:
        exercise_delta = (exercise_hours - 2) * 0.5   # Down to -1%
        
    # Combine values and bound to [0, 100]
    simulated_score = max(0.0, min(100.0, round(ml_predicted_score + stress_delta + exercise_delta, 2)))
    difference = round(simulated_score - prediction.predicted_score, 2)
    
    return {
        "baseline_score": prediction.predicted_score,
        "simulated_score": simulated_score,
        "difference": difference,
        "metrics": {
            "study_hours": study_hours,
            "attendance": attendance,
            "sleep_hours": sleep_hours,
            "internet_usage": internet_usage,
            "average_subject_score": average_subject_score,
            "stress_level": stress_level,
            "exercise_hours": exercise_hours
        }
    }

@app.route("/api/simulations/save", methods=["POST"])
@login_required
def save_simulation():
    from datetime import datetime
    data = request.get_json()
    if not data:
        return {"error": "Invalid request payload"}, 400
        
    scenario_name = data.get("scenario_name", "Simulation Scenario").strip()
    prediction_id = data.get("prediction_id")
    baseline_score = float(data.get("baseline_score", 0))
    study_hours = float(data.get("study_hours", 0))
    attendance = float(data.get("attendance", 0))
    sleep_hours = float(data.get("sleep_hours", 0))
    internet_usage = float(data.get("internet_usage", 0))
    average_subject_score = float(data.get("average_subject_score", 0))
    stress_level = int(data.get("stress_level", 5))
    exercise_hours = float(data.get("exercise_hours", 2))
    simulated_score = float(data.get("simulated_score", 0))
    
    prediction = Prediction.query.get_or_404(prediction_id)
    if prediction.user_id != current_user.id:
        return {"error": "Unauthorized access"}, 403
        
    new_sim = Simulation(
        scenario_name=scenario_name,
        created_at=datetime.now().strftime("%Y-%m-%d"),
        prediction_id=prediction_id,
        baseline_score=baseline_score,
        study_hours=study_hours,
        attendance=attendance,
        sleep_hours=sleep_hours,
        internet_usage=internet_usage,
        average_subject_score=average_subject_score,
        stress_level=stress_level,
        exercise_hours=exercise_hours,
        simulated_score=simulated_score,
        user_id=current_user.id
    )
    
    db.session.add(new_sim)
    db.session.commit()
    
    return {"status": "success", "message": "Simulation scenario saved successfully."}

@app.route("/api/simulations/delete/<int:simulation_id>", methods=["POST"])
@login_required
def delete_simulation(simulation_id):
    sim = Simulation.query.get_or_404(simulation_id)
    if sim.user_id != current_user.id:
        return {"error": "Unauthorized access"}, 403
        
    db.session.delete(sim)
    db.session.commit()
    return {"status": "success", "message": "Simulation deleted successfully."}

# ---------------------------------------
# Goal Tracker
# ---------------------------------------
@app.route("/goals")
@login_required
def goals_page():
    latest_prediction = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.id.desc()).first()
    
    goals = Goal.query.filter_by(user_id=current_user.id).order_by(Goal.id.desc()).all()
    
    active_goals = [g for g in goals if not g.completed]
    completed_goals = [g for g in goals if g.completed]
    
    # Calculate progress for active goals
    active_goals_with_progress = []
    ai_suggestions = None
    latest_active_goal = None
    
    if active_goals:
        latest_active_goal = active_goals[0]
        
    for goal in active_goals:
        pred_score = latest_prediction.predicted_score if latest_prediction else 0.0
        
        score_pct = min(100.0, round((pred_score / goal.target_score) * 100, 2)) if goal.target_score > 0 else 100.0
        study_pct = min(100.0, round((goal.current_study_hours / goal.target_study_hours) * 100, 2)) if goal.target_study_hours > 0 else 100.0
        attendance_pct = min(100.0, round((goal.current_attendance / goal.target_attendance) * 100, 2)) if goal.target_attendance > 0 else 100.0
        tests_pct = min(100.0, round((goal.completed_tests / goal.target_tests) * 100, 2)) if goal.target_tests > 0 else 100.0
        
        overall_pct = round((score_pct + study_pct + attendance_pct + tests_pct) / 4, 2)
        
        # Sync to database
        goal.progress = int(overall_pct)
        
        # Check automatic completion
        if (pred_score >= goal.target_score and 
            goal.current_study_hours >= goal.target_study_hours and 
            goal.current_attendance >= goal.target_attendance and 
            goal.completed_tests >= goal.target_tests):
            goal.completed = True
            goal.progress = 100
            db.session.commit()
            completed_goals.append(goal)
            continue
            
        db.session.commit()
        
        # Calculate remaining stats
        remaining_marks = max(0.0, round(goal.target_score - pred_score, 2))
        remaining_study_hours = max(0.0, round(goal.target_study_hours - goal.current_study_hours, 2))
        remaining_attendance = max(0.0, round(goal.target_attendance - goal.current_attendance, 2))
        
        # Estimate completion date
        from datetime import datetime, timedelta
        estimated_date = goal.target_date
        try:
            created_dt = datetime.strptime(goal.created_at, "%Y-%m-%d")
            today = datetime.now()
            days_elapsed = (today - created_dt).days
            if days_elapsed <= 0:
                days_elapsed = 1
            progress_fraction = overall_pct / 100.0
            if progress_fraction > 0.05:
                estimated_total_days = days_elapsed / progress_fraction
                est_completion = created_dt + timedelta(days=int(estimated_total_days))
                tomorrow = today + timedelta(days=1)
                if est_completion < tomorrow:
                    est_completion = tomorrow
                estimated_date = est_completion.strftime("%Y-%m-%d")
        except Exception as e:
            print("Estimate date error:", e)
            
        active_goals_with_progress.append({
            "goal": goal,
            "score_pct": score_pct,
            "study_pct": study_pct,
            "attendance_pct": attendance_pct,
            "tests_pct": tests_pct,
            "overall_pct": overall_pct,
            "remaining_marks": remaining_marks,
            "remaining_study_hours": remaining_study_hours,
            "remaining_attendance": remaining_attendance,
            "estimated_completion_date": estimated_date
        })
        
    if latest_active_goal:
        ai_suggestions = get_goal_suggestions(latest_prediction, latest_active_goal)
        
    return render_template(
        "goals.html",
        active_goals=active_goals_with_progress,
        completed_goals=completed_goals,
        latest_prediction=latest_prediction,
        ai_suggestions=ai_suggestions
    )

@app.route("/goals/create", methods=["POST"])
@login_required
def create_goal():
    try:
        target_score = float(request.form.get("target_score", 0))
        target_study_hours = float(request.form.get("target_study_hours", 0))
        target_attendance = float(request.form.get("target_attendance", 0))
        target_date = request.form.get("target_date")
    except ValueError:
        flash("Invalid target values provided.", "danger")
        return redirect(url_for("goals_page"))
        
    if not target_date:
        flash("Target date is required.", "danger")
        return redirect(url_for("goals_page"))
        
    # Validation bounds
    if not (0 <= target_score <= 100):
        flash("Target score must be between 0 and 100.", "danger")
        return redirect(url_for("goals_page"))
        
    if not (0 <= target_study_hours <= 24):
        flash("Target study hours must be between 0 and 24.", "danger")
        return redirect(url_for("goals_page"))
        
    if not (0 <= target_attendance <= 100):
        flash("Target attendance must be between 0 and 100.", "danger")
        return redirect(url_for("goals_page"))
        
    new_goal = Goal(
        target_score=target_score,
        target_study_hours=target_study_hours,
        target_attendance=target_attendance,
        target_date=target_date,
        target_assignments=5,
        target_tests=3,
        user_id=current_user.id
    )
    
    db.session.add(new_goal)
    db.session.commit()
    flash("Goal created successfully!", "success")
    return redirect(url_for("goals_page"))

@app.route("/goals/edit/<int:goal_id>", methods=["GET", "POST"])
@login_required
def edit_goal(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if goal.user_id != current_user.id:
        flash("You do not have permission to edit this goal.", "danger")
        return redirect(url_for("goals_page"))
        
    if request.method == "POST":
        try:
            target_score = float(request.form.get("target_score", 0))
            target_study_hours = float(request.form.get("target_study_hours", 0))
            target_attendance = float(request.form.get("target_attendance", 0))
            target_date = request.form.get("target_date")
        except ValueError:
            flash("Invalid target values provided.", "danger")
            return redirect(url_for("edit_goal", goal_id=goal_id))
            
        if not target_date:
            flash("Target date is required.", "danger")
            return redirect(url_for("edit_goal", goal_id=goal_id))
            
        if not (0 <= target_score <= 100) or not (0 <= target_study_hours <= 24) or not (0 <= target_attendance <= 100):
            flash("Values are out of range.", "danger")
            return redirect(url_for("edit_goal", goal_id=goal_id))
            
        goal.target_score = target_score
        goal.target_study_hours = target_study_hours
        goal.target_attendance = target_attendance
        goal.target_date = target_date
        
        db.session.commit()
        flash("Goal updated successfully!", "success")
        return redirect(url_for("goals_page"))
        
    return render_template("edit_goal.html", goal=goal)

@app.route("/goals/delete/<int:goal_id>", methods=["POST"])
@login_required
def delete_goal(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if goal.user_id != current_user.id:
        flash("You do not have permission to delete this goal.", "danger")
        return redirect(url_for("goals_page"))
        
    db.session.delete(goal)
    db.session.commit()
    flash("Goal deleted successfully.", "success")
    return redirect(url_for("goals_page"))

@app.route("/goals/toggle/<int:goal_id>", methods=["POST"])
@login_required
def toggle_goal(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if goal.user_id != current_user.id:
        flash("You do not have permission to modify this goal.", "danger")
        return redirect(url_for("goals_page"))
        
    goal.completed = not goal.completed
    if goal.completed:
        goal.progress = 100
    else:
        goal.progress = 0
    db.session.commit()
    
    status = "completed" if goal.completed else "reopened"
    flash(f"Goal marked as {status}!", "success")
    return redirect(url_for("goals_page"))

@app.route("/goals/update_stats/<int:goal_id>", methods=["POST"])
@login_required
def update_goal_stats(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if goal.user_id != current_user.id:
        flash("You do not have permission to modify this goal.", "danger")
        return redirect(url_for("goals_page"))
        
    try:
        current_study_hours = float(request.form.get("current_study_hours", 0))
        current_attendance = float(request.form.get("current_attendance", 0))
        completed_tests = int(request.form.get("completed_tests", 0))
    except ValueError:
        flash("Invalid stats values provided.", "danger")
        return redirect(url_for("goals_page"))
        
    goal.current_study_hours = max(0.0, current_study_hours)
    goal.current_attendance = max(0.0, min(100.0, current_attendance))
    goal.completed_tests = max(0, completed_tests)
    
    # Recalculate overall progress
    latest_prediction = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.id.desc()).first()
    pred_score = latest_prediction.predicted_score if latest_prediction else 0.0
    
    score_pct = min(100.0, (pred_score / goal.target_score) * 100) if goal.target_score > 0 else 100.0
    study_pct = min(100.0, (goal.current_study_hours / goal.target_study_hours) * 100) if goal.target_study_hours > 0 else 100.0
    attendance_pct = min(100.0, (goal.current_attendance / goal.target_attendance) * 100) if goal.target_attendance > 0 else 100.0
    tests_pct = min(100.0, (goal.completed_tests / goal.target_tests) * 100) if goal.target_tests > 0 else 100.0
    
    overall_pct = round((score_pct + study_pct + attendance_pct + tests_pct) / 4, 2)
    goal.progress = int(overall_pct)
    
    # Automatically mark the goal as completed when all target conditions are achieved
    if (pred_score >= goal.target_score and 
        goal.current_study_hours >= goal.target_study_hours and 
        goal.current_attendance >= goal.target_attendance and 
        goal.completed_tests >= goal.target_tests):
        goal.completed = True
        goal.progress = 100
        flash("Congratulations! All target conditions achieved. Goal automatically marked as completed!", "success")
    else:
        goal.completed = False
        
    db.session.commit()
    flash("Goal metrics updated successfully!", "success")
    return redirect(url_for("goals_page"))




# ---------------------------------------
# AI Academic Mentor Routes
# ---------------------------------------
@app.route("/ai-mentor")
@login_required
def ai_mentor():
    chat_history = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.id.asc()).all()
    suggested_prompts = [
        "How can I improve my score?",
        "Create my study plan.",
        "Explain my prediction.",
        "Help me reach my goal.",
        "Suggest a career."
    ]
    return render_template(
        "ai_mentor.html",
        chat_history=chat_history,
        suggested_prompts=suggested_prompts
    )

@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    data = request.get_json()
    if not data or "message" not in data:
        return {"error": "Message is required"}, 400
        
    message = data.get("message").strip()
    if not message:
        return {"error": "Message cannot be empty"}, 400
        
    # Fetch user data to build student profile
    latest_pred = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.id.desc()).first()
    all_preds = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.id.desc()).all()
    all_goals = Goal.query.filter_by(user_id=current_user.id).order_by(Goal.id.desc()).all()
    
    # Build history summary
    pred_history_items = []
    total_score = 0
    for p in all_preds:
        pred_history_items.append(f"Date: {p.prediction_date}, Score: {p.predicted_score}%, Stream: {p.stream}, Avg Subject Marks: {p.average_subject_score}%")
        total_score += p.predicted_score
    
    pred_history_summary = "\n".join(pred_history_items) if pred_history_items else "No predictions made yet."
    
    # Build goals summary
    goals_items = []
    for g in all_goals:
        status = "Completed" if g.completed else "Active"
        goals_items.append(f"Target: {g.target_score}% score, {g.target_study_hours} hrs/day study, {g.target_attendance}% attendance by {g.target_date} ({status})")
    
    goals_summary = "\n".join(goals_items) if goals_items else "No academic goals set yet."
    
    # Compile student profile for the prompt
    student_profile = {
        "name": current_user.full_name,
        "latest_prediction_score": latest_pred.predicted_score if latest_pred else "N/A",
        "latest_prediction_date": latest_pred.prediction_date if latest_pred else "N/A",
        "stream": latest_pred.stream if latest_pred else "N/A",
        "study_hours": latest_pred.study_hours if latest_pred else "N/A",
        "sleep_hours": latest_pred.sleep_hours if latest_pred else "N/A",
        "internet_usage": latest_pred.internet_usage if latest_pred else "N/A",
        "attendance": latest_pred.attendance if latest_pred else "N/A",
        "average_subject_score": latest_pred.average_subject_score if latest_pred else "N/A",
        "prediction_history_summary": pred_history_summary,
        "goals_summary": goals_summary
    }
    
    # Save user message to database
    user_chat = ChatMessage(user_id=current_user.id, sender="user", message=message)
    db.session.add(user_chat)
    db.session.commit()
    
    # Load recent chat history (e.g. last 15 messages) to provide conversation memory
    recent_db_messages = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.id.desc()).limit(15).all()
    recent_db_messages.reverse()
    
    chat_history_list = []
    # Exclude the newly added user message (which is the last one in recent_db_messages)
    for msg in recent_db_messages[:-1]:
        chat_history_list.append({
            "sender": msg.sender,
            "message": msg.message
        })
        
    # Generate AI reply
    reply = get_mentor_response(student_profile, message, chat_history_list)
    
    # Save AI assistant message to database
    assistant_chat = ChatMessage(user_id=current_user.id, sender="assistant", message=reply)
    db.session.add(assistant_chat)
    db.session.commit()
    
    return {
        "status": "success",
        "reply": reply
    }

@app.route("/api/chat/clear", methods=["POST"])
@login_required
def api_clear_chat():
    ChatMessage.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return {"status": "success", "message": "Chat history cleared successfully"}


# ---------------------------------------
# Run App
# ---------------------------------------

if __name__ == "__main__":

    app.run(debug=True)