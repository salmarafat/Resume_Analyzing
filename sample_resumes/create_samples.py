import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path

def create_resume_docx(filepath: str, data: dict):
    doc = docx.Document()

    # Page margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.6)
        section.bottom_margin = Inches(0.6)
        section.left_margin = Inches(0.7)
        section.right_margin = Inches(0.7)

    # Name Header
    name_p = doc.add_paragraph()
    name_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name_run = name_p.add_run(data["name"])
    name_run.font.size = Pt(20)
    name_run.font.bold = True
    name_run.font.color.rgb = RGBColor(30, 41, 59)

    # Contact Info
    contact_p = doc.add_paragraph()
    contact_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact_text = f"{data['email']}  |  {data['phone']}  |  {data['location']}  |  {data['linkedin']}"
    contact_run = contact_p.add_run(contact_text)
    contact_run.font.size = Pt(9.5)
    contact_run.font.color.rgb = RGBColor(100, 116, 139)

    def add_heading(title):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(3)
        run = h.add_run(title.upper())
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = RGBColor(15, 23, 42)

    # Summary
    add_heading("Professional Summary")
    p_sum = doc.add_paragraph()
    p_sum.paragraph_format.space_after = Pt(6)
    p_sum_run = p_sum.add_run(data["summary"])
    p_sum_run.font.size = Pt(10)

    # Technical Skills
    add_heading("Technical Skills")
    for category, skills in data["skills"].items():
        sp = doc.add_paragraph()
        sp.paragraph_format.space_after = Pt(2)
        r_cat = sp.add_run(f"• {category}: ")
        r_cat.font.bold = True
        r_cat.font.size = Pt(10)
        r_skills = sp.add_run(", ".join(skills))
        r_skills.font.size = Pt(10)

    # Experience
    add_heading("Work Experience")
    for exp in data["experience"]:
        ep = doc.add_paragraph()
        ep.paragraph_format.space_before = Pt(4)
        ep.paragraph_format.space_after = Pt(1)
        r_title = ep.add_run(exp["title"])
        r_title.font.bold = True
        r_title.font.size = Pt(10.5)

        r_comp = ep.add_run(f" — {exp['company']} ({exp['duration']})")
        r_comp.font.italic = True
        r_comp.font.size = Pt(10)

        for b in exp["bullets"]:
            bp = doc.add_paragraph()
            bp.paragraph_format.space_after = Pt(2)
            bp.paragraph_format.left_indent = Inches(0.2)
            r_b = bp.add_run(f"• {b}")
            r_b.font.size = Pt(9.5)

    # Education
    add_heading("Education")
    for edu in data["education"]:
        ed_p = doc.add_paragraph()
        ed_p.paragraph_format.space_after = Pt(2)
        r_deg = ed_p.add_run(edu["degree"])
        r_deg.font.bold = True
        r_deg.font.size = Pt(10)
        r_school = ed_p.add_run(f" — {edu['institution']}, {edu['year']}")
        r_school.font.size = Pt(10)

    # Certifications
    if "certifications" in data and data["certifications"]:
        add_heading("Certifications")
        for cert in data["certifications"]:
            cp = doc.add_paragraph()
            cp.paragraph_format.space_after = Pt(2)
            cp.paragraph_format.left_indent = Inches(0.2)
            rc = cp.add_run(f"• {cert}")
            rc.font.size = Pt(9.5)

    doc.save(filepath)
    print(f"Generated resume: {filepath}")

def main():
    out_dir = Path(__file__).parent

    # 1. Full Stack Software Engineer
    se_data = {
        "name": "Jordan Miller",
        "email": "jordan.miller@devmail.com",
        "phone": "+1 (555) 234-5678",
        "location": "San Francisco, CA",
        "linkedin": "linkedin.com/in/jordanmiller-dev",
        "summary": "Full Stack Software Engineer with 3+ years of experience designing robust RESTful APIs and modern web applications using Python, FastAPI, and Vanilla JavaScript. Proven track record in microservices architecture, relational database optimization, and CI/CD pipelines.",
        "skills": {
            "Languages & Frameworks": ["Python", "FastAPI", "JavaScript", "HTML5", "CSS3", "SQL", "Bash"],
            "Databases & Tools": ["PostgreSQL", "SQLite", "Redis", "Docker", "Git", "REST APIs", "Pytest"],
            "Soft Skills": ["Problem Solving", "Cross-Functional Collaboration", "Agile", "Critical Thinking"]
        },
        "experience": [
            {
                "title": "Software Engineer",
                "company": "CloudStream Solutions",
                "duration": "2023 - Present",
                "bullets": [
                    "Architected high-throughput REST APIs using FastAPI and SQLite/PostgreSQL, reducing p95 latency by 32% across 150k daily active requests.",
                    "Engineered responsive user dashboards with Vanilla JavaScript and HTML5/CSS3, improving mobile page load performance by 40%.",
                    "Containerized microservices using Docker and implemented automated test suites with Pytest achieving 88% code coverage.",
                    "Collaborated in bi-weekly agile sprints, performing peer code reviews and maintaining technical design documentation."
                ]
            },
            {
                "title": "Junior Python Developer",
                "company": "Apex Web Tech",
                "duration": "2021 - 2023",
                "bullets": [
                    "Developed backend data integration endpoints and scheduled background tasks using Python and SQL.",
                    "Refactored legacy relational database schema, reducing database lock contention and query execution time.",
                    "Integrated secure JWT-based user authentication and role-based permissions across 12 API modules."
                ]
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science in Computer Science",
                "institution": "University of California, Davis",
                "year": "2021"
            }
        ],
        "certifications": [
            "AWS Certified Solutions Architect - Associate",
            "Meta Back-End Developer Professional Certificate"
        ]
    }
    create_resume_docx(str(out_dir / "sample_software_engineer.docx"), se_data)

    # 2. Data Scientist
    ds_data = {
        "name": "Dr. Maya Patel",
        "email": "maya.patel@datascience.org",
        "phone": "+1 (555) 876-5432",
        "location": "Boston, MA",
        "linkedin": "linkedin.com/in/mayapatel-phd",
        "summary": "Data Scientist with 4+ years of expertise in predictive machine learning, statistical modeling, and data pipelines. Adept at transforming raw unstructured data into actionable strategic insights using Python, Scikit-Learn, and PyTorch.",
        "skills": {
            "Languages & ML": ["Python", "Machine Learning", "Pandas", "NumPy", "Scikit-Learn", "PyTorch", "SQL", "Statistics"],
            "Tools & Deployments": ["FastAPI", "Docker", "Git", "Data Visualization", "Matplotlib", "Jupyter"],
            "Soft Skills": ["Analytical Thinking", "Communication", "Problem Solving", "Adaptability"]
        },
        "experience": [
            {
                "title": "Senior Data Scientist",
                "company": "Vanguard Predictive Systems",
                "duration": "2022 - Present",
                "bullets": [
                    "Engineered predictive classification models with Scikit-Learn and PyTorch, yielding a 14% improvement in customer retention forecasting.",
                    "Implemented feature extraction pipelines processing over 2TB of user behavioral data with Pandas and SQL.",
                    "Deployed model inference microservices with FastAPI and Docker containerization.",
                    "Delivered data storytelling presentations to executive stakeholders to guide quarterly product roadmap decisions."
                ]
            },
            {
                "title": "Data Analyst & Modeler",
                "company": "Beacon Analytics Group",
                "duration": "2020 - 2022",
                "bullets": [
                    "Conducted rigorous exploratory data analysis (EDA) and hypothesis testing on multi-variate commercial datasets.",
                    "Constructed interactive data visualization dashboards communicating statistical trends to business units.",
                    "Automated daily ETL data extraction scripts in Python and SQL."
                ]
            }
        ],
        "education": [
            {
                "degree": "Master of Science in Data Science & Analytics",
                "institution": "Boston University",
                "year": "2020"
            },
            {
                "degree": "Bachelor of Science in Mathematics & Statistics",
                "institution": "University of Massachusetts",
                "year": "2018"
            }
        ],
        "certifications": [
            "TensorFlow Developer Certificate / Deep Learning Specialization"
        ]
    }
    create_resume_docx(str(out_dir / "sample_data_scientist.docx"), ds_data)

    # 3. Frontend Web Developer
    fe_data = {
        "name": "Liam Connor",
        "email": "liam.connor@frontenddev.io",
        "phone": "+1 (555) 432-1098",
        "location": "Austin, TX",
        "linkedin": "linkedin.com/in/liamconnor-web",
        "summary": "Creative and detail-oriented Frontend Developer with 2+ years of experience building accessible, pixel-perfect web interfaces using Vanilla JavaScript, HTML5, and modern CSS3. Passionate about web performance, animations, and cross-browser consistency.",
        "skills": {
            "Web Technologies": ["JavaScript", "HTML5", "CSS3", "Responsive Design", "REST APIs", "DOM Manipulation"],
            "Tooling & Versioning": ["Git", "GitHub", "Chrome DevTools", "Flexbox", "CSS Grid", "Performance Optimization"],
            "Soft Skills": ["Attention to Detail", "Teamwork", "Agility", "Communication"]
        },
        "experience": [
            {
                "title": "Frontend Web Developer",
                "company": "PixelCraft Studios",
                "duration": "2022 - Present",
                "bullets": [
                    "Engineered responsive user interfaces from Figma designs using pure Vanilla JavaScript, HTML5, and CSS Grid/Flexbox without heavy frameworks.",
                    "Optimized critical rendering path and image compression, elevating Google Lighthouse performance scores from 68 to 96.",
                    "Integrated client-side RESTful API communication with asynchronous Fetch and resilient error state handling.",
                    "Ensured WCAG 2.1 AA accessibility compliance across 40+ production customer-facing pages."
                ]
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science in Information Technology",
                "institution": "Texas State University",
                "year": "2022"
            }
        ],
        "certifications": [
            "CS50's Introduction to Computer Science & Web Programming"
        ]
    }
    create_resume_docx(str(out_dir / "sample_frontend_developer.docx"), fe_data)

if __name__ == "__main__":
    main()
