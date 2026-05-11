def normalize_gpa(gpa, gpa_scale):
    try:
        value = float(str(gpa).replace(",", "."))
    except Exception:
        return None

    scale = str(gpa_scale).lower()

    if "20" in scale:
        return max(0, min(value / 20, 1))

    if "4" in scale:
        return max(0, min(value / 4, 1))

    if "100" in scale:
        return max(0, min(value / 100, 1))

    return None


def calculate_fit_score(
    master,
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
    master_text = f"""
    {master.get("program_name", "")}
    {master.get("university_name", "")}
    {master.get("city", "")}
    {master.get("summary", "")}
    {master.get("official_url", "")}
    """.lower()

    score = 0

    for field in field_focus:
        if field.lower() in master_text:
            score += 18

    for goal in career_goals:
        if goal.lower() in master_text:
            score += 14

    for experience in student_experience:
        if experience.lower() in master_text:
            score += 8

    for preference in program_preferences:
        if preference.lower() in master_text:
            score += 8

    if "english" in language_preference.lower() and "english" in master_text:
        score += 10
    elif "either" in language_preference.lower():
        score += 5
    elif "portuguese" in language_preference.lower() and ("portuguese" in master_text or "português" in master_text):
        score += 10

    if "no strict limit" in budget_preference.lower():
        score += 5
    elif any(word in master_text for word in ["tuition", "fees", "propina", "scholarship", "funding"]):
        score += 5

    cv_lower = cv_text.lower()
    for field in field_focus:
        if field.lower() in cv_lower:
            score += 5

    gpa_normalized = normalize_gpa(gpa, gpa_scale)
    if gpa_normalized is not None:
        if gpa_normalized >= 0.8:
            score += 8
        elif gpa_normalized >= 0.7:
            score += 5
        elif gpa_normalized >= 0.6:
            score += 2

    return round(min(score, 100) / 100, 2)


def estimate_acceptance_likelihood(fit_score, gpa, gpa_scale, cv_text):
    gpa_normalized = normalize_gpa(gpa, gpa_scale)

    profile_boost = 0

    cv_lower = cv_text.lower()

    if any(word in cv_lower for word in ["internship", "estágio", "analyst", "consultant", "research assistant"]):
        profile_boost += 0.08

    if any(word in cv_lower for word in ["leadership", "president", "coordinator", "volunteer", "volunteering"]):
        profile_boost += 0.05

    if gpa_normalized is not None:
        if gpa_normalized >= 0.8:
            profile_boost += 0.1
        elif gpa_normalized < 0.6:
            profile_boost -= 0.1

    competitiveness_score = fit_score + profile_boost

    if competitiveness_score >= 0.8:
        return "Safety"

    if competitiveness_score >= 0.55:
        return "Target"

    return "Reach"