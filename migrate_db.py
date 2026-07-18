import sqlite3
import json
import numpy as np

def migrate_db():
    print("Starting database migration for Version 2...")
    
    conn = sqlite3.connect('instance/student.db') if sqlite3.connect('instance/student.db') else sqlite3.connect('student.db')
    cursor = conn.cursor()
    
    # Check if old table exists
    try:
        cursor.execute("SELECT * FROM predictions LIMIT 1")
        columns = [description[0] for description in cursor.description]
        if "mathematics" not in columns:
            print("Database is already migrated!")
            return
    except sqlite3.OperationalError:
        print("Predictions table doesn't exist yet, nothing to migrate.")
        return
        
    print("Renaming old table...")
    cursor.execute("ALTER TABLE predictions RENAME TO predictions_old")
    
    print("Creating new schema...")
    cursor.execute('''
    CREATE TABLE predictions (
        id INTEGER NOT NULL, 
        prediction_date VARCHAR(20), 
        predicted_score FLOAT, 
        previous_score FLOAT, 
        stream VARCHAR(100), 
        study_hours FLOAT, 
        attendance FLOAT, 
        sleep_hours FLOAT, 
        internet_usage FLOAT, 
        subjects_data TEXT, 
        number_of_subjects INTEGER, 
        average_subject_score FLOAT, 
        highest_subject_score FLOAT, 
        lowest_subject_score FLOAT, 
        score_consistency FLOAT, 
        user_id INTEGER NOT NULL, 
        PRIMARY KEY (id), 
        FOREIGN KEY(user_id) REFERENCES users (id)
    )
    ''')
    
    print("Migrating data...")
    cursor.execute("SELECT * FROM predictions_old")
    rows = cursor.fetchall()
    
    # We need to map old columns to new columns
    # old columns: id(0), prediction_date(1), predicted_score(2), previous_score(3), stream(4), study_hours(5), attendance(6), sleep_hours(7), internet_usage(8), mathematics(9), physics(10), chemistry(11), biology(12), computer_science(13), english(14), user_id(15)
    
    for row in rows:
        math = row[9]
        phy = row[10]
        chem = row[11]
        bio = row[12]
        cs = row[13]
        eng = row[14]
        stream = row[4]
        
        subjects = []
        if math: subjects.append({"name": "Mathematics", "score": math})
        if phy: subjects.append({"name": "Physics", "score": phy})
        if chem: subjects.append({"name": "Chemistry", "score": chem})
        if eng: subjects.append({"name": "English", "score": eng})
        
        if stream == "Biology" and bio:
            subjects.append({"name": "Biology", "score": bio})
        elif cs:
            subjects.append({"name": "Computer Science", "score": cs})
            
        scores = [s["score"] for s in subjects] if subjects else [0]
        
        subjects_json = json.dumps(subjects)
        num_subjects = len(scores)
        avg_score = float(np.mean(scores))
        highest = float(max(scores))
        lowest = float(min(scores))
        consistency = float(np.std(scores))
        
        cursor.execute('''
        INSERT INTO predictions (
            id, prediction_date, predicted_score, previous_score, stream,
            study_hours, attendance, sleep_hours, internet_usage,
            subjects_data, number_of_subjects, average_subject_score,
            highest_subject_score, lowest_subject_score, score_consistency, user_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            row[0], row[1], row[2], row[3], row[4],
            row[5], row[6], row[7], row[8],
            subjects_json, num_subjects, avg_score,
            highest, lowest, consistency, row[15]
        ))
        
    print("Cleaning up...")
    cursor.execute("DROP TABLE predictions_old")
    conn.commit()
    conn.close()
    
    print("Migration complete! History preserved.")

if __name__ == "__main__":
    migrate_db()
