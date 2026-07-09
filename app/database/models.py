DATABASE_TABLES = {
    "applications": """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            location TEXT,
            job_link TEXT,
            status TEXT,
            notes TEXT,
            applied_date TEXT DEFAULT CURRENT_DATE
        )
    """,

    "jobs": """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            location TEXT,
            job_link TEXT,
            source TEXT,
            required_skills TEXT,
            match_score REAL,
            status TEXT DEFAULT 'Saved',
            created_date TEXT DEFAULT CURRENT_DATE
        )
    """,

    "recruiters": """
        CREATE TABLE IF NOT EXISTS recruiters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            name TEXT,
            email TEXT,
            linkedin TEXT,
            notes TEXT
        )
    """,

    "resumes": """
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_name TEXT NOT NULL,
            role_type TEXT,
            file_path TEXT,
            ats_score REAL,
            created_date TEXT DEFAULT CURRENT_DATE
        )
    """
}