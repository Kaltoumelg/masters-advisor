from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "GradMatch AI backend is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import json

from cv_parser import extract_text_from_pdf_bytes
from recommender import generate_recommendations


app = FastAPI(title="GradMatch AI Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # testing only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def parse_list_field(value: str):
    """
    Lovable should send multi-select values as JSON strings.
    Example: '["Finance", "Management"]'

    This function also supports comma-separated text as backup.
    """
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

    field_focus: str = Form(...),
    language_preference: str = Form(...),
    budget_preference: str = Form(...),
    career_goals: str = Form(...),
    scholarship_need: str = Form(...),
    work_experience: str = Form(...),
    study_mode: str = Form(...),

    additional_notes: str = Form(""),
):
    cv_bytes = await cv_file.read()
    cv_text = extract_text_from_pdf_bytes(cv_bytes)

    field_focus_list = parse_list_field(field_focus)
    career_goals_list = parse_list_field(career_goals)

    recommendations = generate_recommendations(
        cv_text=cv_text,
        field_focus=field_focus_list,
        language_preference=language_preference,
        budget_preference=budget_preference,
        career_goals=career_goals_list,
        scholarship_need=scholarship_need,
        work_experience=work_experience,
        study_mode=study_mode,
        additional_notes=additional_notes,
    )

    return {
        "student_inputs_received": {
            "cv_filename": cv_file.filename,
            "field_focus": field_focus_list,
            "language_preference": language_preference,
            "budget_preference": budget_preference,
            "career_goals": career_goals_list,
            "scholarship_need": scholarship_need,
            "work_experience": work_experience,
            "study_mode": study_mode,
            "additional_notes": additional_notes,
        },
        "recommendations": recommendations
    }