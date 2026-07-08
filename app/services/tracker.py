from app.database.database import add_application, get_applications, count_applications

def save_application(company, role, location, job_link, status, notes):
    add_application(company, role, location, job_link, status, notes)

def get_all_applications():
    return get_applications()

def get_total_applications():
    return count_applications()