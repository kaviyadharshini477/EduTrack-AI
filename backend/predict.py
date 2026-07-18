import joblib
import pandas as pd

# ------------------------------------
# Load Trained Model (Will be generated in Phase 4)
# ------------------------------------

try:
    model = joblib.load("model/student_model.pkl")
except FileNotFoundError:
    model = None


def predict_student_performance(
    study_hours,
    attendance,
    sleep_hours,
    internet_usage,
    number_of_subjects,
    average_subject_score,
    highest_subject_score,
    lowest_subject_score,
    score_consistency,
    previous_overall_score
):
    """
    Predicts the student's final exam score using generic academic features.
    Supports any number of subjects.
    """
    if model is None:
        # Fallback to simple calculation if model is not yet retrained for Version 2.0
        return round(min(100.0, max(0.0, (float(average_subject_score) * 0.7) + (float(previous_overall_score) * 0.3))), 2)

    try:
        input_data = pd.DataFrame([{
            "study_hours": float(study_hours),
            "attendance": float(attendance),
            "sleep_hours": float(sleep_hours),
            "internet_usage": float(internet_usage),
            "number_of_subjects": int(number_of_subjects),
            "average_subject_score": float(average_subject_score),
            "highest_subject_score": float(highest_subject_score),
            "lowest_subject_score": float(lowest_subject_score),
            "score_consistency": float(score_consistency),
            "previous_overall_score": float(previous_overall_score)
        }])

        prediction = model.predict(input_data)[0]

        # -----------------------------
        # Safety Checks
        # -----------------------------
        prediction = max(0.0, min(100.0, prediction))

        return round(float(prediction), 2)
    except Exception as e:
        # If the existing model fails because it's still V1, fallback.
        return round(min(100.0, max(0.0, (float(average_subject_score) * 0.7) + (float(previous_overall_score) * 0.3))), 2)


# ------------------------------------
# Test
# ------------------------------------
if __name__ == "__main__":
    score = predict_student_performance(
        study_hours=6,
        attendance=90,
        sleep_hours=7.5,
        internet_usage=2,
        number_of_subjects=5,
        average_subject_score=88.5,
        highest_subject_score=95.0,
        lowest_subject_score=80.0,
        score_consistency=5.5,
        previous_overall_score=89.4
    )
    print("Predicted Exam Score:", score)