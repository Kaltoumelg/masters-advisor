from data_loader import load_all_matching_data
from scoring import conservative_filter_masters, rank_masters_with_gemini


def fallback_recommendations(masters):
    results = []

    for master in masters[:3]:
        results.append({
            "program_name": master.get("program_name", "Unknown program"),
            "university": master.get("university", ""),
            "location": master.get("city", ""),
            "fit_score": 0.5,
            "likelihood": "Medium",
            "program_snapshot": "This program may be relevant, but the AI ranking system could not complete the full evaluation.",
            "why_it_matches": "There is some potential overlap with the student's selected preferences, but the match could not be fully evaluated.",
            "what_to_improve": "Review the program requirements carefully and tailor the application to show relevant academic and professional fit.",
            "program_url": master.get("official_url", ""),
        })

    return results


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

    candidate_masters = conservative_filter_masters(
        masters=masters,
        student_profile=student_profile,
    )

    try:
        recommendations = rank_masters_with_gemini(
            student_profile=student_profile,
            masters=candidate_masters,
        )
        return recommendations

    except Exception as e:
        print("Gemini ranking failed:", e)
        return fallback_recommendations(candidate_masters)