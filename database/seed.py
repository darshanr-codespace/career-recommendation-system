"""
seed.py — Populate the database with career data, skill requirements,
and learning resources.  Run once:  python seed.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.models import get_db, init_db

CAREERS = [
    # (career_name, domain, description, avg_salary_lpa, growth_rate, work_environment, personality_fit, interest_domain)
    ("Software Engineer",       "Information Technology", "Design and build software systems and applications.", 12.0, "High",   "Office/Remote", "R,I,C",   "Technology"),
    ("Data Scientist",          "Information Technology", "Extract insights from large datasets using ML and statistics.", 14.0, "Very High","Office/Remote","I,C",     "Technology"),
    ("Cybersecurity Analyst",   "Information Technology", "Protect systems from digital attacks and data breaches.", 11.0, "Very High","Office",      "R,I,C",   "Technology"),
    ("AI/ML Engineer",          "Information Technology", "Build and deploy machine learning models at scale.", 16.0, "Very High","Office/Remote","I,C",     "Technology"),
    ("Full-Stack Web Developer","Information Technology", "Develop both front-end and back-end web applications.", 10.0, "High",   "Office/Remote","R,I",     "Technology"),
    ("Medical Doctor",          "Healthcare",             "Diagnose and treat illnesses; provide patient care.", 18.0, "High",   "Hospital",    "I,S",     "Healthcare"),
    ("Biomedical Engineer",     "Healthcare",             "Design medical devices and diagnostic equipment.", 13.0, "High",   "Lab/Office",  "R,I",     "Healthcare"),
    ("Clinical Psychologist",   "Healthcare",             "Assess and treat mental, emotional, and behavioural disorders.", 10.0,"High", "Clinic",    "I,S,A",   "Healthcare"),
    ("Pharmacist",              "Healthcare",             "Dispense medicines and advise on drug interactions.", 9.0,  "Moderate","Pharmacy",   "C,I",     "Healthcare"),
    ("Civil Engineer",          "Engineering",            "Design and oversee construction of infrastructure.", 9.0,  "Moderate","Field/Office","R,I,C",   "Engineering"),
    ("Mechanical Engineer",     "Engineering",            "Design and analyse mechanical systems and machines.", 9.5,  "Moderate","Office/Lab",  "R,I",     "Engineering"),
    ("Electrical Engineer",     "Engineering",            "Design electrical systems, circuits, and power grids.", 10.0,"High",  "Office/Field","R,I,C",   "Engineering"),
    ("Chartered Accountant",    "Finance & Commerce",     "Audit accounts, tax planning, and financial advisory.", 12.0,"High",  "Office",      "C,E",     "Business"),
    ("Investment Banker",       "Finance & Commerce",     "Advise on mergers, acquisitions, and capital markets.", 20.0,"High",  "Office",      "E,C",     "Business"),
    ("Management Consultant",   "Business",               "Help organisations improve performance and strategy.", 15.0,"High",  "Office/Travel","E,C,I",  "Business"),
    ("Marketing Manager",       "Business",               "Develop and execute marketing strategies for brands.", 11.0,"High",  "Office",      "E,A",     "Business"),
    ("Lawyer",                  "Law",                    "Advise clients on legal matters and represent in courts.", 14.0,"Moderate","Office/Court","E,I,S","Law"),
    ("UX/UI Designer",          "Design",                 "Create intuitive digital interfaces and user experiences.", 10.0,"High","Office/Remote","A,I",   "Design"),
    ("Graphic Designer",        "Design",                 "Create visual content for print and digital media.", 7.0,  "Moderate","Studio/Remote","A,R",   "Arts & Media"),
    ("Content Writer",          "Media & Communication",  "Create written content for digital and print platforms.", 6.0,"Moderate","Remote",     "A,I",   "Arts & Media"),
    ("Data Analyst",            "Analytics",              "Interpret data and generate actionable business insights.", 9.0,"High","Office/Remote","I,C",   "Technology"),
    ("Research Scientist",      "Research",               "Conduct original research and publish findings.", 12.0,"Moderate","Lab/University","I,R",      "Science & Research"),
    ("Teacher / Educator",      "Education",              "Educate students across subjects in schools or colleges.", 6.0,"Moderate","School/College","S,A,I","Education"),
    ("Product Manager",         "Business",               "Define product vision and manage the product roadmap.", 18.0,"Very High","Office",    "E,I,C",  "Business"),
    ("DevOps Engineer",         "Information Technology", "Bridge development and operations; manage CI/CD pipelines.", 13.0,"Very High","Remote/Office","R,C,I","Technology"),
]

# (career_name, [(skill_name, importance, is_mandatory), ...])
CAREER_SKILLS = {
    "Software Engineer":       [("Programming",5,1),("Data Structures",5,1),("Problem Solving",5,1),("Version Control",4,1),("Databases",3,1),("Communication",3,0)],
    "Data Scientist":          [("Python",5,1),("Statistics",5,1),("Machine Learning",5,1),("Data Visualisation",4,1),("SQL",4,1),("Communication",4,1)],
    "Cybersecurity Analyst":   [("Networking",5,1),("Security Tools",5,1),("Programming",4,1),("Ethical Hacking",4,1),("Problem Solving",5,1),("Attention to Detail",5,1)],
    "AI/ML Engineer":          [("Python",5,1),("Machine Learning",5,1),("Deep Learning",5,1),("Mathematics",5,1),("Data Engineering",4,1),("Research",3,0)],
    "Full-Stack Web Developer":[("HTML/CSS",5,1),("JavaScript",5,1),("Backend Frameworks",4,1),("Databases",4,1),("Version Control",4,1),("UI/UX Basics",3,0)],
    "Medical Doctor":          [("Biology",5,1),("Chemistry",5,1),("Clinical Skills",5,1),("Communication",5,1),("Empathy",5,1),("Problem Solving",5,1)],
    "Biomedical Engineer":     [("Biology",4,1),("Engineering Fundamentals",5,1),("Programming",3,1),("Research",4,1),("Problem Solving",4,1)],
    "Clinical Psychologist":   [("Psychology",5,1),("Communication",5,1),("Empathy",5,1),("Research",4,1),("Counselling",5,1)],
    "Pharmacist":              [("Chemistry",5,1),("Biology",4,1),("Attention to Detail",5,1),("Communication",4,1),("Pharmacology",5,1)],
    "Civil Engineer":          [("Mathematics",5,1),("Physics",4,1),("CAD Software",4,1),("Project Management",4,1),("Problem Solving",4,1)],
    "Mechanical Engineer":     [("Mathematics",5,1),("Physics",5,1),("CAD Software",5,1),("Problem Solving",5,1),("Attention to Detail",4,1)],
    "Electrical Engineer":     [("Mathematics",5,1),("Physics",5,1),("Circuit Design",5,1),("Programming",3,1),("Problem Solving",4,1)],
    "Chartered Accountant":    [("Accounting",5,1),("Taxation",5,1),("Attention to Detail",5,1),("Financial Analysis",4,1),("MS Excel",4,1)],
    "Investment Banker":       [("Financial Analysis",5,1),("Communication",5,1),("MS Excel",5,1),("Valuation",5,1),("Networking",4,1)],
    "Management Consultant":   [("Problem Solving",5,1),("Communication",5,1),("Data Analysis",4,1),("Presentation",4,1),("Business Strategy",5,1)],
    "Marketing Manager":       [("Marketing",5,1),("Communication",5,1),("Data Analysis",4,1),("Creativity",4,1),("Leadership",4,0)],
    "Lawyer":                  [("Legal Research",5,1),("Communication",5,1),("Critical Thinking",5,1),("Writing",5,1),("Negotiation",4,1)],
    "UX/UI Designer":          [("UI Design",5,1),("Prototyping",5,1),("User Research",5,1),("Figma/Sketch",4,1),("Creativity",4,1)],
    "Graphic Designer":        [("Adobe Suite",5,1),("Creativity",5,1),("Typography",4,1),("Colour Theory",4,1),("Communication",3,0)],
    "Content Writer":          [("Writing",5,1),("SEO Basics",3,1),("Research",4,1),("Creativity",4,1),("Communication",4,1)],
    "Data Analyst":            [("SQL",5,1),("MS Excel",5,1),("Data Visualisation",4,1),("Statistics",4,1),("Python",3,0)],
    "Research Scientist":      [("Research",5,1),("Statistics",5,1),("Writing",4,1),("Domain Knowledge",5,1),("Critical Thinking",5,1)],
    "Teacher / Educator":      [("Communication",5,1),("Subject Knowledge",5,1),("Empathy",4,1),("Patience",4,1),("Presentation",4,1)],
    "Product Manager":         [("Product Strategy",5,1),("Communication",5,1),("Data Analysis",4,1),("Leadership",4,1),("Agile/Scrum",4,1)],
    "DevOps Engineer":         [("Linux/Unix",5,1),("CI/CD",5,1),("Cloud Platforms",5,1),("Programming",4,1),("Networking",4,1)],
}

RESOURCES = [
    # (career_name, skill_name, title, url, provider, type)
    ("Software Engineer",  "Programming",      "CS50: Introduction to Programming", "https://cs50.harvard.edu/x/", "Harvard/edX", "MOOC"),
    ("Software Engineer",  "Data Structures",  "Data Structures & Algorithms",      "https://www.coursera.org/specializations/data-structures-algorithms", "Coursera", "MOOC"),
    ("Data Scientist",     "Machine Learning", "Machine Learning Specialisation",   "https://www.coursera.org/specializations/machine-learning-introduction", "Coursera/Andrew Ng", "MOOC"),
    ("Data Scientist",     "Statistics",       "Statistics with Python",             "https://www.coursera.org/specializations/statistics-with-python", "Coursera/Michigan", "MOOC"),
    ("AI/ML Engineer",     "Deep Learning",    "Deep Learning Specialisation",      "https://www.coursera.org/specializations/deep-learning", "Coursera/Andrew Ng", "MOOC"),
    ("Cybersecurity Analyst","Security Tools", "CompTIA Security+ Prep",            "https://www.udemy.com/course/comptia-security-cert-sy0-601/", "Udemy", "Course"),
    ("UX/UI Designer",     "Figma/Sketch",     "Figma UI UX Design Essentials",     "https://www.udemy.com/course/figma-ux-ui-design-user-experience-tutorial-course/", "Udemy", "Course"),
    ("Data Analyst",       "SQL",              "SQL for Data Science",              "https://www.coursera.org/learn/sql-for-data-science", "Coursera/UC Davis", "MOOC"),
    ("Chartered Accountant","MS Excel",        "Excel Skills for Business",         "https://www.coursera.org/specializations/excel", "Coursera/Macquarie", "MOOC"),
    ("Full-Stack Web Developer","JavaScript",  "The Complete JavaScript Course",    "https://www.udemy.com/course/the-complete-javascript-course/", "Udemy", "Course"),
    ("DevOps Engineer",    "CI/CD",            "DevOps Beginners to Advanced",      "https://www.udemy.com/course/devsecops/", "Udemy", "Course"),
    ("Product Manager",    "Product Strategy", "Digital Product Management",        "https://www.coursera.org/specializations/uva-darden-digital-product-management", "Coursera", "MOOC"),
]


def seed():
    init_db()
    conn = get_db()
    cur = conn.cursor()

    # --- Careers ---
    for row in CAREERS:
        cur.execute("""
            INSERT OR IGNORE INTO career
            (career_name,domain,description,avg_salary_lpa,growth_rate,
             work_environment,personality_fit,interest_domain)
            VALUES (?,?,?,?,?,?,?,?)
        """, row)

    conn.commit()

    # --- Career Skills ---
    for cname, skills in CAREER_SKILLS.items():
        cur.execute("SELECT career_id FROM career WHERE career_name=?", (cname,))
        row = cur.fetchone()
        if not row:
            continue
        cid = row["career_id"]
        for sname, imp, mand in skills:
            cur.execute("""
                INSERT OR IGNORE INTO career_skill
                (career_id, skill_name, importance, is_mandatory)
                VALUES (?,?,?,?)
            """, (cid, sname, imp, mand))

    conn.commit()

    # --- Learning Resources ---
    for cname, skill, title, url, provider, rtype in RESOURCES:
        cur.execute("SELECT career_id FROM career WHERE career_name=?", (cname,))
        row = cur.fetchone()
        if not row:
            continue
        cid = row["career_id"]
        cur.execute("""
            INSERT OR IGNORE INTO learning_resource
            (career_id, skill_name, title, url, provider, resource_type)
            VALUES (?,?,?,?,?,?)
        """, (cid, skill, title, url, provider, rtype))

    conn.commit()
    conn.close()
    print("[SEED] Database seeded successfully.")


if __name__ == "__main__":
    seed()
