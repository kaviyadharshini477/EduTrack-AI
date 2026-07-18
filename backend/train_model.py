import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ------------------------------------
# Load Dataset
# ------------------------------------

df = pd.read_csv("dataset/student_performance_dataset_v2.csv")

print("\nDataset Loaded Successfully!")
print(df.head())

# ------------------------------------
# Features
# ------------------------------------

X = df[
    [
        "study_hours",
        "attendance",
        "sleep_hours",
        "internet_usage",
        "number_of_subjects",
        "average_subject_score",
        "highest_subject_score",
        "lowest_subject_score",
        "score_consistency",
        "previous_overall_score"
    ]
]

# ------------------------------------
# Target
# ------------------------------------

y = df["exam_score"]

# ------------------------------------
# Train/Test Split
# ------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

# ------------------------------------
# Train Random Forest Model
# ------------------------------------

model = RandomForestRegressor(
    n_estimators=100,          # Reduced from 500
    max_depth=10,              # Reduced from 20
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

print("\nTraining model...")

model.fit(X_train, y_train)

print("Training Completed!")

# ------------------------------------
# Predictions
# ------------------------------------

predictions = model.predict(X_test)

# ------------------------------------
# Evaluation
# ------------------------------------

mae = mean_absolute_error(y_test, predictions)
mse = mean_squared_error(y_test, predictions)
rmse = mse ** 0.5
r2 = r2_score(y_test, predictions)

print("\n==============================")
print("MODEL PERFORMANCE")
print("==============================")

print(f"MAE  : {mae:.2f}")
print(f"MSE  : {mse:.2f}")
print(f"RMSE : {rmse:.2f}")
print(f"R²   : {r2:.4f}")

# ------------------------------------
# Feature Importance
# ------------------------------------

importance = pd.DataFrame({
    "Feature": X.columns,
    "Importance": model.feature_importances_
}).sort_values(by="Importance", ascending=False)

print("\nFeature Importance")
print("----------------------------")
print(importance)

# ------------------------------------
# Save Model
# ------------------------------------

MODEL_PATH = "model/student_model.pkl"

joblib.dump(model, MODEL_PATH, compress=3)

print("\n====================================")
print("Model Saved Successfully!")
print("Location :", MODEL_PATH)
print("====================================")