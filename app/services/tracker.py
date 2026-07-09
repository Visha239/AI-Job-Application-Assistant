from app.database.database import database


def save_application(company, role, location, job_link, status, notes):
    database.add_application(
        company=company,
        role=role,
        location=location,
        job_link=job_link,
        status=status,
        notes=notes
    )


def get_all_applications():
    return database.get_applications()


def get_total_applications():
    return database.get_application_count()