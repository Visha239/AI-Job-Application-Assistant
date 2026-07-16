# CareerPilot AI

CareerPilot AI is a local Streamlit application that helps organize the job-search workflow from discovery to application tracking.

## Main capabilities

- Fresh job discovery and ranking
- Automatic job-description capture
- ATS and skill-gap analysis
- Truthful DOCX resume tailoring
- Application package generation
- Recruiter outreach drafts and follow-up tracking
- Auto-apply queue for manually reviewed applications
- Application CRM and pipeline analytics
- Career dashboard and practical daily recommendations

CareerPilot does not automatically submit applications and does not invent resume skills, achievements, or hiring probabilities.

## Quick start

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run dashboard.py
```

## Daily use

1. Open **Job Search** and rank fresh jobs.
2. Select a strong job and capture the complete JD.
3. Use **One-Click Optimizer** or **Resume Intelligence**.
4. Review the generated resume and application package.
5. Open the official job page and apply manually.
6. Record the result in **Application CRM**.
7. Use **Recruiter Outreach** and complete follow-ups.
8. Monitor progress from the dashboard.

## Project verification

Run the health check:

```powershell
.\venv\Scripts\python.exe -m scripts.project_health_check
```

Run the stable regression suite:

```powershell
.\venv\Scripts\python.exe run_all_tests.py
```

Run cleanup in preview mode:

```powershell
.\venv\Scripts\python.exe -m scripts.cleanup_project
```

After reviewing the list, apply cleanup:

```powershell
.\venv\Scripts\python.exe -m scripts.cleanup_project --apply
```

## Privacy

Do not commit:

- `.env`
- local databases
- application queue and CRM data
- recruiter records
- uploaded resumes
- generated resumes and reports

The supplied `.gitignore` covers these paths.
