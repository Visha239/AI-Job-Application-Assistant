from app.services.keyword_extractor import KeywordExtractor


class ResumeAnalyzer:

    def __init__(self):

        self.resume_skills = [
            "Python",
            "SQL",
            "Excel",
            "Power BI",
            "Tableau",
            "Linux",
            "AWS",
            "ServiceNow",
            "Jira",
            "Power Query",
            "DAX",
            "Dashboard",
            "Reporting",
            "KPI",
            "Data Analysis",
            "Data Visualization",
            "ETL",
            "MySQL",
            "MariaDB",
            "Oracle",
            "Aurora"
        ]

    def analyze(self, job_description):

        extractor = KeywordExtractor()

        jd_keywords = extractor.extract(job_description)

        matched = []
        emphasize = []
        missing = []

        emphasize_keywords = {
            "Dashboard",
            "Reporting",
            "Power Query",
            "KPI",
            "DAX",
            "Data Visualization"
        }

        for keyword in jd_keywords:

            if keyword in self.resume_skills:

                matched.append(keyword)

                if keyword in emphasize_keywords:
                    emphasize.append(keyword)

            else:

                missing.append(keyword)

        total = len(jd_keywords)

        ats_score = 0

        if total > 0:
            ats_score = round((len(matched) / total) * 100)

        return {

            "ats_score": ats_score,

            "total_keywords": total,

            "matched": matched,

            "emphasize": emphasize,

            "missing": missing,

            "improve": [
                "Career Objective",
                "Technical Skills",
                "Projects",
                "Work Experience"
            ]
        }