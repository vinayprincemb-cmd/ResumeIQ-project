import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
MODEL_NAME = "gemini-2.5-flash"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 3
BUSY_ERROR_MESSAGE = "Gemini servers are currently busy. Please try again in a few moments."
SECTION_DETAILS = [
    {
        "key": "resume_summary",
        "label": "Resume Summary",
        "title": "Role Fit Overview",
        "icon": "i",
        "type": "text",
        "wide": True,
    },
    {
        "key": "strengths",
        "label": "Strengths",
        "title": "What Stands Out",
        "icon": "+",
        "type": "list",
    },
    {
        "key": "missing_skills",
        "label": "Missing Skills",
        "title": "Gaps To Close",
        "icon": "!",
        "type": "list",
    },
    {
        "key": "improvement_suggestions",
        "label": "Improvement Suggestions",
        "title": "Next Resume Edits",
        "icon": ">",
        "type": "list",
    },
    {
        "key": "recommended_projects",
        "label": "Recommended Projects",
        "title": "Portfolio Ideas",
        "icon": "#",
        "type": "list",
    },
]

load_dotenv(ENV_FILE)


def get_gemini_api_key():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError(
            "Gemini API key is missing. Create a .env file in the project root "
            "and add GEMINI_API_KEY=your_actual_api_key."
        )

    return api_key


def extract_text_from_pdf(file_path):
    reader = PdfReader(str(file_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def build_prompt(resume_text, job_role):
    resume_preview = resume_text[:12000]
    prompt_template = """
You are an expert resume reviewer and ATS optimization assistant.

Analyze this resume for the target job role: {job_role}

Return valid JSON only. Do not return plain text, markdown, or code fences.

Use exactly these top-level keys:
{{
  "ats_score": 85,
  "sub_scores": {{
    "skills_match": 82,
    "experience_match": 76,
    "resume_formatting": 90,
    "keyword_optimization": 72
  }},
  "important_keywords": ["Python", "SQL", "Dashboards", "Stakeholder Reporting"],
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "missing_skills": ["skill 1", "skill 2", "skill 3"],
  "improvement_suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"],
  "recommended_projects": ["project 1", "project 2", "project 3"],
  "resume_summary": "short summary of the resume fit for this role"
}}

Rules:
- ats_score must be a number from 0 to 100.
- sub_scores must contain numbers from 0 to 100 for skills_match, experience_match, resume_formatting, and keyword_optimization.
- important_keywords must contain the most important skills, tools, and role keywords found or needed.
- strengths, missing_skills, improvement_suggestions, and recommended_projects must each contain clear beginner-friendly strings.
- resume_summary must be one short paragraph.
- If you cannot find enough information for a list section, return an empty array for that key.
- If you cannot create a resume summary, return an empty string for resume_summary.

Resume text:
{resume_text}
"""

    return prompt_template.format(
        job_role=job_role,
        resume_text=resume_preview,
    )


def clean_json_response(response_text):
    text = response_text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "", 1).replace("```", "", 1).strip()
    elif text.startswith("```"):
        text = text.replace("```", "", 1).replace("```", "", 1).strip()

    return json.loads(text)


def normalize_analysis_result(result):
    # Keep the template simple by making sure common fields have predictable types.
    if not isinstance(result, dict):
        raise ValueError("Gemini returned an invalid response. Please try again.")

    score = result.get("ats_score")

    try:
        score = int(score)
    except (TypeError, ValueError):
        score = None

    result["ats_score"] = None if score is None else max(0, min(score, 100))
    result["sub_scores"] = normalize_sub_scores(result.get("sub_scores", {}))
    result["important_keywords"] = normalize_list(result.get("important_keywords"))

    for key in ["strengths", "missing_skills", "improvement_suggestions", "recommended_projects"]:
        result[key] = normalize_list(result.get(key))

    if not isinstance(result.get("resume_summary"), str):
        result["resume_summary"] = ""

    result["sections"] = build_result_sections(result)

    return result


def normalize_list(value):
    if isinstance(value, str):
        return [value] if value.strip() else []

    if not isinstance(value, list):
        return []

    return [str(item).strip() for item in value if str(item).strip()]


def normalize_sub_scores(sub_scores):
    labels = {
        "skills_match": "Skills Match",
        "experience_match": "Experience Match",
        "resume_formatting": "Resume Formatting",
        "keyword_optimization": "Keyword Optimization",
    }

    if not isinstance(sub_scores, dict):
        sub_scores = {}

    normalized = []

    for key, label in labels.items():
        try:
            score = int(sub_scores.get(key))
        except (TypeError, ValueError):
            score = 0

        normalized.append(
            {
                "key": key,
                "label": label,
                "score": max(0, min(score, 100)),
            }
        )

    return normalized


def build_result_sections(result):
    sections = []

    for section in SECTION_DETAILS:
        key = section["key"]
        value = result.get(key)

        if section["type"] == "text" and value:
            sections.append({**section, "content": value})
        elif section["type"] == "list" and value:
            sections.append({**section, "items": value})

    return sections


def is_overload_error(error):
    error_text = str(error).lower()
    status_code = getattr(error, "status_code", None) or getattr(error, "code", None)

    return str(status_code) == "503" or "503" in error_text or "overloaded" in error_text


def ask_gemini_with_retries(client, prompt):
    for attempt in range(MAX_RETRIES):
        try:
            return client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
        except Exception as exc:
            is_last_attempt = attempt == MAX_RETRIES - 1

            if is_overload_error(exc) and not is_last_attempt:
                time.sleep(RETRY_DELAY_SECONDS)
                continue

            if is_overload_error(exc):
                raise ValueError(BUSY_ERROR_MESSAGE) from exc

            raise


def analyze_resume(file_path, job_role):
    api_key = get_gemini_api_key()
    resume_text = extract_text_from_pdf(Path(file_path))

    if not resume_text:
        raise ValueError("Could not read text from this PDF. Try a text-based resume PDF.")

    client = genai.Client(api_key=api_key)
    prompt = build_prompt(resume_text, job_role)
    response = ask_gemini_with_retries(client, prompt)

    if not response.text:
        raise ValueError("Gemini did not return any analysis. Please try again.")

    try:
        result = clean_json_response(response.text)
        return normalize_analysis_result(result)
    except json.JSONDecodeError as exc:
        raise ValueError("Gemini returned invalid JSON. Please try again.") from exc
