from docx import Document


class ResumeOptimizer:

    def __init__(self, resume_path):
        self.resume_path = resume_path
        self.document = Document(resume_path)

    def extract_sections(self):

        sections = {}

        current_heading = "HEADER"

        sections[current_heading] = []

        headings = [
            "CAREER OBJECTIVE",
            "EDUCATION",
            "WORK EXPERIENCE",
            "PROJECTS",
            "TECHNICAL SKILLS",
            "CERTIFICATIONS"
        ]

        for paragraph in self.document.paragraphs:

            text = paragraph.text.strip()

            if not text:
                continue

            if text.upper() in headings:
                current_heading = text.upper()
                sections[current_heading] = []
                continue

            sections[current_heading].append(text)

        return sections