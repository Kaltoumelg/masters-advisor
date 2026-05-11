from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import json

from cv_parser import extract_text_from_pdf_bytes
from recommender import generate_recommendations


app = FastAPI(title="GradMatch AI Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def parse_list_field(value: str):
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
        return [str(parsed)]
    except Exception:
        return [item.strip() for item in value.split(",") if item.strip()]


@app.get("/")
def home():
    return {"message": "GradMatch AI backend is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/recommend")
async def recommend(
    cv_file: UploadFile = File(...),

    gpa: str = Form(...),
    gpa_scale: str = Form(...),

    field_focus: str = Form(...),
    career_goals: str = Form(...),
    student_experience: str = Form(...),

    language_preference: str = Form(...),
    budget_preference: str = Form(...),
    program_preferences: str = Form(...),

    additional_notes: str = Form(""),
):
    cv_bytes = await cv_file.read()
    cv_text = extract_text_from_pdf_bytes(cv_bytes)

    field_focus_list = parse_list_field(field_focus)
    career_goals_list = parse_list_field(career_goals)
    student_experience_list = parse_list_field(student_experience)
    program_preferences_list = parse_list_field(program_preferences)

    recommendations = generate_recommendations(
        cv_text=cv_text,
        gpa=gpa,
        gpa_scale=gpa_scale,
        field_focus=field_focus_list,
        career_goals=career_goals_list,
        student_experience=student_experience_list,
        language_preference=language_preference,
        budget_preference=budget_preference,
        program_preferences=program_preferences_list,
        additional_notes=additional_notes,
    )

    return {
        "student_inputs_received": {
            "cv_filename": cv_file.filename,
            "gpa": gpa,
            "gpa_scale": gpa_scale,
            "field_focus": field_focus_list,
            "career_goals": career_goals_list,
            "student_experience": student_experience_list,
            "language_preference": language_preference,
            "budget_preference": budget_preference,
            "program_preferences": program_preferences_list,
            "additional_notes": additional_notes,
        },
        "recommendations": recommendations,
    }