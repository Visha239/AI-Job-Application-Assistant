import re


class KeywordExtractor:

    def __init__(self):

        self.keyword_bank = [
            "SQL",
            "Python",
            "Excel",
            "Power BI",
            "Tableau",
            "Power Query",
            "DAX",
            "Dashboard",
            "Reporting",
            "KPI",
            "Data Visualization",
            "ETL",
            "MySQL",
            "Oracle",
            "MariaDB",
            "Aurora",
            "Linux",
            "AWS",
            "ServiceNow",
            "Jira",
            "Troubleshooting",
            "Business Analysis",
            "Requirements Gathering",
            "Stakeholder",
            "Documentation",
            "Gap Analysis",
            "Snowflake",
            "Spark",
            "Databricks"
        ]

    def extract(self, job_description):

        jd = job_description.lower()
        found = []

        for keyword in self.keyword_bank:

            pattern = r"\b" + re.escape(keyword.lower()) + r"\b"

            if re.search(pattern, jd):
                found.append(keyword)

        return sorted(found)