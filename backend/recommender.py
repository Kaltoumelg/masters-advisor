from data_loader import load_masters_from_database
from scoring import calculate_fit_score, estimate_acceptance_likelihood


def build_why_it_matches(master, fit_score, field_focus, career_goals, student_experience):
    selected_fields = ", ".join(field_focus) if field_focus else "your selected fields"
    selected_goals = ", ".join(career_goals) if career_goals else "your career goals"
    selected_experience = ", ".join(student_experience) if student_experience else "your preferred student experience"

    program_name = master.get("program_name", "this program")

    return (
        f"{program_name} appears aligned with your interest in {selected_fields}, "
        f"your career goals in {selected_goals}, and your preference for {selected_experience}. "
        f"The current fit score is {round(fit_score * 100)}%."
    )


def build_what_to_improve(fit_score, acceptance_likelihood):
    if acceptance_likelihood == "Safety":
        return (
            "Your profile appears relatively strong for this option. To strengthen your application further, "
            "focus on a clear motivation letter and showing specific interest in the program."
        )

    if acceptance_likelihood == "Target":
        return (
            "This looks like a realistic but competitive option. You could improve your chances by strengthening "
            "your CV with relevant internships, quantitative coursework, leadership activities, or a strong motivation letter."
        )

    return (
        "This may be a more ambitious option. To improve your likelihood, consider gaining more relevant experience, "
        "improving your GPA or academic evidence, strengthening language/certification proof, and tailoring your application carefully."
    )


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
    masters = load_masters_from_database()

    results = []

    for master in masters:
        fit_score = calculate_fit_score(
            master=master,
            cv_text=cv_text,
            gpa=gpa,
            gpa_scale=gpa_scale,
            field_focus=field_focus,
            career_goals=career_goals,
            student_experience=student_experience,
            language_preference=language_preference,
            budget_preference=budget_preference,
            program_preferences=program_preferences,
            additional_notes=additional_notes,
        )

        acceptance_likelihood = estimate_acceptance_likelihood(
            fit_score=fit_score,
            gpa=gpa,
            gpa_scale=gpa_scale,
            cv_text=cv_text,
        )

        results.append({
            "program_name": master.get("program_name", "Unknown program"),
            "university": master.get("university_name", "Unknown university"),
            "location": master.get("city", ""),
            "fit_score": fit_score,
            "acceptance_likelihood": acceptance_likelihood,
            "why_it_matches": build_why_it_matches(
                master=master,
                fit_score=fit_score,
                field_focus=field_focus,
                career_goals=career_goals,
                student_experience=student_experience,
            ),
            "what_to_improve": build_what_to_improve(
                fit_score=fit_score,
                acceptance_likelihood=acceptance_likelihood,
            ),
            "summary": master.get("summary", ""),
            "program_url": master.get("official_url", ""),
        })

    results = sorted(results, key=lambda x: x["fit_score"], reverse=True)

    return results[:5]