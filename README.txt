
CAREERPILOT SMART JOB DISCOVERY - INTEGRATED SPRINT

1. Copy install_smart_job_discovery.ps1 into:
   C:\Users\birad\AI-Job-Application-Assistant

2. In PowerShell, from the project root, run:

   Set-ExecutionPolicy -Scope Process Bypass
   .\install_smart_job_discovery.ps1

3. Run the integration test:

   .\venv\Scripts\python.exe -m tests.smart_job_discovery_integration_test

Expected ending:

   SMART JOB DISCOVERY INTEGRATION TEST PASSED

4. Run the existing feature test:

   .\venv\Scripts\python.exe -m tests.job_search_feature_pack_test

5. Launch CareerPilot:

   .\venv\Scripts\python.exe -m streamlit run dashboard.py

6. Open Job Search. Start with:
   - Custom role: Data Analyst
   - Posted within: 3 days
   - Minimum score: 45
   - Exclude senior roles: enabled

Security:
Your previous project ZIP included .env. Revoke that Gmail App Password,
create a new one, and update only your local .env.
