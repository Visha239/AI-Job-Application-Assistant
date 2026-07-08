import json
import streamlit as st

from app.services.ats import analyze_ats
from app.services.matcher import match_job
from app.services.recruiter import generate_email
from app.services.tracker import save_application, count_applications
from app.services.career_coach import get_career_advice
from app.services.resume_builder import generate_resume_summary, generate_project_bullets

st.set_page_config(page_title="CareerPilot AI", layout="wide")

with open("data/profile.json", "r") as file:
    profile = json.load(file)

st.title("CareerPilot AI")
st.subheader("Free AI Job Application Assistant")

menu = st.sidebar.selectbox(
    "Choose Feature",
    [
        "Dashboard",
        "ATS Resume Intelligence",
        "Job Matcher",
        "Recruiter Email",
        "Application Tracker",
        "Career Coach"
    ]
)

if menu == "Dashboard":
    st.header(f"Welcome, {profile['name']}")

    applications_count = count_applications()

    col1, col2, col3 = st.columns(3)
    col1.metric("Applications Tracked", applications_count)
    col2.metric("Strong Matches", "Coming Soon")
    col3.metric("Interviews", "Coming Soon")

    st.info(get_career_advice(applications_count))

elif menu == "ATS Resume Intelligence":
    st.header("ATS Resume Intelligence")

    jd = st.text_area("Paste Job Description", height=300)

    if st.button("Analyze ATS"):
        result = analyze_ats(jd)

        st.metric("ATS Keyword Score", f"{result['score']}%")

        st.subheader("Keywords Found")
        st.write(result["found_keywords"])

        st.subheader("Keywords You Can Add If Truthful")
        st.write(result["missing_keywords"][:10])

        st.subheader("Suggested Resume Summary")
        st.write(generate_resume_summary(profile))

        st.subheader("Suggested Project Bullets")
        for bullet in generate_project_bullets():
            st.write("• " + bullet)

elif menu == "Job Matcher":
    st.header("Job Matcher")

    role_type = st.selectbox("Select Role Type", ["Data Analyst", "Business Analyst", "Support Engineer"])
    jd = st.text_area("Paste Job Description", height=300)

    if st.button("Match Job"):
        result = match_job(jd, role_type)

        st.metric("Match Score", f"{result['score']}%")

        st.subheader("Matched Skills")
        st.write(result["matched"])

        st.subheader("Missing Skills")
        st.write(result["missing"])

        st.success(result["recommendation"])

elif menu == "Recruiter Email":
    st.header("Recruiter Email Generator")

    company = st.text_input("Company Name")
    role = st.text_input("Job Role")

    if st.button("Generate Email"):
        email = generate_email(profile, company, role)
        st.text_area("Email Draft", email, height=350)

elif menu == "Application Tracker":
    st.header("Application Tracker")

    company = st.text_input("Company")
    role = st.text_input("Role")
    location = st.text_input("Location")
    job_link = st.text_input("Job Link")
    status = st.selectbox("Status", ["Not Applied", "Applied", "Interview", "Rejected", "Offer"])
    notes = st.text_area("Notes")

    if st.button("Save Application"):
        save_application(company, role, location, job_link, status, notes)
        st.success("Application saved successfully.")

elif menu == "Career Coach":
    st.header("AI Career Coach")

    applications_count = count_applications()

    st.metric("Total Applications", applications_count)
    st.write(get_career_advice(applications_count))

    st.subheader("Today’s Focus")
    st.write("1. Apply to strong-match jobs.")
    st.write("2. Tailor your resume before applying.")
    st.write("3. Send recruiter messages for important companies.")