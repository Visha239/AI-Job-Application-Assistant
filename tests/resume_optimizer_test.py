from app.services.resume_optimizer import ResumeOptimizer

optimizer = ResumeOptimizer("resumes/master/master_resume.docx")

sections = optimizer.extract_sections()

for section, content in sections.items():

    print("\n")
    print("="*50)

    print(section)

    print("="*50)

    for line in content:

        print(line)