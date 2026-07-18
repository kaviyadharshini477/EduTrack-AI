import pandas as pd
import random
import os
import numpy as np

random.seed(42)

# -----------------------------------------
# Helper Functions
# -----------------------------------------

def random_between(low, high):
    return round(random.uniform(low, high), 1)

def attendance_status(attendance):
    if attendance >= 75:
        return "Eligible"
    return "Shortage"

def performance_level(score):
    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Average"
    return "Needs Improvement"

def exam_formula(
        previous_score,
        study_hours,
        attendance,
        sleep,
        internet,
        average_subject_score,
        score_consistency):

    # Base score is a weighted blend of average score and previous score
    score = (average_subject_score * 0.7) + (previous_score * 0.3)

    # -----------------------------
    # Study Hours
    # -----------------------------
    if study_hours >= 8:
        score += random.uniform(4, 7)
    elif study_hours >= 6:
        score += random.uniform(2, 5)
    elif study_hours >= 4:
        score += random.uniform(0, 2)
    elif study_hours >= 2:
        score -= random.uniform(1, 3)
    else:
        score -= random.uniform(3, 6)

    # -----------------------------
    # Attendance
    # -----------------------------
    if attendance >= 95:
        score += random.uniform(3, 5)
    elif attendance >= 85:
        score += random.uniform(2, 4)
    elif attendance >= 75:
        score += random.uniform(0, 2)
    elif attendance >= 60:
        score -= random.uniform(2, 5)
    else:
        score -= random.uniform(6, 10)

    # -----------------------------
    # Sleep
    # -----------------------------
    if 7 <= sleep <= 8:
        score += random.uniform(1, 2)
    elif sleep < 5:
        score -= random.uniform(2, 4)

    # -----------------------------
    # Internet Usage
    # -----------------------------
    if internet <= 2:
        score += random.uniform(1, 2)
    elif internet >= 8:
        score -= random.uniform(2, 4)

    # -----------------------------
    # Consistency Penalty
    # -----------------------------
    # If consistency is high (i.e. standard deviation is high, highly inconsistent), subtract some score
    if score_consistency > 15:
        score -= random.uniform(1, 3)

    # -----------------------------
    # Natural Variation
    # -----------------------------
    score += random.uniform(-2, 2)

    score = max(0, min(100, score))

    return round(score, 2)

def generate_student():

    r = random.random()
    if r < 0.20:
        category = "Excellent"
    elif r < 0.45:
        category = "Good"
    elif r < 0.80:
        category = "Average"
    elif r < 0.95:
        category = "Weak"
    else:
        category = "At Risk"

    # Number of subjects between 3 and 8
    number_of_subjects = random.randint(3, 8)

    if category == "Excellent":
        study_hours = random_between(7, 10)
        attendance = random.randint(88, 100)
        sleep = random_between(7, 8.5)
        internet = random_between(0.5, 2.5)
        base_scores = [random.randint(85, 100) for _ in range(number_of_subjects)]

    elif category == "Good":
        study_hours = random_between(5, 7)
        attendance = random.randint(75, 90)
        sleep = random_between(6.5, 8)
        internet = random_between(2, 4)
        base_scores = [random.randint(70, 92) for _ in range(number_of_subjects)]

    elif category == "Average":
        study_hours = random_between(3, 5)
        attendance = random.randint(60, 82)
        sleep = random_between(5.5, 7.5)
        internet = random_between(3, 6)
        base_scores = [random.randint(50, 78) for _ in range(number_of_subjects)]

    elif category == "Weak":
        study_hours = random_between(1.5, 3.5)
        attendance = random.randint(40, 70)
        sleep = random_between(4.5, 6.5)
        internet = random_between(5, 8)
        base_scores = [random.randint(30, 65) for _ in range(number_of_subjects)]

    else:
        study_hours = random_between(0.5, 2)
        attendance = random.randint(20, 50)
        sleep = random_between(3.5, 5.5)
        internet = random_between(7, 10)
        base_scores = [random.randint(15, 45) for _ in range(number_of_subjects)]

    average_subject_score = round(float(np.mean(base_scores)), 2)
    highest_subject_score = float(max(base_scores))
    lowest_subject_score = float(min(base_scores))
    score_consistency = round(float(np.std(base_scores)), 2)
    
    # Previous score has some correlation with current average
    previous_score = round(max(0, min(100, average_subject_score + random.uniform(-10, 10))), 2)

    exam_score = exam_formula(
        previous_score,
        study_hours,
        attendance,
        sleep,
        internet,
        average_subject_score,
        score_consistency
    )

    return {
        "study_hours": study_hours,
        "attendance": attendance,
        "sleep_hours": sleep,
        "internet_usage": internet,
        "number_of_subjects": number_of_subjects,
        "average_subject_score": average_subject_score,
        "highest_subject_score": highest_subject_score,
        "lowest_subject_score": lowest_subject_score,
        "score_consistency": score_consistency,
        "previous_overall_score": previous_score,
        "exam_score": exam_score,
        "performance_level": performance_level(exam_score),
        "attendance_status": attendance_status(attendance)
    }

# ----------------------------------
# Generate Dataset
# ----------------------------------

def generate_dataset(num_rows=20000):

    students = []
    print(f"\nGenerating {num_rows:,} student records (Version 2.0)...\n")

    for i in range(num_rows):
        students.append(generate_student())
        if (i + 1) % 1000 == 0:
            print(f"{i + 1:,} records generated...")

    df = pd.DataFrame(students)

    # ----------------------------------
    # Shuffle Dataset
    # ----------------------------------
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    # ----------------------------------
    # Create Folder
    # ----------------------------------
    os.makedirs("dataset", exist_ok=True)
    output_path = "dataset/student_performance_dataset_v2.csv"
    df.to_csv(output_path, index=False)

    print("\n========================================")
    print("Dataset Generated Successfully!")
    print("========================================")
    print(f"Rows    : {len(df):,}")
    print(f"Columns : {len(df.columns)}")
    print(f"Saved To: {output_path}")
    print("========================================")

    return df

# ----------------------------------
# Main Program
# ----------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print(" Student Performance Dataset Generator (V2) ")
    print("=" * 60)
    df = generate_dataset(20000)
    print("\nFirst 5 Records\n")
    print(df.head())