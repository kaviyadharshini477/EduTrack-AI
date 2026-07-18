import requests

url = "http://127.0.0.1:5000/predict"

student_data = {
    "study_hours": 5,
    "attendance": 90,
    "sleep_hours": 7,
    "internet_usage": 3,
    "assignments_completed": 18,
    "previous_score": 82
}

response = requests.post(url, json=student_data)

print("Status Code:", response.status_code)
print("Response:", response.json())