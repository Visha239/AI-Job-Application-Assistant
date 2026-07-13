# CareerPilot Smart Job Discovery Feature Pack

Copy the contents of this pack into the root of your existing repository.

## Test

```powershell
.\venv\Scripts\python.exe -m tests.job_search_feature_pack_test
```

Expected ending: `FEATURE PACK TEST PASSED`.

The old imports remain compatible:
- `from app.services.job_search import search_jobs`
- `from app.services.job_ranker import rank_jobs`

The next pack will replace the Streamlit Job Search page so it displays freshness and urgency.
