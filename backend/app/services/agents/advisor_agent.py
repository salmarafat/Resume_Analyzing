import json
import logging
from typing import Dict, Any, List, Optional
from app.config import GEMINI_API_KEY
from app.services.rag_engine import rag_engine

logger = logging.getLogger("advisor_agent")

class CareerAdvisorAgent:
    """
    AI Agent responsible for providing personalized career recommendations,
    synthesizing RAG knowledge base resources, identifying skill gaps,
    and conducting interactive career mentoring sessions.
    """

    def generate_improvement_plan(
        self,
        resume_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive improvement plan fulfilling FR-5:
        Identifies strengths, weaknesses, actionable improvements,
        target certifications, and learning resource roadmaps.
        """
        tech_skills = resume_analysis.get("technical_skills", [])
        soft_skills = resume_analysis.get("soft_skills", [])
        experience = resume_analysis.get("experience", [])
        ats_score = resume_analysis.get("ats_score", 60)

        # 1. Strengths
        strengths = []
        if len(tech_skills) >= 5:
            strengths.append(f"Strong technical breadth spanning {len(tech_skills)} core technologies ({', '.join(tech_skills[:4])}).")
        if soft_skills:
            strengths.append(f"Clear articulation of interpersonal skills ({', '.join(soft_skills[:3])}).")
        if experience and len(experience) >= 1:
            strengths.append(f"Documented professional experience as '{experience[0].get('title')}'.")
        if ats_score >= 75:
            strengths.append("High ATS formatting alignment and section clarity.")
        elif not strengths:
            strengths.append("Demonstrated foundational technical competencies and enthusiasm.")

        # 2. Identify Missing Skills by comparing against Roadmaps
        roadmaps = rag_engine.get_career_roadmaps()
        candidate_skills_lower = {s.lower() for s in tech_skills}

        missing_skills_pool = []
        for rm in roadmaps:
            for milestone in rm.get("milestones", []):
                for skill in milestone.get("key_skills", []):
                    # Skill might be compound like "FastAPI or Flask"
                    for subskill in skill.split(" or "):
                        s_clean = subskill.split("/")[0].strip()
                        if s_clean.lower() not in candidate_skills_lower and s_clean not in missing_skills_pool:
                            missing_skills_pool.append(s_clean)

        # Select top missing skills
        priority_missing = missing_skills_pool[:5] if missing_skills_pool else ["Docker", "Kubernetes", "Redis", "CI/CD", "AWS"]

        # 3. Retrieve Learning Resources from RAG for missing skills
        matched_resources = rag_engine.get_learning_resources_for_skills(priority_missing)
        all_resources = rag_engine.raw_data.get("resources", [])

        # Certifications
        certifications = [
            r for r in all_resources if r.get("category") == "Certifications"
        ][:3]

        # 4. Map skills to roadmaps
        missing_skills_roadmap = []
        all_skills_kb = rag_engine.get_all_skills()
        skill_dict = {s["name"].lower(): s for s in all_skills_kb}

        for skill_name in priority_missing:
            info = skill_dict.get(skill_name.lower(), {})
            desc = info.get("description", f"Industry standard skill required for modern cloud and backend architectures.")
            category = info.get("category", "Software Engineering")
            skill_resources = [
                r for r in all_resources
                if any(skill_name.lower() in ts.lower() for ts in r.get("target_skills", []))
            ]

            missing_skills_roadmap.append({
                "skill": skill_name,
                "category": category,
                "description": desc,
                "learning_resources": skill_resources[:2]
            })

        # 5. Actionable improvements from RAG Guidelines
        actionable_improvements = resume_analysis.get("improvement_tips", [])
        guidelines = rag_engine.get_resume_guidelines()
        for g in guidelines:
            rec = g.get("recommendation")
            if rec and rec not in actionable_improvements and len(actionable_improvements) < 5:
                actionable_improvements.append(rec)

        # 6. Weaknesses
        weaknesses = []
        if ats_score < 70:
            weaknesses.append("ATS formatting score is below the competitive threshold of 75/100.")
        if len(tech_skills) < 4:
            weaknesses.append("Limited technical stack depth declared in the skills section.")
        if not soft_skills:
            weaknesses.append("Lack of explicit soft skill demonstrations (collaboration, agile, leadership).")
        if priority_missing:
            weaknesses.append(f"Noticeable gap in production cloud & DevOps practices ({', '.join(priority_missing[:3])}).")
        if not weaknesses:
            weaknesses.append("Opportunities remain to quantify bullet point metrics (X-Y-Z formula) further.")

        return {
            "resume_id": resume_analysis.get("resume_id", 0),
            "ats_score": ats_score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "actionable_improvements": actionable_improvements,
            "recommended_certifications": certifications,
            "missing_skills_roadmap": missing_skills_roadmap
        }

    def answer_career_question(
        self,
        user_message: str,
        resume_summary: Optional[str] = None,
        candidate_skills: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Answers candidate questions about resume improvements, career transitions,
        and upskilling using RAG retrieval + LLM synthesis (Gemini or deterministic engine).
        """
        # 1. RAG Retrieval across Knowledge Base
        retrieved_docs = rag_engine.retrieve(user_message, top_k=4)
        context_str = rag_engine.format_context_for_prompt(retrieved_docs)

        # 2. Check if Gemini API is available
        if GEMINI_API_KEY:
            try:
                response_text = self._call_gemini_api(user_message, context_str, resume_summary, candidate_skills)
                return {
                    "role": "assistant",
                    "message": response_text,
                    "retrieved_sources": retrieved_docs
                }
            except Exception as e:
                logger.error(f"Gemini API call failed, falling back to deterministic RAG: {e}")

        # 3. Deterministic RAG Knowledge Synthesizer
        response_text = self._synthesize_rag_response(user_message, retrieved_docs, resume_summary, candidate_skills)
        return {
            "role": "assistant",
            "message": response_text,
            "retrieved_sources": retrieved_docs
        }

    def _call_gemini_api(
        self,
        query: str,
        context: str,
        resume_summary: Optional[str],
        skills: Optional[List[str]]
    ) -> str:
        """Invokes Gemini model using google-genai library if key is available."""
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = (
            "You are an expert AI Career Advisor and Technical Recruiter. "
            "Use the provided Knowledge Base context and Candidate Profile to give clear, "
            "empowering, highly actionable advice. Format your output with markdown headers, "
            "bullet points, and direct links if available.\n\n"
            f"Candidate Profile: {resume_summary or 'No active resume attached'}\n"
            f"Candidate Skills: {', '.join(skills) if skills else 'Not specified'}\n\n"
            f"Knowledge Base Context (RAG):\n{context}\n\n"
            f"User Question: {query}"
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text

    def _synthesize_rag_response(
        self,
        query: str,
        docs: List[Dict[str, Any]],
        resume_summary: Optional[str],
        skills: Optional[List[str]]
    ) -> str:
        """
        High-quality deterministic knowledge synthesizer that structures
        an authoritative, personalized response grounded in RAG documents.
        """
        query_lower = query.lower()
        parts = []

        # Personalized greeting and acknowledgment
        if "certif" in query_lower:
            parts.append("### 🎓 Recommended Certifications & Credentials\n")
            parts.append(
                "Certifications demonstrate validated competency to recruiters and bypass initial automated screening filters. "
                "Based on our knowledge base, here are the top industry-recognized paths:\n"
            )
            for d in docs:
                if d.get("category") == "resources":
                    m = d.get("metadata", {})
                    parts.append(f"- **{m.get('name')}** ({m.get('provider')}): {m.get('description')}")
                    if m.get("url"):
                        parts.append(f"  *Resource Link*: [{m.get('name')}]({m.get('url')})\n")

        elif "road" in query_lower or "transition" in query_lower or "learn" in query_lower or "skill" in query_lower:
            parts.append("### 🗺️ Career Progression & Skill Acquisition Roadmap\n")
            parts.append(
                "To advance your technical seniority or transition between specializations, "
                "follow these prioritized milestones:\n"
            )
            for d in docs:
                if d.get("category") == "roadmaps":
                    m = d.get("metadata", {})
                    parts.append(f"**Track: {m.get('track')}**")
                    for ms in m.get("milestones", []):
                        parts.append(f"• **{ms.get('level')}**: {ms.get('focus')}")
                        parts.append(f"  *Key Technologies*: {', '.join(ms.get('key_skills', []))}")
                    parts.append(f"\n💡 *Strategic Advice*: {m.get('transition_advice')}\n")

        elif "resume" in query_lower or "ats" in query_lower or "write" in query_lower or "bullet" in query_lower:
            parts.append("### ✍️ Resume Optimization & ATS Best Practices\n")
            parts.append(
                "Applicant Tracking Systems scan for standardized sections and quantifiable achievements. "
                "Apply these proven recommendations:\n"
            )
            for d in docs:
                if d.get("category") == "guidelines":
                    m = d.get("metadata", {})
                    parts.append(f"- **{m.get('rule')}** ({m.get('importance')} Priority)")
                    parts.append(f"  {m.get('guideline')}")
                    parts.append(f"  *Action*: {m.get('recommendation')}\n")

        else:
            parts.append("### 💡 Career Guidance & Strategic Recommendations\n")
            parts.append(
                "Based on your profile and industry benchmark data, here are key insights to help guide your career:\n"
            )
            for d in docs:
                parts.append(f"• **{d.get('title')}** ({d.get('category').title()}):")
                parts.append(f"  {d.get('text')}\n")

        # Add candidate specific tailored note if skills available
        if skills:
            parts.append(
                f"\n---\n**Tailored for Your Profile:** With your current background in **{', '.join(skills[:3])}**, "
                "focus your next learning cycle on containerization (Docker/Kubernetes) and cloud deployment (AWS) "
                "to maximize hiring interest."
            )

        return "\n".join(parts)

career_advisor_agent = CareerAdvisorAgent()
