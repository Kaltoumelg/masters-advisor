from data_loader import load_masters_from_database
from scoring import calculate_fit_score, estimate_acceptance_likelihood, build_reason


def generate_recommendations(
    cv_text,
    field_focus,
    language_preference,
    budget_preference,
    career_goals,
    scholarship_need,
    work_experience,
    study_mode,
    additional_notes,
):
    masters = load_masters_from_database()

    results = []

    for master in masters:
        fit_score = calculate_fit_score(
            master=master,
            cv_text=cv_text,
            field_focus=field_focus,
            language_preference=language_preference,
            budget_preference=budget_preference,
            career_goals=career_goals,
            scholarship_need=scholarship_need,
            work_experience=work_experience,
            study_mode=study_mode,
            additional_notes=additional_notes,
        )

        likelihood = estimate_acceptance_likelihood(fit_score)

        results.append({
            "program_name": master.get("program_name", "Unknown program"),
            "university": master.get("university_name", "Unknown university"),
            "location": master.get("city", ""),
            "fit_score": fit_score,
            "acceptance_likelihood": likelihood,
            "recommendation_text": build_reason(master, fit_score, likelihood),
            "summary": master.get("summary", ""),
            "program_url": master.get("official_url", ""),
        })

    results = sorted(results, key=lambda x: x["fit_score"], reverse=True)

    return results[:5]