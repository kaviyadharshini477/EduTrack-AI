import os
import json
from groq import Groq
from dotenv import load_dotenv

# ---------------------------------
# Load .env
# ---------------------------------

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def get_ai_guidance(student, predicted_score):

    # ---------------------------------
    # Attendance Rule
    # ---------------------------------

    if student.get("attendance", 100) < 75:
        return {
            "performance_level": "Attendance Shortage",
            "prediction_reason": [
                "Attendance below 75%",
                "Prediction affected by attendance shortage"
            ],
            "strengths": [
                "Academic evaluation limited due to attendance shortage."
            ],
            "weaknesses": [
                f"Attendance is only {student.get('attendance', 0)}%."
            ],
            "study_plan": [
                "Attend every class.",
                "Revise daily.",
                "Meet faculty advisor.",
                "Maintain attendance above 75%."
            ],
            "career_suggestions": [
                {
                    "career": "Not Available",
                    "reason": "Improve attendance first."
                }
            ],
            "motivation": "Improve attendance to receive complete guidance."
        }

    # ---------------------------------
    # Dynamic Subjects Formatting
    # ---------------------------------
    
    subjects_formatted = ""
    for subj in student.get("subjects", []):
        subjects_formatted += f"- {subj['name']}: {subj['score']}\n"

    # ---------------------------------
    # Prompt
    # ---------------------------------

    prompt = f"""
You are an expert academic advisor.

Student Profile:
Course/Stream: {student.get("stream", "Unknown")}
Study Hours/Day: {student.get("study_hours", 0)}
Attendance: {student.get("attendance", 0)}%
Sleep Hours/Day: {student.get("sleep_hours", 0)}
Internet Usage/Day: {student.get("internet_usage", 0)}

Subjects & Scores:
{subjects_formatted}

Previous Overall Score/CGPA: {student.get("previous_score", 0)}
Predicted Final Score: {predicted_score}

Based on this specific student profile and the subjects they are taking, provide personalized academic advice.

Return ONLY JSON.

Rules:
- Keep everything SHORT.
- No paragraphs.
- No extra explanation.
- Maximum 3 strengths.
- Maximum 3 weaknesses (relate them to specific low-scoring subjects if applicable).
- Maximum 4 study plan points.
- Maximum 4 prediction reasons.
- Exactly 3 career suggestions (tailor these careers to the student's Course/Stream and best subjects!).
- Career reason: less than 10 words.
- Motivation: one short sentence.

JSON Format:
{{
"performance_level":"",
"prediction_reason":[],
"strengths":[],
"weaknesses":[],
"study_plan":[],
"career_suggestions":[
{{"career":"","reason":""}}
],
"motivation":""
}}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=350,
            response_format={
                "type": "json_object"
            }
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        return {
            "performance_level": "Unknown",
            "prediction_reason": [
                "Unable to generate AI explanation."
            ],
            "strengths": [],
            "weaknesses": [
                str(e)
            ],
            "study_plan": [],
            "career_suggestions": [],
            "motivation": "AI guidance unavailable."
        }


def get_goal_suggestions_fallback(prediction, goal):
    suggestions = []
    if not prediction:
        return {
            "suggestions": [
                "Please make your first academic performance prediction to receive tailored guidance.",
                "Define a solid study schedule aligned with your targets."
            ],
            "timeline_advice": "Start tracking your metrics daily to prepare for your target date.",
            "feasibility": "Unknown (No prediction history)"
        }
    
    # Calculate gaps
    score_gap = goal.target_score - prediction.predicted_score
    study_gap = goal.target_study_hours - prediction.study_hours
    attendance_gap = goal.target_attendance - prediction.attendance
    
    if score_gap > 0:
        suggestions.append(f"Your target score is {score_gap:.1f}% higher than your latest predicted score ({prediction.predicted_score}%). Focus on raising your subject marks.")
    else:
        suggestions.append("Outstanding! Your current prediction meets or exceeds your target score.")
        
    if study_gap > 0:
        suggestions.append(f"Increase your daily study hours by {study_gap:.1f} hours to reach your target of {goal.target_study_hours} hours/day.")
    else:
        suggestions.append("Your current daily study hours are already matching or exceeding your target.")
        
    if attendance_gap > 0:
        suggestions.append(f"Improve your class attendance by {attendance_gap:.1f}% to meet your target of {goal.target_attendance}%.")
    else:
        suggestions.append("Your attendance is currently meeting or exceeding your target.")
        
    if prediction.sleep_hours < 7:
        suggestions.append("Ensure you get at least 7-8 hours of sleep. Adequate rest significantly boosts cognitive performance.")
        
    if prediction.internet_usage > 3:
        suggestions.append("Try to limit recreational internet/screen time to free up focus blocks for your study goals.")
        
    # Feasibility
    if score_gap > 20:
        feasibility = "Low (Requires significant, immediate performance gains across all subjects)"
    elif score_gap > 8:
        feasibility = "Medium (Achievable with consistent, increased study discipline and attendance)"
    else:
        feasibility = "High (Highly achievable! Maintain your current habits and slightly raise study hours)"
        
    return {
        "suggestions": suggestions[:4],
        "timeline_advice": f"Review your weekly milestones from now until your target date of {goal.target_date}.",
        "feasibility": feasibility
    }

def get_goal_suggestions(prediction, goal):
    if not prediction:
        return get_goal_suggestions_fallback(prediction, goal)
        
    prompt = f"""
You are an expert academic advisor.

A student has set an academic goal and has a current academic prediction.

Goal Targets:
- Target Final Score: {goal.target_score}%
- Target Study Hours/Day: {goal.target_study_hours}
- Target Attendance: {goal.target_attendance}%
- Target Date: {goal.target_date}

Current Prediction Status:
- Predicted Score: {prediction.predicted_score}%
- Current Study Hours/Day: {prediction.study_hours}
- Current Attendance: {prediction.attendance}%
- Current Sleep Hours/Day: {prediction.sleep_hours}
- Current Internet Usage/Day: {prediction.internet_usage}
- Current Average Subject Score: {prediction.average_subject_score}%

Provide personalized, specific, and actionable guidance to help the student achieve their goal.
Compare their current predicted metrics with their targets and identify what actions they must take.

Return ONLY JSON.

Rules:
- Keep suggestions short, actionable, and concrete.
- Maximum 4 suggestion points.
- Timeline advice: less than 15 words.
- Feasibility: must be one of "High", "Medium", or "Low" (with a short explanation in parentheses).

JSON Format:
{{
  "suggestions": [
    "Increase daily study hours to X by...",
    "Improve attendance to Y by..."
  ],
  "timeline_advice": "Focus on consistent daily improvement over the next Z weeks.",
  "feasibility": "Medium (Achievable if study hours are increased)"
}}
"""
    try:
        if not os.getenv("GROQ_API_KEY"):
            return get_goal_suggestions_fallback(prediction, goal)
            
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=300,
            response_format={
                "type": "json_object"
            }
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return get_goal_suggestions_fallback(prediction, goal)


def get_mentor_response(student_profile, message, chat_history):
    system_prompt = f"""You are a supportive, encouraging, and highly analytical AI Academic Mentor and personal academic coach.
Your student is {student_profile.get('name', 'Student')}.

Here is the student's current academic data, which you MUST use to provide highly personalized guidance:
- Latest Prediction:
  * Predicted Score: {student_profile.get('latest_prediction_score', 'N/A')}%
  * Date of Prediction: {student_profile.get('latest_prediction_date', 'N/A')}
  * Course/Stream: {student_profile.get('stream', 'N/A')}
- Study Habits (from latest prediction):
  * Study Hours/Day: {student_profile.get('study_hours', 'N/A')} hrs
  * Sleep Hours/Day: {student_profile.get('sleep_hours', 'N/A')} hrs
  * Internet Usage/Day: {student_profile.get('internet_usage', 'N/A')} hrs
- Attendance: {student_profile.get('attendance', 'N/A')}%
- Average Marks: {student_profile.get('average_subject_score', 'N/A')}%
- Prediction History: {student_profile.get('prediction_history_summary', 'No prediction history yet.')}
- Goal Tracker Data: {student_profile.get('goals_summary', 'No goals set yet.')}

Rules:
1. Act as a personal academic coach.
2. Refer to the student by their name, {student_profile.get('name', 'Student')}.
3. Always tailor your advice specifically to their performance metrics, habits, and goals. Refer to their actual scores, attendance, study hours, or goals in your response. Avoid generic advice (like "study more"). Instead, provide specific calculations or strategies based on their data.
4. Keep responses clear, concise, and structured. Use Markdown formatting (bullet points, bold text) for readability.
5. If the student has no predictions or goals yet, encourage them to make their first prediction and set a goal so you can provide detailed analysis.
"""
    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        role = "assistant" if msg.get("sender") == "assistant" else "user"
        api_messages.append({"role": role, "content": msg.get("message", "")})
    
    api_messages.append({"role": "user", "content": message})
    
    try:
        if not os.getenv("GROQ_API_KEY"):
            return "Note: GROQ_API_KEY is missing from environment. As your academic mentor, I advise setting up the API key in the `.env` file so I can generate insights!"
            
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=api_messages,
            temperature=0.7,
            max_tokens=600,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"I'm sorry, I encountered an error while processing your request: {str(e)}. Please try again."

# ---------------------------------
# Test
# ---------------------------------
if __name__ == "__main__":
    student = {
        "stream": "Medical",
        "study_hours": 8,
        "attendance": 92,
        "sleep_hours": 7,
        "internet_usage": 2,
        "subjects": [
            {"name": "Anatomy", "score": 85},
            {"name": "Physiology", "score": 90},
            {"name": "Pathology", "score": 75}
        ],
        "previous_score": 82
    }

    result = get_ai_guidance(student, 88)
    print(json.dumps(result, indent=4))