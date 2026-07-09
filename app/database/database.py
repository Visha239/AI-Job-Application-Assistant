import sqlite3
from pathlib import Path
from app.database.models import DATABASE_TABLES

DB_PATH = Path("app/database/careerpilot.db")


class Database:

    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def initialize_database(self):
        """
        Create all database tables.
        """
        for table_sql in DATABASE_TABLES.values():
            self.cursor.execute(table_sql)

        self.connection.commit()

    ####################################################
    # Generic Functions
    ####################################################

    def execute(self, query, params=()):
        self.cursor.execute(query, params)
        self.connection.commit()

    def fetchall(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def fetchone(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    ####################################################
    # Applications
    ####################################################

    def add_application(
        self,
        company,
        role,
        location,
        job_link,
        status,
        notes
    ):

        self.execute(
            """
            INSERT INTO applications
            (
                company,
                role,
                location,
                job_link,
                status,
                notes
            )

            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                company,
                role,
                location,
                job_link,
                status,
                notes
            )
        )

    def get_applications(self):

        return self.fetchall(
            """
            SELECT *

            FROM applications

            ORDER BY id DESC
            """
        )

    def get_application_count(self):

        row = self.fetchone(
            """
            SELECT COUNT(*) AS total

            FROM applications
            """
        )

        return row["total"]

    ####################################################
    # Jobs
    ####################################################

    def add_job(
        self,
        company,
        role,
        location,
        job_link,
        source,
        required_skills,
        match_score
    ):

        self.execute(
            """
            INSERT INTO jobs
            (
                company,
                role,
                location,
                job_link,
                source,
                required_skills,
                match_score
            )

            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company,
                role,
                location,
                job_link,
                source,
                required_skills,
                match_score
            )
        )

    def get_jobs(self):

        return self.fetchall(
            """
            SELECT *

            FROM jobs

            ORDER BY match_score DESC
            """
        )

    ####################################################
    # Recruiters
    ####################################################

    def add_recruiter(
        self,
        company,
        name,
        email,
        linkedin,
        notes
    ):

        self.execute(
            """
            INSERT INTO recruiters
            (
                company,
                name,
                email,
                linkedin,
                notes
            )

            VALUES (?, ?, ?, ?, ?)
            """,
            (
                company,
                name,
                email,
                linkedin,
                notes
            )
        )

    def get_recruiters(self):

        return self.fetchall(
            """
            SELECT *

            FROM recruiters
            """
        )

    ####################################################
    # Resume Manager
    ####################################################

    def add_resume(
        self,
        resume_name,
        role_type,
        file_path,
        ats_score
    ):

        self.execute(
            """
            INSERT INTO resumes
            (
                resume_name,
                role_type,
                file_path,
                ats_score
            )

            VALUES (?, ?, ?, ?)
            """,
            (
                resume_name,
                role_type,
                file_path,
                ats_score
            )
        )

    def get_resumes(self):

        return self.fetchall(
            """
            SELECT *

            FROM resumes

            ORDER BY ats_score DESC
            """
        )


database = Database()
database.initialize_database()