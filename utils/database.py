import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from werkzeug.security import generate_password_hash


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "resumeiq.sqlite3"
DEFAULT_USER_EMAIL = "demo@resumeiq.local"


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0,
                email_verified INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                last_login TEXT,
                profile_image TEXT DEFAULT '',
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                profile_picture TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                linkedin TEXT DEFAULT '',
                github TEXT DEFAULT '',
                portfolio TEXT DEFAULT '',
                location TEXT DEFAULT '',
                college TEXT DEFAULT '',
                university TEXT DEFAULT '',
                branch TEXT DEFAULT '',
                graduation_year TEXT DEFAULT '',
                experience TEXT DEFAULT '',
                career_goal TEXT DEFAULT '',
                skills TEXT DEFAULT '[]',
                bio TEXT DEFAULT '',
                current_status TEXT DEFAULT '',
                preferred_role TEXT DEFAULT '',
                onboarding_complete INTEGER DEFAULT 0,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                appearance TEXT DEFAULT 'dark',
                language TEXT DEFAULT 'English',
                notifications TEXT DEFAULT 'Enabled',
                privacy TEXT DEFAULT 'Private workspace',
                api_settings TEXT DEFAULT '',
                session_timeout_minutes INTEGER DEFAULT 120,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                category TEXT DEFAULT 'system',
                is_read INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS job_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Wishlist',
                notes TEXT DEFAULT '',
                timeline_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_job_applications_user_status ON job_applications (user_id, status, updated_at DESC)")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                filename TEXT NOT NULL,
                job_role TEXT NOT NULL,
                ats_score INTEGER,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS generated_resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                full_name TEXT NOT NULL,
                target_role TEXT,
                resume_json TEXT NOT NULL,
                title TEXT DEFAULT '',
                template TEXT DEFAULT '',
                status TEXT DEFAULT 'active',
                is_favorite INTEGER DEFAULT 0,
                archived_at TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                candidate_name TEXT,
                job_role TEXT NOT NULL,
                experience_level TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                interview_type TEXT NOT NULL,
                question_count INTEGER NOT NULL,
                overall_score INTEGER,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS interview_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS aptitude_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                candidate_name TEXT,
                category TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                question_count INTEGER NOT NULL,
                final_score INTEGER,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        migrate_columns(conn)
        ensure_default_user(conn)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS question_bank (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                expected_answer TEXT NOT NULL,
                keywords TEXT NOT NULL,
                category TEXT NOT NULL,
                topic TEXT NOT NULL,
                experience_level TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_question_bank_category
            ON question_bank (category, difficulty, experience_level)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS aptitude_question_bank (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                explanation TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                category TEXT NOT NULL,
                topic TEXT DEFAULT '',
                company_level TEXT DEFAULT '',
                time_limit INTEGER DEFAULT 60,
                question_type TEXT DEFAULT 'MCQ'
            )
            """
        )
        existing_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(aptitude_question_bank)").fetchall()
        }
        for column_name, definition in {
            "topic": "TEXT DEFAULT ''",
            "company_level": "TEXT DEFAULT ''",
            "time_limit": "INTEGER DEFAULT 60",
            "question_type": "TEXT DEFAULT 'MCQ'",
        }.items():
            if column_name not in existing_columns:
                conn.execute(f"ALTER TABLE aptitude_question_bank ADD COLUMN {column_name} {definition}")
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_aptitude_question_bank_category
            ON aptitude_question_bank (category, difficulty)
            """
        )
    from utils.question_bank import seed_question_bank

    seed_question_bank()


def migrate_columns(conn):
    user_columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    for column, definition in {
        "last_login": "TEXT",
        "profile_image": "TEXT DEFAULT ''",
    }.items():
        if column not in user_columns:
            conn.execute(f"ALTER TABLE users ADD COLUMN {column} {definition}")

    table_columns = {
        table: {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for table in ["analyses", "generated_resumes", "interviews", "interview_sessions", "aptitude_tests"]
    }
    for table in ["analyses", "generated_resumes", "interviews", "interview_sessions", "aptitude_tests"]:
        if "user_id" not in table_columns[table]:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER")
    generated_extra = {
        "title": "TEXT DEFAULT ''",
        "template": "TEXT DEFAULT ''",
        "status": "TEXT DEFAULT 'active'",
        "is_favorite": "INTEGER DEFAULT 0",
        "archived_at": "TEXT",
    }
    for column, definition in generated_extra.items():
        if column not in table_columns["generated_resumes"]:
            conn.execute(f"ALTER TABLE generated_resumes ADD COLUMN {column} {definition}")


def ensure_default_user(conn):
    now = utc_now_iso()
    row = conn.execute("SELECT id FROM users WHERE email = ?", (DEFAULT_USER_EMAIL,)).fetchone()
    if row:
        default_user_id = row["id"]
    else:
        cursor = conn.execute(
            """
            INSERT INTO users (email, password_hash, full_name, is_admin, email_verified, created_at, updated_at)
            VALUES (?, ?, ?, 1, 1, ?, ?)
            """,
            (DEFAULT_USER_EMAIL, generate_password_hash("DemoPass123!"), "Vinay Prince", now, now),
        )
        default_user_id = cursor.lastrowid
        conn.execute(
            "INSERT OR REPLACE INTO user_profiles (user_id, skills, career_goal, onboarding_complete, updated_at) VALUES (?, ?, ?, 1, ?)",
            (default_user_id, json.dumps(["Python", "Flask", "AI", "Resume Optimization", "Full Stack"]), "Build a strong AI engineering portfolio and land interview-ready roles.", now),
        )
        conn.execute("INSERT OR REPLACE INTO user_settings (user_id, updated_at) VALUES (?, ?)", (default_user_id, now))

    for table in ["analyses", "generated_resumes", "interviews", "interview_sessions", "aptitude_tests"]:
        conn.execute(f"UPDATE {table} SET user_id = ? WHERE user_id IS NULL", (default_user_id,))


def get_default_user_id():
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (DEFAULT_USER_EMAIL,)).fetchone()
    return row["id"] if row else 1


def create_user(email, password, full_name):
    now = utc_now_iso()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users (email, password_hash, full_name, email_verified, created_at, updated_at)
            VALUES (?, ?, ?, 0, ?, ?)
            """,
            (email.lower(), generate_password_hash(password), full_name, now, now),
        )
        user_id = cursor.lastrowid
        conn.execute("INSERT INTO user_profiles (user_id, updated_at) VALUES (?, ?)", (user_id, now))
        conn.execute("INSERT INTO user_settings (user_id, updated_at) VALUES (?, ?)", (user_id, now))
        create_notification_for_conn(conn, user_id, "Welcome to ResumeIQ+", "Complete onboarding to personalize your dashboard.", "onboarding")
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def get_user_by_email(email):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def record_user_login(user_id):
    """Persist the most recent successful login for the authenticated account."""
    now = utc_now_iso()
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET last_login = ?, updated_at = ? WHERE id = ?",
            (now, now, user_id),
        )


def create_notification_for_conn(conn, user_id, title, body, category="system"):
    conn.execute(
        "INSERT INTO notifications (user_id, title, body, category, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, title, body, category, utc_now_iso()),
    )


def create_notification(user_id, title, body, category="system"):
    with get_connection() as conn:
        create_notification_for_conn(conn, user_id, title, body, category)


def save_analysis(filename, job_role, result, user_id=None):
    user_id = user_id or get_default_user_id()
    score = result.get("ats_score") if isinstance(result, dict) else None
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO analyses (user_id, filename, job_role, ats_score, result_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                filename,
                job_role,
                score,
                json.dumps(result),
                utc_now_iso(),
            ),
        )
        create_notification_for_conn(conn, user_id, "Resume analyzed successfully", f"{filename} scored {score or 0}% for {job_role}.", "resume")


def save_generated_resume(resume, user_id=None):
    user_id = user_id or get_default_user_id()
    if not isinstance(resume, dict):
        resume = {}

    personal = resume.get("personal_details") or {}
    if not isinstance(personal, dict):
        personal = {}

    full_name = personal.get("full_name") or "Untitled Resume"
    target_role = resume.get("target_role") or resume.get("career_objective") or ""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO generated_resumes (user_id, full_name, target_role, resume_json, title, template, status, is_favorite, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'active', 0, ?)
            """,
            (
                user_id,
                full_name,
                target_role[:160],
                json.dumps(resume),
                resume.get("title") or full_name,
                resume.get("template") or "Modern",
                utc_now_iso(),
            ),
        )
        create_notification_for_conn(conn, user_id, "Resume saved", f"{full_name} was added to your resume library.", "resume")
        return cursor.lastrowid


def get_recent_analyses(limit=6, user_id=None):
    user_id = user_id or get_default_user_id()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, filename, job_role, ats_score, created_at
            FROM analyses
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def get_recent_generated_resumes(limit=5, user_id=None):
    user_id = user_id or get_default_user_id()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, full_name, target_role, title, template, status, is_favorite, created_at
            FROM generated_resumes
            WHERE user_id = ? AND COALESCE(status, 'active') != 'deleted'
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def save_interview(report, user_id=None):
    user_id = user_id or get_default_user_id()
    if not isinstance(report, dict):
        report = {}

    setup = report.get("setup") or {}
    scores = report.get("scores") or {}
    overall = scores.get("overall_score")
    try:
        overall = int(overall)
    except (TypeError, ValueError):
        overall = 0

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO interviews (
                user_id, candidate_name, job_role, experience_level, difficulty,
                interview_type, question_count, overall_score, report_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                setup.get("candidate_name") or "Candidate",
                setup.get("job_role") or "General Role",
                setup.get("experience_level") or "Entry",
                setup.get("difficulty") or "Medium",
                setup.get("interview_type") or "Mixed",
                int(setup.get("question_count") or 0),
                max(0, min(overall, 100)),
                json.dumps(report),
                utc_now_iso(),
            ),
        )
        create_notification_for_conn(conn, user_id, "Interview completed", f"{setup.get('job_role') or 'Interview'} report is ready.", "interview")
        return cursor.lastrowid


def save_interview_session(session, user_id=None):
    user_id = user_id or get_default_user_id()
    if not isinstance(session, dict):
        session = {}
    now = utc_now_iso()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO interview_sessions (user_id, session_json, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, json.dumps(session), session.get("status") or "active", now, now),
        )
        return cursor.lastrowid


def update_interview_session(session_id, session, status="active", user_id=None):
    if not session_id:
        return False
    if not isinstance(session, dict):
        session = {}
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE interview_sessions
            SET session_json = ?, status = ?, updated_at = ?
            WHERE id = ? AND (? IS NULL OR user_id = ?)
            """,
            (json.dumps(session), status, utc_now_iso(), session_id, user_id, user_id),
        )
        return cursor.rowcount > 0


def get_interview_session(session_id, user_id=None):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, session_json, status, created_at, updated_at
            FROM interview_sessions
            WHERE id = ? AND (? IS NULL OR user_id = ?)
            """,
            (session_id, user_id, user_id),
        ).fetchone()
    if not row:
        return None
    try:
        session = json.loads(row["session_json"])
    except json.JSONDecodeError:
        session = {}
    if isinstance(session, dict):
        session.update({"id": row["id"], "status": row["status"], "created_at": row["created_at"], "updated_at": row["updated_at"]})
    return session


def save_aptitude_test(result, user_id=None):
    user_id = user_id or get_default_user_id()
    if not isinstance(result, dict):
        result = {}
    setup = result.get("setup") if isinstance(result.get("setup"), dict) else {}
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO aptitude_tests (
                user_id, candidate_name, category, difficulty, question_count, final_score, result_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                setup.get("candidate_name") or "Candidate",
                setup.get("category") or "Mixed",
                setup.get("difficulty") or "Medium",
                int(setup.get("question_count") or len(result.get("questions") or [])),
                int(result.get("final_score") or 0),
                json.dumps(result),
                utc_now_iso(),
            ),
        )
        create_notification_for_conn(conn, user_id, "Aptitude report ready", f"{setup.get('category') or 'Aptitude'} score saved.", "aptitude")
        return cursor.lastrowid


def get_recent_aptitude_tests(limit=5, user_id=None):
    user_id = user_id or get_default_user_id()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, candidate_name, category, difficulty, question_count, final_score, created_at
            FROM aptitude_tests
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def get_aptitude_test(test_id, user_id=None):
    with get_connection() as conn:
        row = conn.execute("SELECT id, result_json FROM aptitude_tests WHERE id = ? AND (? IS NULL OR user_id = ?)", (test_id, user_id, user_id)).fetchone()
    if not row:
        return None
    try:
        result = json.loads(row["result_json"])
    except json.JSONDecodeError:
        result = {}
    if isinstance(result, dict):
        result["id"] = row["id"]
    return result


def get_recent_interviews(limit=5, user_id=None):
    user_id = user_id or get_default_user_id()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, candidate_name, job_role, interview_type, difficulty, overall_score, created_at
            FROM interviews
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def get_interview_history(limit=50, user_id=None):
    user_id = user_id or get_default_user_id()
    with get_connection() as conn:
        interviews = conn.execute(
            """
            SELECT id, candidate_name, job_role, experience_level, difficulty,
                   interview_type, question_count, overall_score, created_at
            FROM interviews
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        aptitude_tests = conn.execute(
            """
            SELECT id, candidate_name, category, difficulty, question_count, final_score, created_at
            FROM aptitude_tests
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    history = []
    for row in interviews:
        item = dict(row)
        item["record_type"] = "interview"
        history.append(item)
    for row in aptitude_tests:
        item = dict(row)
        item.update({"record_type": "aptitude", "job_role": item.get("category") or "Aptitude Test", "interview_type": "Aptitude Test", "overall_score": item.get("final_score") or 0})
        history.append(item)
    return sorted(history, key=lambda item: item.get("created_at") or "", reverse=True)[:limit]


def get_interview_report(interview_id, user_id=None):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, report_json
            FROM interviews
            WHERE id = ? AND (? IS NULL OR user_id = ?)
            """,
            (interview_id, user_id, user_id),
        ).fetchone()

    if not row:
        return None

    try:
        report = json.loads(row["report_json"])
    except json.JSONDecodeError:
        report = {}

    if isinstance(report, dict):
        report["id"] = row["id"]
    return report


def delete_interview(interview_id, user_id=None):
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM interviews WHERE id = ? AND (? IS NULL OR user_id = ?)", (interview_id, user_id, user_id))
        return cursor.rowcount > 0


def delete_aptitude_test(test_id, user_id=None):
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM aptitude_tests WHERE id = ? AND (? IS NULL OR user_id = ?)", (test_id, user_id, user_id))
    return cursor.rowcount > 0


def get_interview_analytics(user_id=None):
    user_id = user_id or get_default_user_id()
    with get_connection() as conn:
        trend_rows = conn.execute(
            """
            SELECT id, candidate_name, job_role, interview_type, overall_score, report_json, created_at
            FROM interviews
            WHERE user_id = ?
            ORDER BY id ASC
            LIMIT 30
            """
        , (user_id,)).fetchall()

    technical_trend = []
    communication_trend = []
    overall_trend = []

    for row in trend_rows:
        try:
            report = json.loads(row["report_json"])
        except json.JSONDecodeError:
            report = {}
        scores = report.get("scores") if isinstance(report, dict) else {}
        if not isinstance(scores, dict):
            scores = {}

        label = row["created_at"][:10] if row["created_at"] else f"#{row['id']}"
        technical_trend.append({"label": label, "score": int(scores.get("technical_score") or 0)})
        communication_trend.append({"label": label, "score": int(scores.get("communication_score") or 0)})
        overall_trend.append({"label": label, "score": int(row["overall_score"] or 0)})

    return {
        "technical_trend": technical_trend,
        "communication_trend": communication_trend,
        "overall_trend": overall_trend,
    }


def get_latest_resume(user_id=None):
    user_id = user_id or get_default_user_id()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, full_name, target_role, created_at
            FROM generated_resumes
            WHERE user_id = ? AND COALESCE(status, 'active') = 'active'
            ORDER BY id DESC
            LIMIT 1
            """
        , (user_id,)).fetchone()
    return dict(row) if row else None


def get_latest_analysis(user_id=None):
    user_id = user_id or get_default_user_id()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, filename, job_role, ats_score, created_at
            FROM analyses
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """
        , (user_id,)).fetchone()
    return dict(row) if row else None


def get_dashboard_stats(user_id=None):
    user_id = user_id or get_default_user_id()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_resumes,
                COALESCE(ROUND(AVG(ats_score)), 0) AS avg_score,
                COALESCE(MAX(ats_score), 0) AS best_score
            FROM analyses
            WHERE user_id = ?
            """
        , (user_id,)).fetchone()
        generated_count = conn.execute("SELECT COUNT(*) AS total FROM generated_resumes WHERE user_id = ? AND COALESCE(status, 'active') != 'deleted'", (user_id,)).fetchone()["total"]
        interview_row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_interviews,
                COALESCE(ROUND(AVG(overall_score)), 0) AS avg_interview_score,
                COALESCE(MAX(overall_score), 0) AS best_interview_score
            FROM interviews
            WHERE user_id = ?
            """
        , (user_id,)).fetchone()
        aptitude_row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_aptitude_tests,
                COALESCE(ROUND(AVG(final_score)), 0) AS avg_aptitude_score,
                COALESCE(MAX(final_score), 0) AS best_aptitude_score
            FROM aptitude_tests
            WHERE user_id = ?
            """
        , (user_id,)).fetchone()

    stats = dict(row)
    stats["generated_resumes"] = generated_count
    stats.update(dict(interview_row))
    stats.update(dict(aptitude_row))
    return stats


def get_profile_summary(user_id=None):
    user_id = user_id or get_default_user_id()
    stats = get_dashboard_stats(user_id)
    user = get_user_by_id(user_id) or {}
    profile = get_profile(user_id)
    return {
        "name": user.get("full_name") or "ResumeIQ+ User",
        "email": user.get("email") or "",
        "skills": profile.get("skills", []),
        "career_goal": profile.get("career_goal") or "Build a focused career plan with ResumeIQ+.",
        "onboarding_complete": bool(profile.get("onboarding_complete")),
        "is_admin": bool(user.get("is_admin")),
        "resume_count": stats.get("generated_resumes", 0),
        "interview_count": stats.get("total_interviews", 0),
        "average_ats_score": stats.get("avg_score", 0),
        "average_interview_score": stats.get("avg_interview_score", 0),
    }


def parse_skills(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
            if isinstance(decoded, list):
                return parse_skills(decoded)
        except json.JSONDecodeError:
            pass
        return [item.strip() for item in value.replace("\n", ",").split(",") if item.strip()]
    return []


def get_profile(user_id):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT u.id AS user_id, u.email, u.full_name, u.is_admin, u.email_verified,
                   p.profile_picture, p.phone, p.linkedin, p.github, p.portfolio, p.location,
                   p.college, p.university, p.branch, p.graduation_year, p.experience,
                   p.career_goal, p.skills, p.bio, p.current_status, p.preferred_role,
                   p.onboarding_complete
            FROM users u
            LEFT JOIN user_profiles p ON p.user_id = u.id
            WHERE u.id = ?
            """,
            (user_id,),
        ).fetchone()
    if not row:
        return {}
    profile = dict(row)
    profile["skills"] = parse_skills(profile.get("skills") or "[]")
    return profile


def update_profile(user_id, data):
    allowed = [
        "profile_picture", "phone", "linkedin", "github", "portfolio", "location",
        "college", "university", "branch", "graduation_year", "experience",
        "career_goal", "bio", "current_status", "preferred_role",
    ]
    full_name = str(data.get("full_name") or "").strip()
    email = str(data.get("email") or "").strip().lower()
    skills = parse_skills(data.get("skills"))
    now = utc_now_iso()
    with get_connection() as conn:
        if full_name:
            conn.execute("UPDATE users SET full_name = ?, updated_at = ? WHERE id = ?", (full_name, now, user_id))
        if email:
            conn.execute("UPDATE users SET email = ?, updated_at = ? WHERE id = ?", (email, now, user_id))
        values = {key: str(data.get(key) or "").strip()[:1000] for key in allowed}
        values["skills"] = json.dumps(skills)
        values["updated_at"] = now
        assignments = ", ".join([f"{key} = ?" for key in values])
        conn.execute(
            f"UPDATE user_profiles SET {assignments} WHERE user_id = ?",
            tuple(values.values()) + (user_id,),
        )
        create_notification_for_conn(conn, user_id, "Profile updated", "Your account profile changes were saved.", "profile")
    return get_profile(user_id)


def complete_onboarding(user_id, data):
    payload = dict(data)
    payload["current_status"] = str(data.get("current_status") or "").strip()
    payload["preferred_role"] = str(data.get("preferred_role") or "").strip()
    payload["experience"] = str(data.get("experience") or "").strip()
    payload["career_goal"] = str(data.get("career_goal") or "").strip()
    payload["skills"] = data.get("primary_skills") or data.get("skills") or []
    profile = update_profile(user_id, payload)
    with get_connection() as conn:
        conn.execute("UPDATE user_profiles SET onboarding_complete = 1, updated_at = ? WHERE user_id = ?", (utc_now_iso(), user_id))
        create_notification_for_conn(conn, user_id, "Onboarding complete", "Your dashboard is now personalized for your career goal.", "onboarding")
    profile["onboarding_complete"] = True
    return profile


def get_settings(user_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,)).fetchone()
    return dict(row) if row else {}


def update_settings(user_id, data):
    allowed = ["appearance", "language", "notifications", "privacy", "api_settings", "session_timeout_minutes"]
    values = {}
    for key in allowed:
        if key in data:
            values[key] = data[key]
    if "session_timeout_minutes" in values:
        try:
            values["session_timeout_minutes"] = max(15, min(int(values["session_timeout_minutes"]), 1440))
        except (TypeError, ValueError):
            values["session_timeout_minutes"] = 120
    values["updated_at"] = utc_now_iso()
    assignments = ", ".join([f"{key} = ?" for key in values])
    with get_connection() as conn:
        conn.execute(f"UPDATE user_settings SET {assignments} WHERE user_id = ?", tuple(values.values()) + (user_id,))
    return get_settings(user_id)


def list_resumes(user_id, query="", status="active", favorite=None):
    clauses = ["user_id = ?"]
    params = [user_id]
    if status != "all":
        clauses.append("COALESCE(status, 'active') = ?")
        params.append(status)
    else:
        clauses.append("COALESCE(status, 'active') != 'deleted'")
    if favorite is not None:
        clauses.append("COALESCE(is_favorite, 0) = ?")
        params.append(1 if favorite else 0)
    if query:
        clauses.append("(full_name LIKE ? OR target_role LIKE ? OR title LIKE ? OR template LIKE ?)")
        like = f"%{query}%"
        params.extend([like, like, like, like])
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT id, full_name, target_role, title, template, status, is_favorite, created_at, archived_at
            FROM generated_resumes
            WHERE {' AND '.join(clauses)}
            ORDER BY is_favorite DESC, id DESC
            """,
            params,
        ).fetchall()
    return [dict(row) for row in rows]


def get_resume(user_id, resume_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM generated_resumes WHERE id = ? AND user_id = ?", (resume_id, user_id)).fetchone()
    if not row:
        return None
    item = dict(row)
    try:
        item["resume"] = json.loads(item.get("resume_json") or "{}")
    except json.JSONDecodeError:
        item["resume"] = {}
    return item


def update_resume_state(user_id, resume_id, action, title=None):
    now = utc_now_iso()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM generated_resumes WHERE id = ? AND user_id = ?", (resume_id, user_id)).fetchone()
        if not row:
            return None
        if action == "duplicate":
            cursor = conn.execute(
                """
                INSERT INTO generated_resumes (user_id, full_name, target_role, resume_json, title, template, status, is_favorite, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'active', 0, ?)
                """,
                (user_id, row["full_name"], row["target_role"], row["resume_json"], f"Copy of {row['title'] or row['full_name']}", row["template"], now),
            )
            return get_resume(user_id, cursor.lastrowid)
        if action == "rename":
            conn.execute("UPDATE generated_resumes SET title = ? WHERE id = ? AND user_id = ?", (str(title or "").strip()[:160], resume_id, user_id))
        elif action == "archive":
            conn.execute("UPDATE generated_resumes SET status = 'archived', archived_at = ? WHERE id = ? AND user_id = ?", (now, resume_id, user_id))
        elif action == "restore":
            conn.execute("UPDATE generated_resumes SET status = 'active', archived_at = NULL WHERE id = ? AND user_id = ?", (resume_id, user_id))
        elif action == "favorite":
            conn.execute("UPDATE generated_resumes SET is_favorite = CASE WHEN COALESCE(is_favorite, 0) = 1 THEN 0 ELSE 1 END WHERE id = ? AND user_id = ?", (resume_id, user_id))
        elif action == "delete":
            conn.execute("UPDATE generated_resumes SET status = 'deleted' WHERE id = ? AND user_id = ?", (resume_id, user_id))
        else:
            return None
    return get_resume(user_id, resume_id)


JOB_STATUSES = ("Wishlist", "Applied", "Assessment", "Interview", "Offer", "Rejected")


def list_job_applications(user_id, status=""):
    clauses, params = ["user_id = ?"], [user_id]
    if status in JOB_STATUSES:
        clauses.append("status = ?")
        params.append(status)
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM job_applications WHERE {' AND '.join(clauses)} ORDER BY updated_at DESC, id DESC",
            tuple(params),
        ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        try:
            item["timeline"] = json.loads(item.pop("timeline_json") or "[]")
        except json.JSONDecodeError:
            item["timeline"] = []
        items.append(item)
    return items


def save_job_application(user_id, data):
    company = str(data.get("company") or "").strip()[:160]
    role = str(data.get("role") or "").strip()[:160]
    status = str(data.get("status") or "Wishlist").strip()
    if not company or not role:
        raise ValueError("Company and role are required.")
    if status not in JOB_STATUSES:
        status = "Wishlist"
    now = utc_now_iso()
    timeline = [{"status": status, "at": now}]
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO job_applications (user_id, company, role, status, notes, timeline_json, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, company, role, status, str(data.get("notes") or "").strip()[:4000], json.dumps(timeline), now, now),
        )
        create_notification_for_conn(conn, user_id, "Job added to tracker", f"{company} — {role} is now in {status}.", "job")
    return cursor.lastrowid


def update_job_application(user_id, job_id, data):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM job_applications WHERE id = ? AND user_id = ?", (job_id, user_id)).fetchone()
        if not row:
            return None
        old = dict(row)
        status = str(data.get("status") or old["status"]).strip()
        if status not in JOB_STATUSES:
            raise ValueError("Choose a valid application status.")
        try:
            timeline = json.loads(old["timeline_json"] or "[]")
        except json.JSONDecodeError:
            timeline = []
        now = utc_now_iso()
        if status != old["status"]:
            timeline.append({"status": status, "at": now})
        company = str(data.get("company") or old["company"]).strip()[:160]
        role = str(data.get("role") or old["role"]).strip()[:160]
        notes = str(data.get("notes") if "notes" in data else old["notes"]).strip()[:4000]
        conn.execute("UPDATE job_applications SET company = ?, role = ?, status = ?, notes = ?, timeline_json = ?, updated_at = ? WHERE id = ? AND user_id = ?", (company, role, status, notes, json.dumps(timeline), now, job_id, user_id))
    return next((item for item in list_job_applications(user_id) if item["id"] == job_id), None)


def delete_job_application(user_id, job_id):
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM job_applications WHERE id = ? AND user_id = ?", (job_id, user_id))
    return cursor.rowcount > 0


def get_notifications(user_id, limit=20):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, title, body, category, is_read, created_at
            FROM notifications
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def global_search(user_id, query):
    query = str(query or "").strip()
    if not query:
        return {"resumes": [], "templates": [], "reports": [], "interviews": []}
    like = f"%{query}%"
    with get_connection() as conn:
        resumes = conn.execute(
            """
            SELECT id, title, full_name, target_role, template, created_at
            FROM generated_resumes
            WHERE user_id = ? AND COALESCE(status, 'active') != 'deleted'
              AND (title LIKE ? OR full_name LIKE ? OR target_role LIKE ? OR template LIKE ?)
            LIMIT 10
            """,
            (user_id, like, like, like, like),
        ).fetchall()
        reports = conn.execute(
            """
            SELECT id, filename, job_role, ats_score, created_at
            FROM analyses
            WHERE user_id = ? AND (filename LIKE ? OR job_role LIKE ?)
            LIMIT 10
            """,
            (user_id, like, like),
        ).fetchall()
        interviews = conn.execute(
            """
            SELECT id, candidate_name, job_role, interview_type, overall_score, created_at
            FROM interviews
            WHERE user_id = ? AND (candidate_name LIKE ? OR job_role LIKE ? OR interview_type LIKE ?)
            LIMIT 10
            """,
            (user_id, like, like, like),
        ).fetchall()
    templates = [
        {"name": name, "category": name}
        for name in ["Modern", "Corporate", "Developer", "Student", "Minimal", "Executive", "Creative", "ATS Friendly"]
        if query.lower() in name.lower()
    ]
    return {
        "resumes": [dict(row) for row in resumes],
        "templates": templates,
        "reports": [dict(row) for row in reports],
        "interviews": [dict(row) for row in interviews],
    }


def get_admin_analytics():
    with get_connection() as conn:
        users = conn.execute("SELECT id, email, full_name, is_admin, email_verified, created_at FROM users ORDER BY id DESC").fetchall()
        counts = {
            "users": conn.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"],
            "resumes": conn.execute("SELECT COUNT(*) AS total FROM generated_resumes WHERE COALESCE(status, 'active') != 'deleted'").fetchone()["total"],
            "analyses": conn.execute("SELECT COUNT(*) AS total FROM analyses").fetchone()["total"],
            "interviews": conn.execute("SELECT COUNT(*) AS total FROM interviews").fetchone()["total"],
            "api_usage": conn.execute("SELECT COUNT(*) AS total FROM analyses").fetchone()["total"] + conn.execute("SELECT COUNT(*) AS total FROM interviews").fetchone()["total"],
        }
        uploaded = conn.execute("SELECT id, user_id, filename, job_role, ats_score, created_at FROM analyses ORDER BY id DESC LIMIT 50").fetchall()
    return {"counts": counts, "users": [dict(row) for row in users], "uploaded_resumes": [dict(row) for row in uploaded]}


def delete_user(user_id):
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM users WHERE id = ? AND email != ?", (user_id, DEFAULT_USER_EMAIL))
        return cursor.rowcount > 0
