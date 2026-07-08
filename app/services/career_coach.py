def get_career_advice(applications_count):
    if applications_count < 10:
        return "Today’s goal: Apply to at least 10 good matching jobs."
    elif applications_count < 30:
        return "Good progress. Start following up with recruiters for older applications."
    else:
        return "Strong activity. Focus more on high-match jobs and interview preparation."