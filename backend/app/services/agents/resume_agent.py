import re
import json
from typing import Dict, Any, List, Optional
from app.services.rag_engine import rag_engine

# Common technical skill tokens for robust regex/token matching
KNOWN_TECH_SKILLS = [
    "Python", "FastAPI", "Flask", "Django", "JavaScript", "TypeScript", "HTML5", "CSS3",
    "SQL", "SQLite", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker", "Kubernetes",
    "Git", "GitHub", "GitLab", "CI/CD", "Linux", "Bash", "REST APIs", "GraphQL",
    "AWS", "GCP", "Azure", "Terraform", "Machine Learning", "Deep Learning", "PyTorch",
    "TensorFlow", "Scikit-Learn", "Pandas", "NumPy", "RAG", "NLP", "LLM", "C++", "C#",
    "Java", "Golang", "Rust", "Microservices", "Unit Testing", "Pytest", "Selenium"
]

KNOWN_SOFT_SKILLS = [
    "Problem Solving", "Communication", "Teamwork", "Collaboration", "Leadership",
    "Adaptability", "Critical Thinking", "Agile", "Scrum", "Time Management",
    "Analytical Thinking", "Mentorship", "Creativity", "Attention to Detail"
]

ACTION_VERBS = [
    "architected", "engineered", "developed", "built", "designed", "implemented",
    "spearheaded", "accelerated", "optimized", "refactored", "automated", "deployed",
    "reduced", "increased", "led", "managed", "created", "launched", "integrated"
]

class ResumeAnalyzerAgent:
    """
    AI Agent responsible for parsing, extracting, and analyzing resume text.
    Extracts candidate contact details, skills, education, experience,
    calculates an ATS score, and generates an executive summary.
    """

    def analyze(self, text: str) -> Dict[str, Any]:
        """Runs the full analysis pipeline on the given resume text."""
        contact_info = self._extract_contact_info(text)
        technical_skills = self._extract_technical_skills(text)
        soft_skills = self._extract_soft_skills(text)
        education = self._extract_education(text)
        experience = self._extract_experience(text)
        certifications = self._extract_certifications(text)
        ats_score, tips = self._calculate_ats_score_and_tips(
            text, contact_info, technical_skills, soft_skills, experience, education
        )
        summary = self._generate_executive_summary(
            contact_info.get("name"), technical_skills, experience, education, ats_score
        )

        return {
            "candidate_name": contact_info.get("name") or "Candidate",
            "email": contact_info.get("email"),
            "phone": contact_info.get("phone"),
            "summary": summary,
            "technical_skills": technical_skills,
            "soft_skills": soft_skills,
            "experience": experience,
            "education": education,
            "certifications": certifications,
            "ats_score": ats_score,
            "improvement_tips": tips
        }

    def _extract_contact_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extracts candidate name, email, and phone number."""
        email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
        email = email_match.group(0) if email_match else None

        phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        phone = phone_match.group(0) if phone_match else None

        # Candidate Name Heuristic: Check the first few lines of the resume
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        name = None
        for line in lines[:6]:
            # Skip lines containing email, phone, links, or header keywords
            line_l = line.lower()
            if "@" in line or (phone and phone in line) or any(k in line_l for k in ["resume", "curriculum", "summary", "profile", "experience", "education", "skills"]):
                continue
            words = line.split()
            if 2 <= len(words) <= 4 and all(re.match(r'^[A-Za-z\'. -]+$', w) for w in words):
                name = line
                break

        if not name and lines:
            # Fallback to first non-empty line if reasonably short
            first_line = lines[0]
            if len(first_line.split()) <= 4 and not re.search(r'[@0-9]', first_line):
                name = first_line

        return {
            "name": name or "Professional Candidate",
            "email": email,
            "phone": phone
        }

    def _extract_technical_skills(self, text: str) -> List[str]:
        """Detects technical skills using both RAG skill dictionary and common vocabulary."""
        text_lower = text.lower()
        detected = set()

        # Check knowledge base skills
        kb_skills = rag_engine.get_all_skills()
        for item in kb_skills:
            if item.get("type") == "technical":
                skill_name = item.get("name")
                # Search name
                pattern = r'\b' + re.escape(skill_name.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    detected.add(skill_name)
                    continue
                # Search synonyms
                for syn in item.get("synonyms", []):
                    if re.search(r'\b' + re.escape(syn.lower()) + r'\b', text_lower):
                        detected.add(skill_name)
                        break

        # Check additional known skills
        for skill in KNOWN_TECH_SKILLS:
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                detected.add(skill)

        return sorted(list(detected))

    def _extract_soft_skills(self, text: str) -> List[str]:
        """Detects interpersonal and professional soft skills."""
        text_lower = text.lower()
        detected = set()

        # Check knowledge base skills
        kb_skills = rag_engine.get_all_skills()
        for item in kb_skills:
            if item.get("type") == "soft":
                skill_name = item.get("name")
                pattern = r'\b' + re.escape(skill_name.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    detected.add(skill_name)
                    continue
                for syn in item.get("synonyms", []):
                    if re.search(r'\b' + re.escape(syn.lower()) + r'\b', text_lower):
                        detected.add(skill_name)
                        break

        for skill in KNOWN_SOFT_SKILLS:
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                detected.add(skill)

        return sorted(list(detected))

    def _extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extracts education history including degrees, colleges, and dates."""
        education_list = []
        degree_patterns = [
            r"(?:Bachelor|Master|Doctor|PhD|B\.S\.|M\.S\.|B\.Tech|M\.Tech|Associate|B\.A\.|M\.A\.)[^\n,.]*",
            r"(?:B\.Sc|M\.Sc|BS|MS|MBA)\s+in\s+[^\n,.]*"
        ]

        text_lines = text.splitlines()
        for i, line in enumerate(text_lines):
            line_str = line.strip()
            for pat in degree_patterns:
                match = re.search(pat, line_str, re.IGNORECASE)
                if match:
                    degree_name = match.group(0).strip()
                    # Check next line or current line for institution and year
                    institution = None
                    year = None

                    # Search year
                    year_match = re.search(r'\b(19\d{2}|20\d{2}(?:\s*-\s*(?:20\d{2}|Present))?)\b', line_str)
                    if year_match:
                        year = year_match.group(0)

                    # Look for institution keywords
                    inst_keywords = ["university", "college", "institute", "school", "academy"]
                    if any(kw in line_str.lower() for kw in inst_keywords):
                        institution = line_str
                    elif i + 1 < len(text_lines) and any(kw in text_lines[i+1].lower() for kw in inst_keywords):
                        institution = text_lines[i+1].strip()
                        if not year:
                            ym = re.search(r'\b(19\d{2}|20\d{2})\b', text_lines[i+1])
                            if ym:
                                year = ym.group(0)

                    education_list.append({
                        "degree": degree_name,
                        "institution": institution or "Accredited Institution",
                        "year": year or "Completed"
                    })
                    break

        if not education_list and re.search(r'\b(?:education|academic|university|degree)\b', text, re.IGNORECASE):
            education_list.append({
                "degree": "Higher Education Degree",
                "institution": "University / College",
                "year": "Documented"
            })

        return education_list

    def _extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extracts professional experience entries."""
        experience_list = []
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        title_keywords = [
            "Software Engineer", "Developer", "Data Scientist", "Data Analyst",
            "DevOps Engineer", "Cloud Engineer", "System Architect", "Tech Lead",
            "Full Stack", "Backend Engineer", "Frontend Engineer", "Intern", "Manager"
        ]

        for i, line in enumerate(lines):
            for kw in title_keywords:
                if kw.lower() in line.lower() and len(line) < 100:
                    title = line
                    company = None
                    duration = None
                    description_bullets = []

                    # Look at adjacent lines
                    if i + 1 < len(lines):
                        next_line = lines[i+1]
                        date_match = re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|20\d{2})\b', next_line, re.IGNORECASE)
                        if date_match or "|" in next_line or "-" in next_line:
                            duration = next_line
                        else:
                            company = next_line

                    # Collect subsequent bullet points
                    for j in range(i + 2, min(i + 6, len(lines))):
                        bullet = lines[j]
                        if bullet.startswith(("•", "-", "*")) or len(bullet) > 20:
                            description_bullets.append(bullet)
                        else:
                            break

                    experience_list.append({
                        "title": title,
                        "company": company or "Technology Company",
                        "duration": duration or "Experienced",
                        "description": " ".join(description_bullets) if description_bullets else "Executed development and engineering tasks."
                    })
                    break

        # Fallback if no specific title keyword matched
        if not experience_list:
            experience_list.append({
                "title": "Software & Technical Experience",
                "company": "Industry Projects",
                "duration": "Documented",
                "description": "Practical application of software development and problem solving skills."
            })

        return experience_list[:5]  # Keep top 5 prominent roles

    def _extract_certifications(self, text: str) -> List[str]:
        """Extracts listed certifications."""
        certs = []
        patterns = [
            r'AWS Certified[^\n,.]*',
            r'Certified Kubernetes[^\n,.]*',
            r'CKA\b',
            r'TensorFlow Developer[^\n,.]*',
            r'Meta Back-End[^\n,.]*',
            r'Google Cloud Certified[^\n,.]*',
            r'Microsoft Certified[^\n,.]*'
        ]
        for pat in patterns:
            matches = re.findall(pat, text, re.IGNORECASE)
            for m in matches:
                if m.strip() not in certs:
                    certs.append(m.strip())
        return certs

    def _calculate_ats_score_and_tips(
        self,
        text: str,
        contact: Dict[str, Any],
        tech_skills: List[str],
        soft_skills: List[str],
        experience: List[Dict],
        education: List[Dict]
    ) -> (int, List[str]):
        """
        Calculates an ATS compatibility score (0-100) and actionable improvement tips
        augmented by the RAG resume guidelines knowledge base.
        """
        score = 0
        tips = []

        # 1. Contact Info check (max 20 pts)
        contact_pts = 0
        if contact.get("name") and contact["name"] != "Candidate":
            contact_pts += 10
        if contact.get("email"):
            contact_pts += 5
        else:
            tips.append("Add a clear professional email address to the top of your resume.")
        if contact.get("phone"):
            contact_pts += 5
        else:
            tips.append("Include a contact phone number for recruiter reach-out.")
        score += contact_pts

        # 2. Skills section (max 25 pts)
        if len(tech_skills) >= 6:
            score += 15
        elif len(tech_skills) >= 3:
            score += 10
            tips.append("Expand your technical skills list to include key frameworks, databases, and developer tools.")
        else:
            score += 5
            tips.append("Include a dedicated Technical Skills section with categorized programming languages, tools, and platforms.")

        if len(soft_skills) >= 2:
            score += 10
        else:
            score += 4
            tips.append("Highlight core soft skills such as Problem Solving, Communication, or Agile Teamwork.")

        # 3. Experience & Action Verbs (max 30 pts)
        if experience:
            score += 15
            # Check for action verbs in experience
            text_lower = text.lower()
            verb_count = sum(1 for verb in ACTION_VERBS if re.search(r'\b' + verb + r'\b', text_lower))
            if verb_count >= 4:
                score += 15
            elif verb_count >= 2:
                score += 10
                tips.append("Use more decisive action verbs (e.g. Engineered, Spearheaded, Optimized) at the start of bullet points.")
            else:
                score += 5
                tips.append("Rewrite bullet points following the X-Y-Z formula (accomplished X, measured by Y, by doing Z).")
        else:
            tips.append("Add a detailed Professional Experience or Projects section detailing your technical accomplishments.")

        # 4. Education (max 15 pts)
        if education:
            score += 15
        else:
            score += 5
            tips.append("Ensure your Education history (Degree, Institution, Graduation Year) is clearly structured.")

        # 5. Length and readability (max 10 pts)
        word_count = len(text.split())
        if 250 <= word_count <= 1000:
            score += 10
        elif word_count < 250:
            score += 4
            tips.append("Your resume appears brief. Add more project descriptions and measurable results.")
        else:
            score += 6
            tips.append("Your resume may be too verbose. Try keeping it concise (1 to 2 pages max).")

        # Cap score between 20 and 98
        final_score = max(20, min(score, 98))

        # Retrieve guidelines from RAG for additional grounded tips
        guidelines = rag_engine.get_resume_guidelines()
        if len(tips) < 3 and guidelines:
            for g in guidelines:
                rec = g.get("recommendation")
                if rec and rec not in tips:
                    tips.append(rec)
                    if len(tips) >= 4:
                        break

        return final_score, tips

    def _generate_executive_summary(
        self,
        name: Optional[str],
        skills: List[str],
        experience: List[Dict],
        education: List[Dict],
        ats_score: int
    ) -> str:
        """Generates a cohesive executive summary of the candidate's profile."""
        candidate = name or "The candidate"
        primary_skills = ", ".join(skills[:5]) if skills else "software engineering and modern web technologies"
        edu_summary = education[0].get("degree") if education else "a background in technology"

        role_summary = experience[0].get("title") if experience else "software developer"

        summary = (
            f"{candidate} is an accomplished technical professional with demonstrated proficiency in {primary_skills}. "
            f"Equipped with {edu_summary}, they have hands-on experience as a {role_summary}, contributing to system "
            f"design, feature development, and collaborative problem solving. Evaluated with an ATS readiness score of "
            f"{ats_score}/100, their profile exhibits solid technical foundations and strong growth potential for modern engineering teams."
        )
        return summary

resume_analyzer_agent = ResumeAnalyzerAgent()
