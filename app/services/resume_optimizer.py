from pathlib import Path
from shutil import copyfile
from docx import Document


class ResumeOptimizer:
    def __init__(self, master_resume_path="resumes/master/master_resume.docx"):
        self.master_resume_path = Path(master_resume_path)

    def create_resume_copy(self, output_filename):
        output_dir = Path("exports/docx")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / output_filename
        copyfile(self.master_resume_path, output_path)
        return output_path

    def extract_keywords(self, job_description):
        keyword_bank = [
            "SQL", "Python", "Excel", "Power BI", "Tableau", "Data Analysis",
            "Dashboard", "Reporting", "KPI", "DAX", "Power Query", "ETL",
            "Data Visualization", "Business Analysis", "Requirements Gathering",
            "Documentation", "Stakeholder", "Gap Analysis", "Jira",
            "ServiceNow", "Linux", "AWS", "Troubleshooting"
        ]

        jd_lower = job_description.lower()
        found = []

        for keyword in keyword_bank:
            if keyword.lower() in jd_lower:
                found.append(keyword)

        return found

    def generate_objective(self, role_type, keywords):
        keyword_text = ", ".join(keywords[:6])

        if role_type == "Data Analyst":
            return (
                f"Data-focused professional with 1.1 years of experience in SQL, Python, Power BI, Excel, "
                f"production support, and cloud infrastructure. Skilled in {keyword_text}. "
                f"Experienced in dashboard development, reporting, data analysis, troubleshooting, "
                f"and supporting business decision-making through actionable insights."
            )

        if role_type == "Business Analyst":
            return (
                f"Business-focused analyst with 1.1 years of experience in SQL, Excel, documentation, "
                f"stakeholder communication, and reporting. Skilled in {keyword_text}. "
                f"Experienced in understanding requirements, identifying gaps, improving processes, "
                f"and translating business needs into actionable insights."
            )

        if role_type == "Support Engineer":
            return (
                f"Technical support professional with 1.1 years of experience in production support, Linux, SQL, "
                f"ServiceNow, Jira, AWS, and incident management. Skilled in {keyword_text}. "
                f"Experienced in monitoring, maintaining, and resolving issues in live enterprise systems."
            )

        return (
            f"Detail-oriented professional with experience in SQL, Python, Power BI, Excel, "
            f"production support, and business reporting. Skilled in {keyword_text}."
        )

    def replace_career_objective(self, doc, new_objective):
        found_heading = False

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()

            if text.upper() == "CAREER OBJECTIVE":
                found_heading = True
                continue

            if found_heading and text:
                paragraph.text = new_objective
                return True

        return False

    def optimize_resume(self, role_type, job_description):
        output_filename = f"{role_type.replace(' ', '_')}_JD_Optimized_Resume.docx"
        output_path = self.create_resume_copy(output_filename)

        doc = Document(output_path)

        keywords = self.extract_keywords(job_description)
        new_objective = self.generate_objective(role_type, keywords)

        self.replace_career_objective(doc, new_objective)

        doc.save(output_path)

        return {
            "output_path": str(output_path),
            "keywords": keywords,
            "objective": new_objective
        }