def generate_email(profile, company, role):
    return f"""Subject: Application for {role} Role

Dear Hiring Team,

I hope you are doing well.

My name is {profile['name']}. I am interested in the {role} role at {company}.

I have experience in SQL, Python, Power BI, Excel, Tableau, and Data Analysis. I have also worked on Power BI dashboards, SQL analysis, and Python-based data analysis projects.

I believe my skills match the requirements of this role, and I would be happy to discuss how I can contribute to your team.

Please find my resume attached for your reference.

Thank you for your time and consideration.

Best regards,
{profile['name']}
{profile['email']}
"""