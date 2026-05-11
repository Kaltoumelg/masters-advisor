from data_loader import load_all_matching_data
from scoring import score_master_with_ai


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

    results = []

    for master in masters:
        ai_score = score_master_with_ai(master, student_profile)

        results.append({
            "program_name": master.get("program_name", "Unknown program"),
            "university": f"University ID {master.get('university_id', '')}",
            "location": master.get("city", ""),
            "fit_score": round(ai_score["fit_score"] / 100, 2),
            "acceptance_likelihood": ai_score["acceptance_likelihood"],
            "why_it_matches": ai_score["why_it_matches"],
            "what_to_improve": ai_score["what_to_improve"],
            "summary": master.get("program_summary", ""),
            "program_url": master.get("official_url", ""),
        })

    results = sorted(results, key=lambda x: x["fit_score"], reverse=True)

    return results[:5]