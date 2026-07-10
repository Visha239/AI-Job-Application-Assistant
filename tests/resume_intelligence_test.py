from app.services.resume_report import ResumeReport

jd = """

We are hiring a Data Analyst.

Required Skills

SQL

Python

Excel

Power BI

Power Query

Dashboard

Reporting

KPI

Data Visualization

ETL

Snowflake

Spark

"""

report = ResumeReport().generate(jd)

print("=" * 60)

print("CAREERPILOT RESUME REPORT")

print("=" * 60)

print()

print("ATS SCORE")

print(report["ats_score"])

print()

print("MATCHED")

for i in report["matched"]:

    print("✔", i)

print()

print("EMPHASIZE")

for i in report["emphasize"]:

    print("➕", i)

print()

print("MISSING")

for i in report["missing"]:

    print("✘", i)

print()

print("SECTIONS")

for i in report["improve"]:

    print("•", i)