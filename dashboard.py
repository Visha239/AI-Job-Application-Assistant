import json
import streamlit as st
import pandas as pd

from app.services.ats import analyze_ats
from app.services.matcher import match_job
from app.services.recruiter import generate_email
from app.services.tracker import save_application, get_all_applications, get_total_applications
from app.services.career_coach import get_career_advice
from app.services.resume_builder import generate_resume
from app.services.resume_intelligence import analyze_resume_intelligence
from app.utils.config_loader import get_role_names
from app.utils.pdf import generate_resume_pdf

st.set_page_config(page_title="CareerPilot AI", layout="wide")

with open("data/profile.json", "r") as file:
    profile = json.load(file)

st.title("CareerPilot AI")
st.subheader("Free AI Job Application Assistant")

menu = st.sidebar.selectbox(
    "Choose Feature",
    [
        "Dashboard",
        "Resume Intelligence v2",
        "Resume Builder",
        "ATS Resume Intelligence",
        "Job Matcher",
        "Recruiter Email",
        "Application Tracker",
        "Career Coach"
    ]
)

if menu == "Dashboard":
    st.header(f"Welcome, {profile['name']}")
    total_applications = get_total_applications()

    col1, col2, col3 = st.columns(3)
    col1.metric("Applications Tracked", total_applications)
    col2.metric("Strong Matches", "Coming Soon")
    col3.metric("Interviews", "Coming Soon")

    st.info(get_career_advice(total_applications))

elif menu == "Resume Intelligence v2":
    st.header("Resume Intelligence v2")

    role_type = st.selectbox("Select Target Role", get_role_names())
    jd = st.text_area("Paste Job Description", height=300)

    if st.button("Analyze Resume Fit"):
        result = analyze_resume_intelligence(jd, role_type)

        col1, col2 = st.columns(2)
        col1.metric("Current Resume Score", f"{result['current_score']}%")
        col2.metric("Expected Score After Tailoring", f"{result['expected_score']}%")

        st.subheader("Strengths")
        st.write(result["matched_skills"])

        st.subheader("Missing Skills / Keywords")
        st.write(result["missing_skills"])

        st.subheader("Recommended Resume Version")
        st.success(result["resume_version"])

        st.subheader("Recommended Projects to Highlight")
        for project in result["recommended_projects"]:
            st.write("• " + project)

        st.subheader("Recommendation")
        st.success(result["recommendation"])

elif menu == "Resume Builder":
    st.header("Resume Builder")

    role_type = st.selectbox("Select Resume Type", get_role_names())
    jd = st.text_area("Paste Job Description for Tailoring", height=250)

    if st.button("Generate Tailored Resume"):
        intelligence = analyze_resume_intelligence(jd, role_type)
        resume = generate_resume(profile, role_type, intelligence["missing_skills"])

        st.subheader("Resume Preview")

        st.markdown(f"## {resume['name']}")
        st.write(resume["email"])

        st.markdown("### Professional Summary")
        st.write(resume["summary"])

        st.markdown("### Skills")
        st.write(", ".join(resume["skills"]))

        st.markdown("### Projects")
        for project in resume["projects"]:
            st.write("• " + project)

        st.markdown("### Experience")
        for exp in resume["experience"]:
            st.write("• " + exp)

        pdf_path = generate_resume_pdf(resume)

        with open(pdf_path, "rb") as pdf_file:
            st.download_button(
                label="📄 Download ATS Resume PDF",
                data=pdf_file,
                file_name=pdf_path.split("\\")[-1],
                mime="application/pdf"
            )

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

elif menu == "Job Matcher":
    st.header("Job Matcher")

    role_type = st.selectbox("Select Role Type", get_role_names())
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

    with st.form("application_form"):
        company = st.text_input("Company")
        role = st.text_input("Role")
        location = st.text_input("Location")
        job_link = st.text_input("Job Link")
        status = st.selectbox("Status", ["Not Applied", "Applied", "Interview", "Rejected", "Offer"])
        notes = st.text_area("Notes")

        submitted = st.form_submit_button("Save Application")

        if submitted:
            save_application(company, role, location, job_link, status, notes)
            st.success("Application saved successfully.")

    st.subheader("Saved Applications")

    applications = get_all_applications()

    if applications:
        df = pd.DataFrame(
            applications,
            columns=["ID", "Company", "Role", "Location", "Job Link", "Status", "Notes", "Applied Date"]
        )
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No applications saved yet.")

elif menu == "Career Coach":
    st.header("AI Career Coach")

    total_applications = get_total_applications()

    st.metric("Total Applications", total_applications)
    st.write(get_career_advice(total_applications))

    st.subheader("Today’s Focus")
    st.write("1. Apply to strong-match jobs.")
    st.write("2. Tailor your resume before applying.")
    st.write("3. Send recruiter messages for important companies.")