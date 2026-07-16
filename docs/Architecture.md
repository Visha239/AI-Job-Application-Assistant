# CareerPilot Architecture

## Entry point

`dashboard.py` is the Streamlit home dashboard.

## Application layers

### Pages

The `pages/` folder contains Streamlit workflows such as Job Search, Application Copilot, Recruiter Outreach, Auto Apply Assistant, Application CRM, Career Coach, Resume Intelligence, and One-Click Optimizer.

### Services

The `app/services/` folder contains business logic. Streamlit pages should call service functions rather than embedding storage, ranking, ATS, or resume-generation logic directly.

### Utilities

The `app/utils/` folder contains shared helpers and configuration loading.

### Data

The `data/` folder contains the user profile and private runtime state. Private runtime JSON files are excluded from Git.

### Exports

Generated resumes, reports, queue exports, CRM exports, and regression reports are stored below `exports/` and excluded from Git.

## State flow

Selected Job → Application Context → JD Capture → ATS/Resume Intelligence → Application Package → Queue/CRM/Outreach → Dashboard

## Production-readiness commands

- `python -m scripts.project_health_check`
- `python run_all_tests.py`
- `python -m scripts.cleanup_project`
