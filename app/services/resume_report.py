from app.services.resume_analyzer import ResumeAnalyzer


class ResumeReport:

    def generate(self, job_description):

        analyzer = ResumeAnalyzer()

        report = analyzer.analyze(job_description)

        return report