import json
import logging
import os
import random
import sys
import time
import traceback
from pathlib import Path

LOGGER = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
except ModuleNotFoundError as exc:
    load_dotenv = None
    DOTENV_IMPORT_ERROR = exc
else:
    DOTENV_IMPORT_ERROR = None

try:
    from google.genai import Client, types
except (ImportError, ModuleNotFoundError) as exc:
    Client = None
    types = None
    GENAI_IMPORT_ERROR = exc
    GENAI_IMPORT_TRACEBACK = traceback.format_exc()
else:
    GENAI_IMPORT_ERROR = None
    GENAI_IMPORT_TRACEBACK = ""

try:
    from pypdf import PdfReader
except (ImportError, ModuleNotFoundError) as exc:
    PdfReader = None
    PDF_IMPORT_ERROR = exc
else:
    PDF_IMPORT_ERROR = None


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
MODEL_NAME = "gemini-2.5-flash"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 3
BUSY_ERROR_MESSAGE = "Gemini servers are currently busy. Please try again in a few moments."
GEMINI_QUOTA_MESSAGE = (
    "AI evaluation is temporarily unavailable because the Gemini API usage limit has been reached. "
    "Your interview has been saved and can be evaluated later."
)
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
RESUME_ROLE_KEYWORDS = {
    "python": ["Python", "Flask", "Django", "REST API", "SQL", "testing", "Git"],
    "data analyst": ["SQL", "Excel", "Power BI", "Tableau", "Python", "statistics", "dashboards"],
    "data scientist": ["Python", "machine learning", "statistics", "pandas", "scikit-learn", "SQL", "modeling"],
    "ai engineer": ["Python", "LLM", "machine learning", "vector database", "API", "evaluation", "MLOps"],
    "frontend": ["JavaScript", "HTML", "CSS", "React", "responsive design", "accessibility", "Git"],
    "full stack": ["JavaScript", "Python", "Flask", "React", "SQL", "REST API", "deployment"],
    "software": ["data structures", "algorithms", "system design", "testing", "Git", "API", "databases"],
    "cloud": ["AWS", "Azure", "Docker", "Kubernetes", "CI/CD", "Linux", "monitoring"],
    "cybersecurity": ["network security", "OWASP", "SIEM", "Linux", "incident response", "risk", "controls"],
}

if load_dotenv and ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=False)


def get_gemini_api_key():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError(
            "Gemini API key is missing. Add GEMINI_API_KEY to your .env file locally "
            "or set it as an environment variable on Render."
        )

    return api_key


def extract_text_from_pdf(file_path):
    if PdfReader is None:
        LOGGER.exception("pypdf import failed: %s", PDF_IMPORT_ERROR)
        raise ValueError(
            "PDF reader dependency is not available. Run pip install -r requirements.txt "
            "and use Python 3.9 or newer."
        )

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


def build_builder_prompt(action, section, content, target_role):
    return f"""
You are an expert resume writer and ATS optimization assistant.

Return valid JSON only. Do not return markdown or code fences.
Use exactly this schema:
{{
  "content": "improved resume-ready content",
  "suggestions": ["short suggestion 1", "short suggestion 2", "short suggestion 3"]
}}

Task: {action}
Resume section: {section}
Target role: {target_role or "General professional role"}

Rules:
- Keep the content truthful and based on the supplied draft.
- If the draft is sparse, create polished but generic wording the user can edit.
- Use concise ATS-friendly language and strong action verbs.
- For bullet point improvement, return bullet-ready lines separated by newlines.
- Do not invent employer names, degrees, certifications, or metrics unless clearly marked as placeholders.

Draft content:
{content[:6000]}
"""


def build_interview_questions_prompt(setup):
    question_count = max(1, min(int(setup.get("question_count") or 5), 20))
    return f"""
You are an expert AI interview coach.

Return valid JSON only. Do not return markdown or code fences.
Use exactly this schema:
{{
  "questions": [
    {{
      "id": 1,
      "question_number": 1,
      "question": "interview question",
      "difficulty": "Medium",
      "type": "Technical",
      "expected_skills": ["Python", "Problem solving"],
      "competency": "Technical depth",
      "intent": "what this question evaluates"
    }}
  ]
}}

Create {question_count} interview questions.
Job role: {setup.get("job_role") or "General professional role"}
Experience level: {setup.get("experience_level") or "Entry"}
Difficulty: {setup.get("difficulty") or "Medium"}
Interview type: {setup.get("interview_type") or "Mixed"}
Custom focus: {setup.get("custom_focus") or "Use a balanced role-relevant interview."}

Rules:
- Questions must be practical, job-relevant, and distinct.
- Include question_number, difficulty, type, and expected_skills for every question.
- For Technical, include role-specific problem-solving questions.
- For HR and Behavioral, include communication, ownership, and judgment prompts.
- For Mixed, blend technical, behavioral, and role-fit questions.
"""


def build_interview_evaluation_prompt(setup, answers):
    return f"""
You are an expert hiring interviewer and communication coach.

Return valid JSON only. Do not return markdown or code fences.
Use exactly this schema:
{{
  "scores": {{
    "technical_score": 80,
    "communication_score": 80,
    "confidence_score": 80,
    "grammar_score": 80,
    "vocabulary_score": 80,
    "problem_solving_score": 80,
    "role_readiness_score": 80,
    "overall_percentage": 80,
    "overall_score": 80
  }},
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "performance_summary": "short summary",
  "hiring_recommendation": "Strong hire / Hire / Lean hire / Needs more preparation",
  "detailed_feedback": "specific overall coaching feedback",
  "suggested_better_answers": ["better answer 1", "better answer 2"],
  "section_wise_feedback": ["technical feedback", "communication feedback", "problem solving feedback"],
  "improved_sample_answers": ["improved answer 1", "improved answer 2"],
  "improvement_plan": ["next step 1", "next step 2"],
  "learning_resources": ["resource 1", "resource 2"],
  "suggested_courses": ["course 1", "course 2"],
  "roadmap": ["week 1 focus", "week 2 focus"],
  "answers": [
    {{
      "question": "question text",
    "answer": "candidate answer",
    "score": 80,
      "technical_score": 80,
      "communication_score": 80,
      "confidence_score": 80,
      "grammar_score": 80,
      "vocabulary_score": 80,
      "problem_solving_score": 80,
      "better_answer": "stronger sample answer",
      "improvement_tips": ["tip 1", "tip 2"]
    }}
  ]
}}

Interview setup:
{json.dumps(setup, ensure_ascii=False)}

Questions and answers:
{json.dumps(answers, ensure_ascii=False)[:12000]}

Rules:
- All scores must be integers from 0 to 100.
- Evaluate honestly but constructively.
- Better answers should be concise and specific.
- Improvement tips must be actionable.
"""


def build_answer_evaluation_prompt(setup, question, answer):
    return f"""
You are an expert interview coach evaluating one answer immediately after it is given.

Return valid JSON only. Do not return markdown or code fences.
Use exactly this schema:
{{
  "technical_score": 80,
  "communication_score": 80,
  "confidence_score": 80,
  "grammar_score": 80,
  "problem_solving_score": 80,
  "overall_score": 80,
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "better_sample_answer": "concise stronger sample answer",
  "improvement_suggestions": ["suggestion 1", "suggestion 2"]
}}

Interview setup:
{json.dumps(setup, ensure_ascii=False)}

Question:
{json.dumps(question, ensure_ascii=False)}

Candidate answer:
{str(answer or "")[:6000]}

Rules:
- All scores must be integers from 0 to 100.
- Be constructive, specific, and role-relevant.
- If the answer is empty or skipped, score it low and explain what should be covered.
"""


def clean_json_response(response_text):
    text = response_text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "", 1).replace("```", "", 1).strip()
    elif text.startswith("```"):
        text = text.replace("```", "", 1).replace("```", "", 1).strip()

    return json.loads(text)


def build_aptitude_questions_prompt(setup):
    question_count = max(1, min(int(setup.get("question_count") or 10), 30))
    category = setup.get("category") or "Mixed"
    difficulty = setup.get("difficulty") or "Medium"
    return f"""
You are an expert aptitude test creator.

Return valid JSON only. Do not return markdown or code fences.
Use exactly this schema:
{{
  "questions": [
    {{
      "question_number": 1,
      "category": "{category}",
      "question": "multiple choice question",
      "options": {{"A": "option A", "B": "option B", "C": "option C", "D": "option D"}},
      "correct_answer": "A",
      "explanation": "short explanation",
      "difficulty": "{difficulty}",
      "time_limit": 60
    }}
  ]
}}

Create {question_count} multiple choice aptitude questions.
Category: {category}
Difficulty: {difficulty}

Rules:
- Categories may include Quantitative Aptitude, Logical Reasoning, Verbal Ability, Data Interpretation, or Mixed.
- Every question must have four options A through D.
- correct_answer must be one of A, B, C, or D.
- Keep explanations concise and useful.
"""


def normalize_builder_response(result):
    if not isinstance(result, dict):
        raise ValueError("Gemini returned an invalid builder response. Please try again.")

    content = result.get("content")
    suggestions = result.get("suggestions")

    return {
        "content": str(content or "").strip(),
        "suggestions": normalize_list(suggestions)[:5],
    }


def normalize_score(value):
    try:
        score = int(value)
    except (TypeError, ValueError):
        score = 0
    return max(0, min(score, 100))


def normalize_interview_questions(result):
    if not isinstance(result, dict):
        raise ValueError("Gemini returned an invalid interview response. Please try again.")

    questions = result.get("questions")
    if not isinstance(questions, list):
        questions = []

    normalized = []
    for index, item in enumerate(questions, start=1):
        if not isinstance(item, dict):
            continue
        question = str(item.get("question") or "").strip()
        if not question:
            continue
        normalized.append(
            {
                "id": index,
                "question_number": int(item.get("question_number") or index),
                "question": question,
                "difficulty": str(item.get("difficulty") or "Medium").strip(),
                "type": str(item.get("type") or item.get("competency") or "Mixed").strip(),
                "expected_skills": normalize_list(item.get("expected_skills"))[:6],
                "competency": str(item.get("competency") or "Role fit").strip(),
                "intent": str(item.get("intent") or "Evaluate interview readiness.").strip(),
            }
        )

    if not normalized:
        raise ValueError("Gemini did not return interview questions. Please try again.")

    return normalized


def normalize_interview_report(result, setup, answers):
    if not isinstance(result, dict):
        raise ValueError("Gemini returned an invalid interview report. Please try again.")

    raw_scores = result.get("scores") if isinstance(result.get("scores"), dict) else {}
    score_keys = [
        "technical_score",
        "communication_score",
        "confidence_score",
        "grammar_score",
        "vocabulary_score",
        "problem_solving_score",
    "role_readiness_score",
    "overall_percentage",
    "overall_score",
    ]
    scores = {key: normalize_score(raw_scores.get(key)) for key in score_keys}
    if not scores["overall_score"]:
        scores["overall_score"] = round(sum(scores[key] for key in [
            "technical_score",
            "communication_score",
            "confidence_score",
            "grammar_score",
            "vocabulary_score",
            "problem_solving_score",
        ]) / 6)
    if not scores["overall_percentage"]:
        scores["overall_percentage"] = scores["overall_score"]
    if not scores["role_readiness_score"]:
        scores["role_readiness_score"] = scores["overall_score"]

    answer_rows = []
    raw_answers = result.get("answers") if isinstance(result.get("answers"), list) else []
    for index, answer in enumerate(answers):
        evaluated = raw_answers[index] if index < len(raw_answers) and isinstance(raw_answers[index], dict) else {}
        live_evaluation = answer.get("evaluation") if isinstance(answer.get("evaluation"), dict) else {}
        answer_rows.append(
            {
                "question": str(answer.get("question") or evaluated.get("question") or "").strip(),
                "answer": str(answer.get("answer") or "").strip(),
                "score": normalize_score(evaluated.get("score") or live_evaluation.get("overall_score")),
                "technical_score": normalize_score(evaluated.get("technical_score") or live_evaluation.get("technical_score")),
                "communication_score": normalize_score(evaluated.get("communication_score") or live_evaluation.get("communication_score")),
                "confidence_score": normalize_score(evaluated.get("confidence_score") or live_evaluation.get("confidence_score")),
                "grammar_score": normalize_score(evaluated.get("grammar_score") or live_evaluation.get("grammar_score")),
                "vocabulary_score": normalize_score(evaluated.get("vocabulary_score") or live_evaluation.get("vocabulary_score")),
                "problem_solving_score": normalize_score(evaluated.get("problem_solving_score") or live_evaluation.get("problem_solving_score")),
                "better_answer": str(evaluated.get("better_answer") or live_evaluation.get("better_sample_answer") or "").strip(),
                "improvement_tips": (normalize_list(evaluated.get("improvement_tips")) or normalize_list(live_evaluation.get("improvement_suggestions")))[:4],
            }
        )

    return {
        "setup": setup,
        "scores": scores,
        "strengths": normalize_list(result.get("strengths"))[:6],
        "weaknesses": normalize_list(result.get("weaknesses"))[:6],
        "performance_summary": str(result.get("performance_summary") or "").strip(),
        "hiring_recommendation": str(result.get("hiring_recommendation") or "Needs more preparation").strip(),
        "detailed_feedback": str(result.get("detailed_feedback") or "").strip(),
        "suggested_better_answers": normalize_list(result.get("suggested_better_answers"))[:6],
        "section_wise_feedback": normalize_list(result.get("section_wise_feedback"))[:8],
        "improved_sample_answers": normalize_list(result.get("improved_sample_answers"))[:8],
        "improvement_plan": normalize_list(result.get("improvement_plan"))[:6],
        "learning_resources": normalize_list(result.get("learning_resources"))[:6],
        "suggested_courses": normalize_list(result.get("suggested_courses") or result.get("learning_resources"))[:6],
        "roadmap": normalize_list(result.get("roadmap"))[:8],
        "answers": answer_rows,
        "evaluation_type": "AI Evaluation",
    }


def normalize_aptitude_questions(result):
    if not isinstance(result, dict):
        raise ValueError("Gemini returned an invalid aptitude response. Please try again.")

    questions = result.get("questions") if isinstance(result.get("questions"), list) else []
    normalized = []
    for index, item in enumerate(questions, start=1):
        if not isinstance(item, dict):
            continue
        options = item.get("options") if isinstance(item.get("options"), dict) else {}
        question = str(item.get("question") or "").strip()
        correct = str(item.get("correct_answer") or "").strip().upper()[:1]
        if not question or correct not in {"A", "B", "C", "D"}:
            continue
        normalized.append(
            {
                "question_number": int(item.get("question_number") or index),
                "category": str(item.get("category") or "Mixed").strip(),
                "question": question,
                "options": {letter: str(options.get(letter) or "").strip() for letter in ["A", "B", "C", "D"]},
                "correct_answer": correct,
                "explanation": str(item.get("explanation") or "").strip(),
                "difficulty": str(item.get("difficulty") or "Medium").strip(),
                "time_limit": max(15, min(int(item.get("time_limit") or 60), 300)),
            }
        )

    if not normalized:
        raise ValueError("Gemini did not return aptitude questions. Please try again.")
    return normalized


def locally_evaluate_interview(setup, answers, message=""):
    answered = [item for item in answers if str(item.get("answer") or "").strip()]
    total = max(1, len(answers))
    completion = len(answered) / total
    word_counts = [len(str(item.get("answer") or "").split()) for item in answered]
    avg_words = sum(word_counts) / max(1, len(word_counts))
    substance = min(1, avg_words / 80)
    structure_hits = sum(
        1
        for item in answered
        if any(token in str(item.get("answer") or "").lower() for token in ["result", "because", "example", "implemented", "improved", "measured"])
    )
    structure = structure_hits / max(1, len(answered))
    base = round((completion * 35) + (substance * 35) + (structure * 30))
    communication = min(100, round(base + 6 if avg_words >= 45 else base))
    grammar = min(100, max(35, round(base + 4)))
    confidence = min(100, max(30, round((completion * 50) + (substance * 50))))
    technical = min(100, max(25, round((substance * 45) + (structure * 35) + (completion * 20))))
    problem = min(100, max(25, round((structure * 50) + (substance * 30) + (completion * 20))))
    overall = round((technical + communication + grammar + confidence + problem) / 5)
    scores = {
        "technical_score": technical,
        "communication_score": communication,
        "grammar_score": grammar,
        "vocabulary_score": min(100, max(30, round(base + 2))),
        "confidence_score": confidence,
        "problem_solving_score": problem,
        "role_readiness_score": overall,
        "overall_percentage": overall,
        "overall_score": overall,
    }
    answer_rows = []
    for item in answers:
        answer = str(item.get("answer") or "").strip()
        answer_score = 0 if not answer else min(100, max(35, round((len(answer.split()) / 80) * 55 + 35)))
        answer_rows.append(
            {
                "question": str(item.get("question") or "").strip(),
                "answer": answer,
                "score": answer_score,
                "technical_score": answer_score,
                "communication_score": min(100, answer_score + 4),
                "grammar_score": min(100, answer_score + 3),
                "vocabulary_score": min(100, answer_score + 2),
                "confidence_score": min(100, answer_score + 1),
                "problem_solving_score": answer_score,
                "better_answer": "Use a concise structure: context, action, result, and the specific skills or tools you used.",
                "improvement_tips": ["Add measurable results.", "Name the tools or concepts used.", "Close with the impact of your work."],
            }
        )
    return {
        "setup": setup,
        "scores": scores,
        "strengths": ["Completed answers were saved.", "Response structure can be improved with examples."],
        "weaknesses": ["Some answers may need more measurable detail.", "AI-level semantic feedback is pending."],
        "performance_summary": message or "Offline Evaluation generated from answer completeness, length, clarity signals, and structure.",
        "hiring_recommendation": "Needs more preparation" if overall < 70 else "Lean hire",
        "detailed_feedback": "Offline Evaluation: this rule-based score is immediate and approximate. Generate AI Evaluation later for deeper feedback.",
        "suggested_better_answers": ["Use STAR or problem-action-result framing for each answer."],
        "section_wise_feedback": ["Technical depth depends on specific examples.", "Communication improves when answers include context, action, and result."],
        "improved_sample_answers": ["A stronger answer briefly defines the situation, explains your specific action, and closes with measurable impact."],
        "improvement_plan": ["Add one concrete example per answer.", "Quantify outcomes where possible.", "Practice shorter, structured responses."],
        "learning_resources": ["Review STAR interview method.", "Practice role-specific fundamentals.", "Record and review answers for clarity."],
        "suggested_courses": ["Interview communication fundamentals", "Role-specific technical interview practice", "Business English for professional interviews"],
        "roadmap": ["Review role fundamentals.", "Practice five structured answers.", "Repeat a timed mock interview and compare scores."],
        "answers": answer_rows,
        "evaluation_type": "Offline Evaluation",
        "ai_error": message,
    }


OFFLINE_ROLES = [
    "Python", "Java", "C", "C++", "JavaScript", "SQL", "Data Analyst", "AI Engineer",
    "Software Engineer", "Full Stack Developer", "Data Science", "Cybersecurity", "Cloud",
]
TECHNICAL_TOPICS = [
    "data structures", "algorithms", "debugging", "testing", "API design", "databases",
    "security", "performance", "deployment", "system design", "error handling", "version control",
    "object-oriented design", "concurrency", "scalability", "clean code", "logging", "caching",
    "authentication", "data modeling", "frontend state", "backend services", "cloud monitoring",
    "automation", "analytics", "machine learning", "ETL", "SQL optimization", "networking", "Linux",
]
TECHNICAL_TEMPLATES = [
    "Explain how you would apply {topic} in a {role} project.",
    "Walk through a production issue involving {topic} and how you would debug it.",
    "What tradeoffs would you consider when using {topic} for a {role} system?",
    "Describe a practical example where {topic} improves reliability or maintainability.",
    "How would you test a {role} feature that depends on {topic}?",
]
HR_TEMPLATES = [
    "Tell me about yourself for a {role} position.",
    "Why are you interested in this {role} role?",
    "What are your strengths as a {role} candidate?",
    "What is one area you are actively improving?",
    "How do you handle feedback from a manager or teammate?",
    "Why should we hire you for this role?",
    "Describe your preferred work environment.",
    "How do you prioritize when several tasks are urgent?",
    "What motivates you to keep learning?",
    "Where do you see your career moving next?",
]
BEHAVIORAL_TEMPLATES = [
    "Describe a time you solved a difficult problem related to {topic}.",
    "Tell me about a time you disagreed with a teammate and how you handled it.",
    "Give an example of taking ownership when a project was at risk.",
    "Describe a time you had to learn something quickly.",
    "Tell me about a time you improved a process or workflow.",
    "Share an example of communicating technical work to a non-technical person.",
    "Describe a time you made a mistake and what you changed afterward.",
    "Tell me about a project where requirements were unclear.",
    "Give an example of working under a tight deadline.",
    "Describe a time you helped another person succeed.",
]
APTITUDE_CATEGORIES = ["Quantitative", "Logical", "Verbal", "Reasoning", "Mixed"]


def build_offline_question_bank():
    technical = []
    for role in OFFLINE_ROLES:
        for topic in TECHNICAL_TOPICS:
            for template in TECHNICAL_TEMPLATES:
                technical.append(
                    {
                        "question": template.format(role=role, topic=topic),
                        "type": "Technical",
                        "difficulty": "Medium",
                        "expected_skills": [role, topic],
                        "competency": "Technical depth",
                    }
                )
    hr = [
        {
            "question": template.format(role=role),
            "type": "HR",
            "difficulty": "Medium",
            "expected_skills": ["self-awareness", "communication"],
            "competency": "Professional fit",
        }
        for role in OFFLINE_ROLES
        for template in HR_TEMPLATES
        for _index in range(2)
    ]
    behavioral = [
        {
            "question": template.format(topic=topic),
            "type": "Behavioral",
            "difficulty": "Medium",
            "expected_skills": ["ownership", "communication", topic],
            "competency": "Behavioral judgment",
        }
        for topic in TECHNICAL_TOPICS
        for template in BEHAVIORAL_TEMPLATES
    ]
    aptitude = []
    for category in APTITUDE_CATEGORIES:
        for index in range(1, 61):
            base = index + 7
            correct = (base * 2) if category in {"Quantitative", "Mixed"} else base
            aptitude.append(
                {
                    "question_number": index,
                    "category": category,
                    "question": f"{category}: choose the best answer for practice item {index}.",
                    "options": {
                        "A": str(correct - 2),
                        "B": str(correct),
                        "C": str(correct + 3),
                        "D": str(correct + 5),
                    },
                    "correct_answer": "B",
                    "explanation": "Option B follows the intended pattern for this offline practice item.",
                    "difficulty": "Medium",
                    "time_limit": 60,
                }
            )
    return {"technical": technical, "hr": hr, "behavioral": behavioral, "aptitude": aptitude}


OFFLINE_QUESTION_BANK = build_offline_question_bank()


def generate_offline_interview_questions(setup):
    interview_type = str(setup.get("interview_type") or "Mixed").lower()
    difficulty = str(setup.get("difficulty") or "Medium").strip() or "Medium"
    role = str(setup.get("job_role") or "Software Engineer").strip()
    question_count = max(1, min(int(setup.get("question_count") or 5), 20))
    pools = []
    if "technical" in interview_type:
        pools.extend(OFFLINE_QUESTION_BANK["technical"])
    elif "hr" in interview_type:
        pools.extend(OFFLINE_QUESTION_BANK["hr"])
    elif "behavioral" in interview_type:
        pools.extend(OFFLINE_QUESTION_BANK["behavioral"])
    else:
        pools.extend(OFFLINE_QUESTION_BANK["technical"])
        pools.extend(OFFLINE_QUESTION_BANK["hr"])
        pools.extend(OFFLINE_QUESTION_BANK["behavioral"])
    role_matches = [item for item in pools if role.lower() in item["question"].lower() or role.lower() in " ".join(item.get("expected_skills", [])).lower()]
    candidates = role_matches or pools
    random.shuffle(candidates)
    selected = candidates[:question_count]
    return [
        {
            "id": index,
            "question_number": index,
            "question": item["question"],
            "difficulty": difficulty,
            "type": item["type"],
            "expected_skills": item.get("expected_skills", [])[:6],
            "competency": item.get("competency") or item["type"],
            "intent": "Offline question bank prompt generated without Gemini.",
            "offline": True,
        }
        for index, item in enumerate(selected, start=1)
    ]


def generate_offline_aptitude_questions(setup):
    category = str(setup.get("category") or "Mixed").strip()
    difficulty = str(setup.get("difficulty") or "Medium").strip()
    question_count = max(1, min(int(setup.get("question_count") or 10), 30))
    pool = [item for item in OFFLINE_QUESTION_BANK["aptitude"] if item["category"].lower() == category.lower()]
    if not pool or category.lower() == "mixed":
        pool = OFFLINE_QUESTION_BANK["aptitude"][:]
    random.shuffle(pool)
    selected = pool[:question_count]
    return [{**item, "question_number": index, "difficulty": difficulty} for index, item in enumerate(selected, start=1)]


def normalize_answer_evaluation(result):
    if not isinstance(result, dict):
        raise ValueError("Gemini returned an invalid answer evaluation. Please try again.")

    score_keys = [
        "technical_score",
        "communication_score",
        "confidence_score",
        "grammar_score",
        "problem_solving_score",
        "overall_score",
    ]
    scores = {key: normalize_score(result.get(key)) for key in score_keys}
    if not scores["overall_score"]:
        scores["overall_score"] = round(sum(scores[key] for key in score_keys[:-1]) / 5)

    return {
        **scores,
        "strengths": normalize_list(result.get("strengths"))[:4],
        "weaknesses": normalize_list(result.get("weaknesses"))[:4],
        "better_sample_answer": str(result.get("better_sample_answer") or "").strip(),
        "improvement_suggestions": normalize_list(result.get("improvement_suggestions"))[:4],
    }


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


def infer_role_keywords(job_role):
    lowered = str(job_role or "").lower()
    for key, keywords in RESUME_ROLE_KEYWORDS.items():
        if key in lowered:
            return keywords
    return ["communication", "problem solving", "project", "leadership", "SQL", "Python", "Git"]


def locally_analyze_resume(file_path, job_role):
    path = Path(file_path)
    try:
        resume_text = extract_text_from_pdf(path)
    except Exception as exc:
        LOGGER.warning("Offline PDF text extraction fallback used for %s: %s", path.name, exc, exc_info=True)
        try:
            raw = path.read_bytes()
        except OSError:
            raw = b""
        resume_text = raw.decode("latin-1", errors="ignore")

    if not resume_text.strip():
        resume_text = f"{path.stem} {job_role or 'general resume'} skills experience projects education"

    lowered = resume_text.lower()
    words = [word.strip(".,:;()[]{}").lower() for word in resume_text.split()]
    word_count = len([word for word in words if word])
    role_keywords = infer_role_keywords(job_role)
    matched = [keyword for keyword in role_keywords if keyword.lower() in lowered]
    missing = [keyword for keyword in role_keywords if keyword not in matched]
    section_terms = ["experience", "education", "projects", "skills", "certifications", "summary"]
    present_sections = [term for term in section_terms if term in lowered]
    weak_sections = [term.title() for term in section_terms if term not in present_sections]
    bullet_count = resume_text.count("\n-") + resume_text.count("\n•") + resume_text.count("\n*")
    metrics_count = sum(1 for token in words if any(char.isdigit() for char in token))
    formatting_score = min(100, max(35, 45 + len(present_sections) * 8 + min(bullet_count, 8) * 2))
    keyword_score = round((len(matched) / max(1, len(role_keywords))) * 100)
    grammar_estimate = min(100, max(45, 78 - max(0, resume_text.count("  ") * 2) - max(0, resume_text.count(" i ") * 3)))
    resume_score = min(100, max(35, round((formatting_score + keyword_score + grammar_estimate + min(100, word_count / 5)) / 4)))
    ats_score = min(100, max(30, round((keyword_score * 0.45) + (formatting_score * 0.35) + (min(100, metrics_count * 8) * 0.2))))
    strengths = []
    if matched:
        strengths.append(f"Includes role-relevant keywords such as {', '.join(matched[:4])}.")
    if metrics_count:
        strengths.append("Uses measurable details, which improves recruiter readability.")
    if len(present_sections) >= 4:
        strengths.append("Contains several core resume sections.")
    if not strengths:
        strengths.append("The resume has readable content that can be improved with targeted edits.")
    suggestions = [
        "Add measurable outcomes to project and experience bullets.",
        "Mirror the most important keywords from the target job description.",
        "Keep section headings standard so ATS parsers can detect them.",
    ]
    if weak_sections:
        suggestions.append(f"Strengthen or add these sections: {', '.join(weak_sections[:4])}.")
    result = {
        "ats_score": ats_score,
        "resume_score": resume_score,
        "grammar_estimate": grammar_estimate,
        "formatting_score": formatting_score,
        "keyword_match": keyword_score,
        "sub_scores": {
            "skills_match": keyword_score,
            "experience_match": min(100, max(35, 45 + metrics_count * 6)),
            "resume_formatting": formatting_score,
            "keyword_optimization": keyword_score,
        },
        "important_keywords": matched or role_keywords[:5],
        "strengths": strengths[:5],
        "missing_skills": missing[:7],
        "weak_sections": weak_sections[:6],
        "improvement_suggestions": suggestions[:6],
        "recommended_projects": [
            f"Build a role-focused {job_role or 'target role'} project with measurable outcomes.",
            "Create a portfolio case study that explains problem, tools, result, and impact.",
        ],
        "resume_summary": (
            "Offline Resume Analysis: Gemini is unavailable, so this report estimates ATS readiness from "
            "resume structure, keyword coverage, measurable details, and formatting signals."
        ),
        "overall_feedback": "Use this offline result as a quick readiness check. Regenerate AI analysis later for deeper semantic feedback.",
        "evaluation_type": "Offline Resume Analysis",
    }
    return normalize_analysis_result(result)


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


def is_quota_error(error):
    error_text = str(error).lower()
    status_code = getattr(error, "status_code", None) or getattr(error, "code", None)
    return (
        str(status_code) == "429"
        or "429" in error_text
        or "resource_exhausted" in error_text
        or "quota" in error_text
        or "usage limit" in error_text
    )


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

            if is_quota_error(exc):
                raise ValueError(GEMINI_QUOTA_MESSAGE) from exc

            if is_overload_error(exc) and not is_last_attempt:
                time.sleep(RETRY_DELAY_SECONDS)
                continue

            if is_overload_error(exc):
                raise ValueError(BUSY_ERROR_MESSAGE) from exc

            raise


def analyze_resume(file_path, job_role):
    if Client is None or types is None:
        LOGGER.error(
            "Google GenAI SDK import failed. Python=%s Error=%r Traceback=%s",
            sys.version,
            GENAI_IMPORT_ERROR,
            GENAI_IMPORT_TRACEBACK,
        )
        raise ValueError(
            "Google GenAI SDK could not be imported. Reinstall dependencies with "
            "python -m pip install --upgrade -r requirements.txt and ensure there is "
            "no local google.py, genai.py, or google folder shadowing the package."
        )

    api_key = get_gemini_api_key()
    resume_text = extract_text_from_pdf(Path(file_path))

    if not resume_text:
        raise ValueError("Could not read text from this PDF. Try a text-based resume PDF.")

    client = Client(api_key=api_key)
    prompt = build_prompt(resume_text, job_role)
    response = ask_gemini_with_retries(client, prompt)

    if not response.text:
        raise ValueError("Gemini did not return any analysis. Please try again.")

    try:
        result = clean_json_response(response.text)
        return normalize_analysis_result(result)
    except json.JSONDecodeError as exc:
        raise ValueError("Gemini returned invalid JSON. Please try again.") from exc


def generate_resume_assistance(action, section, content, target_role=""):
    if Client is None or types is None:
        LOGGER.error(
            "Google GenAI SDK import failed. Python=%s Error=%r Traceback=%s",
            sys.version,
            GENAI_IMPORT_ERROR,
            GENAI_IMPORT_TRACEBACK,
        )
        raise ValueError("Google GenAI SDK could not be imported. Reinstall dependencies.")

    if not str(content or "").strip():
        raise ValueError("Add some draft content before using AI assistance.")

    client = Client(api_key=get_gemini_api_key())
    prompt = build_builder_prompt(action, section, str(content), target_role)
    response = ask_gemini_with_retries(client, prompt)

    if not response.text:
        raise ValueError("Gemini did not return any resume content. Please try again.")

    try:
        return normalize_builder_response(clean_json_response(response.text))
    except json.JSONDecodeError as exc:
        raise ValueError("Gemini returned invalid JSON. Please try again.") from exc


def generate_interview_questions(setup):
    if Client is None or types is None:
        LOGGER.error(
            "Google GenAI SDK import failed. Python=%s Error=%r Traceback=%s",
            sys.version,
            GENAI_IMPORT_ERROR,
            GENAI_IMPORT_TRACEBACK,
        )
        raise ValueError("Google GenAI SDK could not be imported. Reinstall dependencies.")

    client = Client(api_key=get_gemini_api_key())
    response = ask_gemini_with_retries(client, build_interview_questions_prompt(setup))

    if not response.text:
        raise ValueError("Gemini did not return interview questions. Please try again.")

    try:
        return normalize_interview_questions(clean_json_response(response.text))
    except json.JSONDecodeError as exc:
        raise ValueError("Gemini returned invalid JSON. Please try again.") from exc


def generate_aptitude_questions(setup):
    if Client is None or types is None:
        LOGGER.error(
            "Google GenAI SDK import failed. Python=%s Error=%r Traceback=%s",
            sys.version,
            GENAI_IMPORT_ERROR,
            GENAI_IMPORT_TRACEBACK,
        )
        raise ValueError("Google GenAI SDK could not be imported. Reinstall dependencies.")

    client = Client(api_key=get_gemini_api_key())
    response = ask_gemini_with_retries(client, build_aptitude_questions_prompt(setup))

    if not response.text:
        raise ValueError("Gemini did not return aptitude questions. Please try again.")

    try:
        return normalize_aptitude_questions(clean_json_response(response.text))
    except json.JSONDecodeError as exc:
        raise ValueError("Gemini returned invalid JSON. Please try again.") from exc


def evaluate_interview(setup, answers):
    if Client is None or types is None:
        LOGGER.error(
            "Google GenAI SDK import failed. Python=%s Error=%r Traceback=%s",
            sys.version,
            GENAI_IMPORT_ERROR,
            GENAI_IMPORT_TRACEBACK,
        )
        raise ValueError("Google GenAI SDK could not be imported. Reinstall dependencies.")

    if not answers:
        raise ValueError("Answer at least one interview question before finishing.")

    client = Client(api_key=get_gemini_api_key())
    response = ask_gemini_with_retries(client, build_interview_evaluation_prompt(setup, answers))

    if not response.text:
        raise ValueError("Gemini did not return an interview report. Please try again.")

    try:
        return normalize_interview_report(clean_json_response(response.text), setup, answers)
    except json.JSONDecodeError as exc:
        raise ValueError("Gemini returned invalid JSON. Please try again.") from exc


def evaluate_aptitude(setup, questions, answers, started_at=None, finished_at=None):
    answer_map = answers if isinstance(answers, dict) else {}
    rows = []
    topic_totals = {}
    difficulty_totals = {}
    correct = 0
    for index, question in enumerate(questions, start=1):
        selected = str(answer_map.get(str(index)) or answer_map.get(index) or "").strip().upper()[:1]
        expected = str(question.get("correct_answer") or "").strip().upper()[:1]
        is_correct = selected == expected
        if is_correct:
            correct += 1
        topic = question.get("topic") or question.get("category") or setup.get("category") or "Mixed"
        difficulty = question.get("difficulty") or setup.get("difficulty") or "Medium"
        topic_totals.setdefault(topic, {"correct": 0, "total": 0})
        difficulty_totals.setdefault(difficulty, {"correct": 0, "total": 0})
        topic_totals[topic]["total"] += 1
        difficulty_totals[difficulty]["total"] += 1
        if is_correct:
            topic_totals[topic]["correct"] += 1
            difficulty_totals[difficulty]["correct"] += 1
        rows.append({**question, "selected_answer": selected, "is_correct": is_correct})

    total = max(1, len(questions))
    wrong = len(questions) - correct
    accuracy = round((correct / total) * 100)

    def summarize(stats):
        return [
            {"topic": topic, "correct": value["correct"], "total": value["total"], "accuracy": round((value["correct"] / max(1, value["total"])) * 100)}
            for topic, value in stats.items()
        ]

    topic_performance = summarize(topic_totals)
    difficulty_analysis = summarize(difficulty_totals)
    weak_areas = [item["topic"] for item in topic_performance if item["accuracy"] < 60]
    strong_areas = [item["topic"] for item in topic_performance if item["accuracy"] >= 75]
    return {
        "setup": setup,
        "questions": rows,
        "correct_answers": correct,
        "wrong_answers": wrong,
        "accuracy": accuracy,
        "time_taken": "",
        "topic_wise_performance": topic_performance,
        "weak_areas": weak_areas or ["Review missed questions and explanations."],
        "strong_areas": strong_areas or ["Build consistency across all categories."],
        "difficulty_analysis": difficulty_analysis,
        "final_score": accuracy,
        "started_at": started_at,
        "finished_at": finished_at,
    }


def evaluate_interview_answer(setup, question, answer):
    if Client is None or types is None:
        LOGGER.error(
            "Google GenAI SDK import failed. Python=%s Error=%r Traceback=%s",
            sys.version,
            GENAI_IMPORT_ERROR,
            GENAI_IMPORT_TRACEBACK,
        )
        raise ValueError("Google GenAI SDK could not be imported. Reinstall dependencies.")

    client = Client(api_key=get_gemini_api_key())
    response = ask_gemini_with_retries(client, build_answer_evaluation_prompt(setup, question, answer))

    if not response.text:
        raise ValueError("Gemini did not return an answer evaluation. Please try again.")

    try:
        return normalize_answer_evaluation(clean_json_response(response.text))
    except json.JSONDecodeError as exc:
        raise ValueError("Gemini returned invalid JSON. Please try again.") from exc
