from pathlib import Path
from shutil import copyfile
from docx import Document

source = Path("resumes/master/master_resume.docx")
output_dir = Path("exports/docx")
output_dir.mkdir(parents=True, exist_ok=True)

destination = output_dir / "objective_updated_resume.docx"

copyfile(source, destination)

doc = Document(destination)

new_objective = (
    "Data-focused professional with 1.1 years of experience in SQL, Python, Power BI, Excel, "
    "production support, and cloud infrastructure. Experienced in dashboard development, reporting, "
    "data analysis, troubleshooting, and supporting enterprise production systems. Skilled in using "
    "analytical tools and technical problem-solving to support business decision-making."
)

found_heading = False

for paragraph in doc.paragraphs:
    text = paragraph.text.strip()

    if text.upper() == "CAREER OBJECTIVE":
        found_heading = True
        continue

    if found_heading and text:
        paragraph.text = new_objective
        break

doc.save(destination)

print(f"Updated resume created: {destination}")