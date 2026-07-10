from app.services.resume_optimizer import ResumeOptimizer

job_description = """
We are hiring a Data Analyst with experience in SQL, Python, Excel, Power BI,
DAX, Power Query, dashboards, KPI reporting, ETL, and data visualization.
"""

optimizer = ResumeOptimizer()

result = optimizer.optimize_resume(
    role_type="Data Analyst",
    job_description=job_description
)

print("Optimized Resume:", result["output_path"])
print("Keywords Found:", result["keywords"])
print("New Objective:", result["objective"])