import pandas as pd

# -----------------------------
# STEP 1: Load the Dataset
# -----------------------------

# Relative path (Recommended)
dataset_path = "dataset/student_dataset_10000_rows.csv"

# Read CSV file
df = pd.read_csv(dataset_path)

# -----------------------------
# STEP 2: Display Basic Information
# -----------------------------

print("\n========== FIRST 5 ROWS ==========\n")
print(df.head())

print("\n========== LAST 5 ROWS ==========\n")
print(df.tail())

print("\n========== DATASET SHAPE ==========\n")
print(f"Rows    : {df.shape[0]}")
print(f"Columns : {df.shape[1]}")

print("\n========== COLUMN NAMES ==========\n")
print(df.columns.tolist())

print("\n========== DATA TYPES ==========\n")
print(df.dtypes)

print("\n========== DATASET INFORMATION ==========\n")
df.info()

print("\n========== STATISTICAL SUMMARY ==========\n")
print(df.describe(include='all'))

# -----------------------------
# STEP 3: Check Missing Values
# -----------------------------

print("\n========== MISSING VALUES ==========\n")
print(df.isnull().sum())

# -----------------------------
# STEP 4: Fill Missing Values
# -----------------------------

# Fill numeric columns with mean
numeric_columns = df.select_dtypes(include=['number']).columns

for col in numeric_columns:
    df[col] = df[col].fillna(df[col].mean())

# Fill text columns with "Unknown"
text_columns = df.select_dtypes(include=['object']).columns

for col in text_columns:
    df[col] = df[col].fillna("Unknown")

print("\nMissing values after filling:\n")
print(df.isnull().sum())

# -----------------------------
# STEP 5: Check Duplicate Rows
# -----------------------------

duplicates = df.duplicated().sum()

print("\n========== DUPLICATE ROWS ==========\n")
print(f"Duplicate Rows : {duplicates}")

if duplicates > 0:
    df.drop_duplicates(inplace=True)
    print("Duplicate rows removed.")

# -----------------------------
# STEP 6: Display Final Shape
# -----------------------------

print("\n========== FINAL DATASET SHAPE ==========\n")
print(df.shape)

# -----------------------------
# STEP 7: Save Cleaned Dataset
# -----------------------------

cleaned_path = "dataset/student_dataset_cleaned.csv"

df.to_csv(cleaned_path, index=False)

print("\n==========================================")
print(" Dataset Loaded Successfully")
print(" Cleaned Dataset Saved Successfully")
print(f" Saved as : {cleaned_path}")
print("==========================================")