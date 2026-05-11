def calculate_fit_score(
    master,
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
    """
    Temporary scoring logic.
    Later you replace this with the real formula.
    """

    master_text = f"""
    {master.get("program_name", "")}
    {master.get("university_name", "")}
    {master.get("city", "")}
    {master.get("summary", "")}
    """.lower()

    student_text = f"""
    {cv_text}
    {' '.join(field_focus)}
    {language_preference}
    {budget_preference}
    {' '.join(career_goals)}
    {scholarship_need}
    {work_experience}
    {study_mode}
    {additional_notes}
    """.lower()

    score = 0

    for field in field_focus:
        if field.lower() in master_text:
            score += 25

    for goal in career_goals:
        if goal.lower() in master_text:
            score += 20

    if "english" in language_preference.lower() and "english" in master_text:
        score += 15

    if "finance" in student_text and "finance" in master_text:
        score += 15

    if "analytics" in student_text and ("analytics" in master_text or "data" in master_text):
        score += 15

    if "management" in student_text and "management" in master_text:
        score += 15

    if study_mode.lower() in master_text:
        score += 5

    score = min(score, 100)

    return round(score / 100, 2)


def estimate_acceptance_likelihood(fit_score):
    """
    Temporary acceptance likelihood.
    Later this can use GPA, CV strength, requirements, university selectivity, etc.
    """

    if fit_score >= 0.75:
        return "High"
    elif fit_score >= 0.45:
        return "Medium"
    else:
        return "Low"


def build_reason(master, fit_score, likelihood):
    return (
        f"This program seems to be a {likelihood.lower()} compatibility option because "
        f"its description aligns with the student's selected interests and goals. "
        f"The current fit score is {fit_score}."
    )