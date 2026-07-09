from shutil import copyfile
from pathlib import Path

source = Path("resumes/master/master_resume.docx")
output_dir = Path("exports")
output_dir.mkdir(exist_ok=True)

destination = output_dir / "optimized_resume_test.docx"

copyfile(source, destination)

print(f"Optimized resume copy created: {destination}")