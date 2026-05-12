from data_loader import load_all_matching_data
from scoring import evaluate_master_with_gemini


def generate_recommendations(
    cv_text,
    gpa,
    gpa_scale,
    field_focus,
    career_goals,
    student_experience,
    language_preference,
    budget_preference,
    program_preferences,
    additional_notes,
):
    masters = load_all_matching_data()

    student_profile = {
        "cv_text": cv_text,
        "gpa": gpa,
        "gpa_scale": gpa_scale,
        "field_focus": field_focus,
        "career_goals": career_goals,
        "student_experience": student_experience,
        "language_preference": language_preference,
        "budget_preference": budget_preference,
        "program_preferences": program_preferences,
        "additional_notes": additional_notes,
    }

    evaluated = []

    for master in masters:
        try:
            result = evaluate_master_with_gemini(master, student_profile)
            evaluated.append(result)
        except Exception as e:
            print(f"Gemini failed for {master.get('program_name')}: {e}")

    evaluated = sorted(
        evaluated,
        key=lambda item: item.get("fit_score", 0),
        reverse=True,
    )

    return evaluated[:3]