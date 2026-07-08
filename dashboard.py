import json
import re
import streamlit as st

st.set_page_config(page_title="CareerPilot AI", layout="wide")

with open("data/profile.json", "r") as file:
    profile = json.load(file)

important_keywords = [
    "SQL", "Python", "Excel", "Power BI", "Tableau", "Data Analysis",
    "Business Analysis", "Requirements Gathering", "Documentation",
    "Dashboard", "Reporting", "KPI", "DAX", "Power Query",
    "ETL", "Data Visualization", "Stakeholder", "UML",
    "Gap Analysis", "Jira", "ServiceNow", "Linux"
]

st.title("CareerPilot AI")
st.subheader("AI Job Application Assistant")

menu = st.sidebar.selectbox(
    "Choose Feature",
    [
        "Dashboard",
        "ATS Resume Tailor",
        "Recruiter Email"
    ]
)

if menu == "Dashboard":
    st.header(f"Welcome, {profile['name']}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Applications Tracked", "0")
    col2.metric("Strong Matches", "0")
    col3.metric("Interviews", "0")

elif menu == "ATS Resume Tailor":
    st.header("ATS Resume Tailor")

    jd = st.text_area("Paste Job Description", height=300)

    if st.button("Analyze ATS Match"):
        found_keywords = []
        missing_keywords = []

        for keyword in important_keywords:
            pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
            if re.search(pattern, jd.lower()):
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)

        ats_score = round((len(found_keywords) / len(important_keywords)) * 100, 2)

        st.metric("ATS Keyword Score", f"{ats_score}%")

        st.subheader("Keywords Found")
        st.write(found_keywords)

        st.subheader("Keywords You Can Add If Truthful")
        st.write(missing_keywords[:8])

        st.subheader("Suggested Resume Summary")
        st.write(
            f"Data-focused professional with {profile['experience_years']} years of experience "
            f"in SQL, Python, Excel, Power BI, Tableau, reporting, dashboards, and business analysis. "
            f"Experienced in analyzing data, creating actionable insights, and supporting business decision-making "
            f"through data visualization and structured reporting."
        )

elif menu == "Recruiter Email":
    st.header("Recruiter Email Generator")

    company = st.text_input("Company Name")
    role = st.text_input("Job Role")

    if st.button("Generate Email"):
        email = f"""Subject: Application for {role} Role

Dear Hiring Team,

I hope you are doing well.

My name is {profile['name']}. I am interested in the {role} role at {company}.

I have experience in SQL, Python, Power BI, Excel, Tableau, and Data Analysis.

Please find my resume attached for your reference.

Best regards,
{profile['name']}
{profile['email']}
"""
        st.text_area("Email Draft", email, height=300)