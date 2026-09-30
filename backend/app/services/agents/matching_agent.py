import json
import re
from typing import Dict, Any, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.services.rag_engine import rag_engine

class JobMatchingAgent:
    """
    AI Agent responsible for evaluating candidate resumes against job descriptions,
    computing similarity metrics, identifying skill gaps, and generating
    comprehensive match explanations.
    """

    def evaluate_match(
        self,
        resume_text: str,
        candidate_skills: List[str],
        job: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates the compatibility between a candidate resume and a job specification.
        Returns match score (0-100%), matched skills, missing skills, and detailed explanation.
        """
        # Parse job skills
        req_skills = job.get("required_skills", [])
        if isinstance(req_skills, str):
            try:
                req_skills = json.loads(req_skills)
            except Exception:
                req_skills = [s.strip() for s in req_skills.split(",") if s.strip()]

        pref_skills = job.get("preferred_skills", [])
        if isinstance(pref_skills, str):
            try:
                pref_skills = json.loads(pref_skills)
            except Exception:
                pref_skills = [s.strip() for s in pref_skills.split(",") if s.strip()]

        candidate_skills_lower = {s.lower() for s in candidate_skills}
        resume_text_lower = resume_text.lower()

        # 1. Evaluate Required Skills
        matched_required = []
        missing_required = []
        for skill in req_skills:
            if self._is_skill_present(skill, candidate_skills_lower, resume_text_lower):
                matched_required.append(skill)
            else:
                missing_required.append(skill)

        # 2. Evaluate Preferred Skills
        matched_preferred = []
        missing_preferred = []
        for skill in pref_skills:
            if self._is_skill_present(skill, candidate_skills_lower, resume_text_lower):
                matched_preferred.append(skill)
            else:
                missing_preferred.append(skill)

        # 3. Calculate Skill Ratios
        req_ratio = len(matched_required) / len(req_skills) if req_skills else 1.0
        pref_ratio = len(matched_preferred) / len(pref_skills) if pref_skills else 0.5

        # 4. Calculate Semantic Similarity via TF-IDF
        semantic_sim = self._calculate_semantic_similarity(resume_text, job.get("description", ""))

        # 5. Composite Score Calculation (Weighted)
        # 50% Required Skills, 15% Preferred Skills, 35% Semantic Context
        composite_score = (req_ratio * 50.0) + (pref_ratio * 15.0) + (semantic_sim * 35.0)
        match_score = round(max(5.0, min(composite_score, 99.0)), 1)

        # 6. Generate Contextual Match Explanation
        matched_all = matched_required + matched_preferred
        missing_all = missing_required
        explanation = self._generate_match_explanation(
            job.get("title", "Position"),
            job.get("company", "Company"),
            match_score,
            matched_required,
            missing_required,
            matched_preferred
        )

        return {
            "match_score": match_score,
            "matched_skills": matched_all,
            "missing_skills": missing_all,
            "match_explanation": explanation
        }

    def _is_skill_present(self, skill: str, candidate_skills_set: set, resume_text_lower: str) -> bool:
        """Checks if a skill exists in candidate skill list or in the resume text."""
        skill_lower = skill.lower()
        if skill_lower in candidate_skills_set:
            return True
        # Check as whole word in text
        pattern = r'\b' + re.escape(skill_lower) + r'\b'
        return bool(re.search(pattern, resume_text_lower))

    def _calculate_semantic_similarity(self, text_a: str, text_b: str) -> float:
        """Computes TF-IDF cosine similarity between two texts."""
        if not text_a.strip() or not text_b.strip():
            return 0.3
        try:
            vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
            tfidf = vectorizer.fit_transform([text_a, text_b])
            sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
            # Rescale slightly so that standard technical text scores between 0.3 and 0.95
            rescaled = min(1.0, float(sim) * 2.2 + 0.15)
            return max(0.1, rescaled)
        except Exception:
            return 0.4

    def _generate_match_explanation(
        self,
        title: str,
        company: str,
        score: float,
        matched_req: List[str],
        missing_req: List[str],
        matched_pref: List[str]
    ) -> str:
        """Builds an explanatory narrative of the candidate's alignment with the role."""
        if score >= 80:
            fit_tier = "Exceptional Match"
            sentiment = "Your qualifications closely mirror the core demands of this role."
        elif score >= 65:
            fit_tier = "Strong Match"
            sentiment = "You fulfill the primary requirements and have a competitive profile."
        elif score >= 45:
            fit_tier = "Moderate Match"
            sentiment = "You have a solid foundational skill set, but several required technologies are missing."
        else:
            fit_tier = "Developing Alignment"
            sentiment = "Significant skill acquisition is recommended before applying to this position."

        matched_req_str = ", ".join(matched_req) if matched_req else "None directly detected"
        missing_req_str = ", ".join(missing_req) if missing_req else "None! All required skills satisfied"
        pref_str = f" Bonus competencies verified: {', '.join(matched_pref)}." if matched_pref else ""

        explanation = (
            f"**{fit_tier} ({score}%)**: {sentiment}\n\n"
            f"• **Verified Required Competencies**: {matched_req_str}.{pref_str}\n"
            f"• **Key Skill Gaps to Address**: {missing_req_str}.\n"
            f"• **Recommendation**: "
            + ("Prioritize this application immediately and tailor your summary around your verified competencies."
               if score >= 75 else
               "Review the missing skills and consider completing recommended online certifications before applying.")
        )
        return explanation

job_matching_agent = JobMatchingAgent()
