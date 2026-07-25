import json
import random

from utils.database import get_connection


QUESTION_CATEGORIES = [
    "Python",
    "Java",
    "SQL",
    "JavaScript",
    "HTML",
    "CSS",
    "React",
    "Flask",
    "Data Analyst",
    "AI",
    "Machine Learning",
    "Cloud",
    "Cyber Security",
    "Full Stack Developer",
    "Frontend Developer",
    "Backend Developer",
    "Software Engineer",
    "Data Scientist",
    "AI / ML Engineer",
    "HR Interview",
    "Behavioral Interview",
    "Communication Skills",
]

APTITUDE_CATEGORIES = {
    "Quantitative Aptitude",
    "Logical Reasoning",
    "Verbal Ability",
    "Data Interpretation",
    "Analytical Reasoning",
    "Mixed Aptitude",
}

ROLE_ALIASES = {
    "python": "Python",
    "java": "Java",
    "full stack": "Full Stack Developer",
    "frontend": "Frontend Developer",
    "html": "HTML",
    "css": "CSS",
    "react": "React",
    "javascript": "JavaScript",
    "flask": "Flask",
    "backend": "Backend Developer",
    "software": "Software Engineer",
    "data analyst": "Data Analyst",
    "data scientist": "Data Scientist",
    "ai engineer": "AI",
    "artificial intelligence": "AI",
    "ai / ml": "AI / ML Engineer",
    "machine learning": "Machine Learning",
    "ml engineer": "Machine Learning",
    "sql": "SQL",
    "cyber": "Cyber Security",
    "security": "Cyber Security",
    "cloud": "Cloud",
    "hr": "HR Interview",
    "behavior": "Behavioral Interview",
    "communication": "Communication Skills",
    "logical": "Logical Reasoning",
    "quantitative": "Quantitative Aptitude",
    "verbal": "Verbal Ability",
    "data interpretation": "Data Interpretation",
    "analytical": "Analytical Reasoning",
    "aptitude": "Mixed Aptitude",
    "mixed": "Mixed Aptitude",
}

ROLE_TOPICS = {
    "Python": ["Python data model", "iterators", "generators", "decorators", "context managers", "async IO", "testing", "packaging", "pandas", "error handling"],
    "Java": ["OOP", "collections", "streams", "Spring Boot", "JPA", "JVM memory", "concurrency", "REST APIs", "testing", "exceptions"],
    "SQL": ["joins", "indexes", "normalization", "query plans", "window functions", "transactions", "stored procedures", "constraints", "ETL", "performance tuning"],
    "JavaScript": ["closures", "promises", "event loop", "DOM APIs", "modules", "fetch", "error handling", "state", "testing", "performance"],
    "HTML": ["semantic tags", "forms", "accessibility", "metadata", "tables", "SEO basics", "media", "landmarks", "validation", "responsive structure"],
    "CSS": ["flexbox", "grid", "specificity", "responsive design", "animation", "variables", "positioning", "accessibility", "performance", "architecture"],
    "React": ["components", "hooks", "state management", "effects", "forms", "routing", "performance", "testing", "accessibility", "API integration"],
    "Flask": ["routing", "blueprints", "request handling", "Jinja", "SQLAlchemy", "auth", "testing", "deployment", "security", "REST APIs"],
    "Full Stack Developer": ["REST design", "frontend state", "database schema", "authentication", "deployment", "API contracts", "performance", "testing", "caching", "responsive UI"],
    "Frontend Developer": ["HTML semantics", "CSS layout", "JavaScript", "React state", "accessibility", "performance", "forms", "testing", "responsive design", "browser APIs"],
    "Backend Developer": ["API design", "database indexing", "queues", "caching", "auth", "observability", "transactions", "scaling", "testing", "deployment"],
    "Software Engineer": ["data structures", "algorithms", "system design", "testing", "clean code", "debugging", "version control", "requirements", "performance", "design patterns"],
    "Data Analyst": ["SQL joins", "Excel", "dashboards", "statistics", "data cleaning", "Power BI", "Tableau", "KPIs", "stakeholder reporting", "A/B analysis"],
    "Data Scientist": ["feature engineering", "model validation", "statistics", "Python ML", "classification", "regression", "clustering", "experiments", "bias", "deployment"],
    "AI": ["LLM evaluation", "prompt design", "embeddings", "RAG", "model safety", "fine tuning", "agents", "vector databases", "latency", "human review"],
    "Machine Learning": ["feature engineering", "model validation", "classification", "regression", "clustering", "cross validation", "bias", "metrics", "deployment", "monitoring"],
    "AI / ML Engineer": ["model serving", "LLMs", "embeddings", "MLOps", "evaluation", "fine tuning", "feature stores", "vector databases", "monitoring", "prompt design"],
    "Cyber Security": ["OWASP", "network security", "incident response", "SIEM", "threat modeling", "IAM", "vulnerability scanning", "encryption", "risk", "forensics"],
    "Cloud": ["AWS", "Azure", "containers", "Kubernetes", "serverless", "CI/CD", "networking", "monitoring", "cost optimization", "resilience"],
    "HR Interview": ["self introduction", "motivation", "strengths", "weaknesses", "conflict", "priorities", "adaptability", "career goals", "feedback", "culture fit"],
    "Behavioral Interview": ["ownership", "conflict", "ambiguity", "leadership", "failure", "learning", "deadline pressure", "teamwork", "communication", "decision making"],
    "Communication Skills": ["clarity", "listening", "presentation", "stakeholder updates", "written communication", "feedback", "negotiation", "storytelling", "meetings", "conflict"],
}

DIFFICULTIES = ["Easy", "Medium", "Hard"]
EXPERIENCE_LEVELS = ["Fresher", "1-2 Years", "3-5 Years", "5+ Years"]


def _resolve_category(value, interview_type="Technical"):
    text = f"{value or ''} {interview_type or ''}".lower()
    for key, category in ROLE_ALIASES.items():
        if key in text:
            return category
    return "Software Engineer"


def _question_templates(category):
    if category == "HR Interview":
        return [
            "How would you answer an HR interviewer asking about {topic}?",
            "Tell me about your {topic} in a professional setting.",
            "What example would you give to demonstrate {topic}?",
            "How do you improve your {topic} over time?",
            "Why does {topic} matter for the role you are applying for?",
        ]
    if category == "Behavioral Interview":
        return [
            "Describe a time you demonstrated {topic}.",
            "Tell me about a situation where {topic} changed the outcome.",
            "Give an example of handling {topic} under pressure.",
            "What did you learn from a past experience involving {topic}?",
            "How would you use STAR format to explain {topic}?",
        ]
    if category == "Communication Skills":
        return [
            "How would you communicate a complex update involving {topic}?",
            "Describe how you use {topic} when working with stakeholders.",
            "What steps help you improve {topic} in a team environment?",
            "Give an example where strong {topic} prevented confusion.",
            "How would you adapt your {topic} for a non-technical audience?",
        ]
    return [
        "In a real {category} interview, how would you explain {topic} to someone reviewing your project experience?",
        "A production issue appears in a module that uses {topic}. What would you inspect first, and why?",
        "What is one common mistake candidates make with {topic}, and how would you avoid it in code or design?",
        "Describe a project decision where {topic} affected performance, reliability, or maintainability.",
        "If an interviewer asked for a follow-up on {topic}, what edge cases, tests, or tradeoffs would you discuss?",
    ]


def _expected_answer(category, topic):
    if category in {"HR Interview", "Behavioral Interview", "Communication Skills"}:
        return f"A strong answer uses a clear example, explains the action taken, reflects on the result, and connects {topic} to the target role."
    return f"A strong answer defines {topic}, explains the reasoning or tradeoffs, gives a concrete implementation example, and mentions testing, reliability, and impact."


def _seed_interview_rows(conn):
    existing = conn.execute("SELECT COUNT(*) AS total FROM question_bank").fetchone()["total"]
    if existing >= len(QUESTION_CATEGORIES) * 100:
        return
    conn.execute("DELETE FROM question_bank")
    rows = []
    for category in QUESTION_CATEGORIES:
        if category in APTITUDE_CATEGORIES:
            continue
        topics = ROLE_TOPICS.get(category, ROLE_TOPICS["Software Engineer"])
        templates = _question_templates(category)
        counter = 0
        for topic in topics:
            for template in templates:
                for experience in EXPERIENCE_LEVELS[:2]:
                    counter += 1
                    rows.append(
                        (
                            template.format(topic=topic, category=category),
                            DIFFICULTIES[counter % len(DIFFICULTIES)],
                            _expected_answer(category, topic),
                            json.dumps([category, topic, "STAR", "examples", "impact"]),
                            category,
                            topic,
                            experience,
                        )
                    )
                    if counter >= 100:
                        break
                if counter >= 100:
                    break
            if counter >= 100:
                break
    conn.executemany(
        """
        INSERT INTO question_bank (
            question, difficulty, expected_answer, keywords, category, topic, experience_level
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def _aptitude_item(category, index):
    difficulty = DIFFICULTIES[index % len(DIFFICULTIES)]
    company_levels = ["TCS", "Infosys", "Accenture", "Capgemini", "Cognizant", "Wipro", "IBM", "Deloitte"]
    company_level = company_levels[index % len(company_levels)]
    time_limit = 45 + (index % 4) * 15
    if category == "Quantitative Aptitude":
        topics = ["Percentages", "Profit & Loss", "Time & Work", "Probability", "Averages", "Ratio", "Permutation", "Combination"]
        topic = topics[index % len(topics)]
        n = index + 12
        if topic == "Percentages":
            question = f"A value of {n * 40} is increased by {10 + index % 15}% and then reduced by {5 + index % 10}%. Which expression gives the final value?"
            options = {"A": f"{n * 40} x {(110 + index % 15) / 100:.2f} x {(95 - index % 10) / 100:.2f}", "B": f"{n * 40} + {15 + index % 10}", "C": f"{n * 40} x {(100 - index % 10) / 100:.2f}", "D": f"{n * 40} / {(105 + index % 15) / 100:.2f}"}
            answer = "A"
            explanation = "Successive percentage changes are applied multiplicatively, not by simple addition."
        elif topic == "Profit & Loss":
            cp = 200 + index * 4
            pct = 8 + index % 12
            question = f"A product costs Rs. {cp} and is sold at a profit of {pct}%. What is the selling price?"
            sp = round(cp * (100 + pct) / 100, 2)
            options = {"A": f"Rs. {round(cp * pct / 100, 2)}", "B": f"Rs. {sp}", "C": f"Rs. {cp - pct}", "D": f"Rs. {cp + pct}"}
            answer = "B"
            explanation = "Selling price equals cost price multiplied by (100 + profit percentage) / 100."
        elif topic == "Time & Work":
            a = 6 + index % 8
            b = a + 4
            question = f"A can finish a task in {a} days and B can finish it in {b} days. How much work do they complete together in one day?"
            options = {"A": f"1/{a + b}", "B": f"{a + b}/{a * b}", "C": f"{a * b}/{a + b}", "D": f"1/{abs(b - a)}"}
            answer = "B"
            explanation = "Combined one-day work is the sum of individual rates: 1/A + 1/B."
        elif topic == "Probability":
            red = 3 + index % 5
            blue = 4 + index % 6
            question = f"A bag has {red} red and {blue} blue balls. What is the probability of drawing a red ball?"
            options = {"A": f"{red}/{red + blue}", "B": f"{blue}/{red + blue}", "C": f"{red}/{blue}", "D": f"{blue}/{red}"}
            answer = "A"
            explanation = "Probability is favorable outcomes divided by total outcomes."
        elif topic == "Averages":
            avg = 45 + index % 20
            count = 5 + index % 5
            new_score = avg + 10
            question = f"The average score of {count} students is {avg}. If one more student with score {new_score} joins, what expression gives the new average?"
            options = {"A": f"({avg} + {new_score}) / 2", "B": f"({avg} x {count} + {new_score}) / {count + 1}", "C": f"{avg} + {new_score} / {count}", "D": f"{new_score} - {avg}"}
            answer = "B"
            explanation = "Convert average to total, add the new value, then divide by the new count."
        elif topic == "Ratio":
            a = 2 + index % 5
            b = a + 3
            total = (a + b) * (6 + index % 4)
            question = f"A sum of Rs. {total} is divided in the ratio {a}:{b}. What is the larger share?"
            options = {"A": f"Rs. {total * a // (a + b)}", "B": f"Rs. {total * b // (a + b)}", "C": f"Rs. {total // b}", "D": f"Rs. {total // a}"}
            answer = "B"
            explanation = "The larger share is total multiplied by the larger ratio part over the sum of ratio parts."
        elif topic == "Permutation":
            letters = 5 + index % 4
            question = f"How many ways can {letters} different candidates be arranged in a row?"
            options = {"A": str(letters * letters), "B": f"{letters}!", "C": str(letters + letters), "D": str(letters * (letters - 1))}
            answer = "B"
            explanation = "Arranging all distinct objects in a row is a factorial permutation."
        else:
            n = 6 + index % 5
            r = 2 + index % 3
            question = f"Which formula gives the number of ways to choose {r} members from {n} candidates?"
            options = {"A": f"{n}P{r}", "B": f"{n}C{r}", "C": f"{n} + {r}", "D": f"{n} x {r}"}
            answer = "B"
            explanation = "Choosing without order uses combinations, nCr."
    elif category == "Logical Reasoning":
        topics = ["Number Series", "Blood Relations", "Directions", "Clock", "Calendar", "Coding Logic", "Data Sufficiency"]
        topic = topics[index % len(topics)]
        if topic == "Number Series":
            start = index + 2
            question = f"Find the next term: {start}, {start + 2}, {start + 6}, {start + 12}, ?"
            options = {"A": str(start + 16), "B": str(start + 20), "C": str(start + 22), "D": str(start + 24)}
            answer = "B"
            explanation = "The differences are +2, +4, +6, so the next difference is +8."
        elif topic == "Blood Relations":
            question = "Pointing to a woman, Ravi says, 'She is the daughter of my mother's only son.' How is the woman related to Ravi?"
            options = {"A": "Sister", "B": "Daughter", "C": "Mother", "D": "Aunt"}
            answer = "B"
            explanation = "Ravi's mother's only son is Ravi, so the woman is Ravi's daughter."
        elif topic == "Directions":
            question = f"A person walks {5 + index % 4} km north, turns right and walks {3 + index % 5} km, then turns right again. Which direction is the person facing?"
            options = {"A": "North", "B": "East", "C": "South", "D": "West"}
            answer = "C"
            explanation = "North, right to east, and right again means facing south."
        elif topic == "Clock":
            question = "At 3:30, what is the angle between the hour hand and the minute hand?"
            options = {"A": "75 degrees", "B": "90 degrees", "C": "60 degrees", "D": "105 degrees"}
            answer = "A"
            explanation = "Minute hand is at 180 degrees; hour hand is at 105 degrees, so the angle is 75 degrees."
        elif topic == "Calendar":
            question = "If today is Monday, what day will it be after 45 days?"
            options = {"A": "Wednesday", "B": "Thursday", "C": "Friday", "D": "Saturday"}
            answer = "A"
            explanation = "45 mod 7 is 3, so three days after Monday is Wednesday."
        elif topic == "Coding Logic":
            question = "If CODE is written as DQGI by shifting letters +1, +2, +3, +4, how is TEST encoded with the same rule?"
            options = {"A": "UGVX", "B": "UHVX", "C": "VGUW", "D": "SFRS"}
            answer = "A"
            explanation = "Apply increasing shifts to each letter: T+1, E+2, S+3, T+4."
        else:
            question = "Statement: All analysts use SQL. Some SQL users build dashboards. Which conclusion definitely follows?"
            options = {"A": "All analysts build dashboards", "B": "Some dashboard builders are analysts", "C": "All analysts use SQL", "D": "No SQL users are analysts"}
            answer = "C"
            explanation = "Only the original universal statement is definitely guaranteed."
    elif category == "Verbal Ability":
        topics = ["Synonyms", "Antonyms", "Grammar", "Error Detection", "Sentence Rearrangement", "Reading Comprehension"]
        topic = topics[index % len(topics)]
        word = ["precise", "expand", "reluctant", "brief", "robust", "concise"][index % 6]
        question = f"Choose the best {topic.lower()} option for '{word}' in a professional sentence."
        verbal_options = {
            "precise": ("accurate", "careless", "ordinary", "late"),
            "expand": ("increase", "hide", "refuse", "weaken"),
            "reluctant": ("hesitant", "certain", "eager", "simple"),
            "brief": ("short", "complex", "angry", "formal"),
            "robust": ("strong", "fragile", "unclear", "minor"),
            "concise": ("brief", "lengthy", "uncertain", "incorrect"),
        }
        vals = verbal_options[word]
        options = {"A": vals[1], "B": vals[0], "C": vals[2], "D": vals[3]}
        answer = "B"
        explanation = f"In this context, '{word}' is closest to '{vals[0]}'."
    elif category == "Data Interpretation":
        topic = "Data Interpretation"
        base = 100 + index * 3
        question = f"A report shows sales of {base}, {base + 20}, and {base + 50} units over three quarters. What is the average quarterly sale?"
        avg = round((base + base + 20 + base + 50) / 3, 2)
        options = {"A": str(base + 20), "B": str(avg), "C": str(base + 50), "D": str(base)}
        answer = "B"
        explanation = "Average is total sales divided by the number of quarters."
    elif category == "Analytical Reasoning":
        topic = ["Puzzle", "Statement Based", "Data Sufficiency"][index % 3]
        question = f"Four candidates A, B, C, and D are interviewed. A is before B, C is after B, and D is before A. Who is interviewed first?"
        options = {"A": "A", "B": "B", "C": "C", "D": "D"}
        answer = "D"
        explanation = "The order constraints give D before A before B before C."
    else:
        source = ["Quantitative Aptitude", "Logical Reasoning", "Verbal Ability", "Data Interpretation", "Analytical Reasoning"][index % 5]
        item = _aptitude_item(source, index)
        item["category"] = "Mixed Aptitude"
        return item
    return {
        "category": category,
        "difficulty": difficulty,
        "question": question,
        "option_a": options["A"],
        "option_b": options["B"],
        "option_c": options["C"],
        "option_d": options["D"],
        "correct_answer": answer,
        "explanation": explanation,
        "topic": topic,
        "company_level": company_level,
        "time_limit": time_limit,
        "question_type": "MCQ" if index % 5 else "Statement Based",
    }


def _seed_aptitude_rows(conn):
    existing = conn.execute("SELECT COUNT(*) AS total FROM aptitude_question_bank").fetchone()["total"]
    if existing >= len(APTITUDE_CATEGORIES) * 100:
        return
    conn.execute("DELETE FROM aptitude_question_bank")
    rows = []
    for category in sorted(APTITUDE_CATEGORIES):
        for index in range(1, 101):
            item = _aptitude_item(category, index)
            rows.append(
                (
                    item["question"],
                    item["option_a"],
                    item["option_b"],
                    item["option_c"],
                    item["option_d"],
                    item["correct_answer"],
                    item["explanation"],
                    item["difficulty"],
                    item["category"],
                    item["topic"],
                    item["company_level"],
                    item["time_limit"],
                    item["question_type"],
                )
            )
    conn.executemany(
        """
        INSERT INTO aptitude_question_bank (
            question, option_a, option_b, option_c, option_d, correct_answer,
            explanation, difficulty, category, topic, company_level, time_limit, question_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def seed_question_bank():
    with get_connection() as conn:
        _seed_interview_rows(conn)
        _seed_aptitude_rows(conn)


def get_interview_questions(setup):
    category = _resolve_category(setup.get("job_role"), setup.get("interview_type"))
    interview_type = str(setup.get("interview_type") or "").lower()
    if "hr" in interview_type:
        category = "HR Interview"
    elif "behavioral" in interview_type:
        category = "Behavioral Interview"
    elif "communication" in interview_type:
        category = "Communication Skills"
    difficulty = str(setup.get("difficulty") or "Medium").strip()
    experience = str(setup.get("experience_level") or "").strip()
    count = max(1, min(int(setup.get("question_count") or 5), 20))
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, question, difficulty, expected_answer, keywords, category, topic, experience_level
            FROM question_bank
            WHERE category = ?
              AND (? = '' OR difficulty = ?)
              AND (? = '' OR experience_level = ?)
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (category, difficulty, difficulty, experience, experience, count),
        ).fetchall()
        if len(rows) < count:
            rows = conn.execute(
                """
                SELECT id, question, difficulty, expected_answer, keywords, category, topic, experience_level
                FROM question_bank
                WHERE category = ?
                ORDER BY RANDOM()
                LIMIT ?
                """,
                (category, count),
            ).fetchall()
    selected = [dict(row) for row in rows]
    random.shuffle(selected)
    return [
        {
            "id": item["id"],
            "question_number": index,
            "question": item["question"],
            "difficulty": item["difficulty"],
            "type": setup.get("interview_type") or "Technical",
            "expected_answer": item["expected_answer"],
            "expected_skills": json.loads(item["keywords"] or "[]")[:6],
            "keywords": json.loads(item["keywords"] or "[]"),
            "category": item["category"],
            "topic": item["topic"],
            "experience_level": item["experience_level"],
            "competency": item["topic"],
            "intent": "Question selected from the local SQLite question bank.",
            "offline": True,
        }
        for index, item in enumerate(selected, start=1)
    ]


def get_aptitude_questions(setup):
    category = _resolve_category(setup.get("category"), "aptitude")
    if category not in APTITUDE_CATEGORIES:
        category = "Mixed Aptitude"
    difficulty = str(setup.get("difficulty") or "Medium").strip()
    count = max(1, min(int(setup.get("question_count") or 10), 30))
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, question, option_a, option_b, option_c, option_d, correct_answer,
                   explanation, difficulty, category, topic, company_level, time_limit, question_type
            FROM aptitude_question_bank
            WHERE category = ?
              AND (? = '' OR difficulty = ?)
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (category, difficulty, difficulty, count),
        ).fetchall()
        if len(rows) < count:
            rows = conn.execute(
                """
                SELECT id, question, option_a, option_b, option_c, option_d, correct_answer,
                       explanation, difficulty, category, topic, company_level, time_limit, question_type
                FROM aptitude_question_bank
                WHERE category = ?
                ORDER BY RANDOM()
                LIMIT ?
                """,
                (category, count),
            ).fetchall()
    return [
        {
            "id": row["id"],
            "question_number": index,
            "category": row["category"],
            "question": row["question"],
            "options": {"A": row["option_a"], "B": row["option_b"], "C": row["option_c"], "D": row["option_d"]},
            "correct_answer": row["correct_answer"],
            "explanation": row["explanation"],
            "difficulty": row["difficulty"],
            "topic": row["topic"] or row["category"],
            "company_level": row["company_level"] or "Placement Level",
            "time_limit": row["time_limit"] or 60,
            "question_type": row["question_type"] or "MCQ",
        }
        for index, row in enumerate(rows, start=1)
    ]
