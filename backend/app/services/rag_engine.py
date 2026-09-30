import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import KNOWLEDGE_BASE_DIR

logger = logging.getLogger("rag_engine")

class RAGEngine:
    """
    Retrieval-Augmented Generation (RAG) engine that manages, indexes,
    and searches across the 5 core knowledge base collections:
      1. Job descriptions
      2. Skill descriptions
      3. Career roadmaps
      4. Learning resources
      5. Resume writing guidelines
    """
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.raw_data: Dict[str, Any] = {}
        self.load_knowledge_base()
        self.build_index()

    def load_knowledge_base(self):
        """Loads all JSON files from the knowledge base directory."""
        files = {
            "jobs": "job_descriptions.json",
            "skills": "skill_descriptions.json",
            "roadmaps": "career_roadmaps.json",
            "resources": "learning_resources.json",
            "guidelines": "resume_guidelines.json"
        }

        self.documents = []
        self.raw_data = {}

        for category, filename in files.items():
            file_path = KNOWLEDGE_BASE_DIR / filename
            if not file_path.exists():
                logger.warning(f"Knowledge base file {filename} not found at {file_path}")
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.raw_data[category] = data

                    # Index chunks for each file
                    if category == "jobs":
                        for item in data:
                            content = f"Job Title: {item.get('title')}. Department: {item.get('department')}. " \
                                      f"Experience: {item.get('experience_level')}. " \
                                      f"Summary: {item.get('summary')}. " \
                                      f"Required Skills: {', '.join(item.get('required_skills', []))}. " \
                                      f"Preferred Skills: {', '.join(item.get('preferred_skills', []))}."
                            self.documents.append({
                                "id": item.get("id"),
                                "category": category,
                                "title": item.get("title"),
                                "text": content,
                                "metadata": item
                            })

                    elif category == "skills":
                        for item in data:
                            content = f"Skill: {item.get('name')}. Category: {item.get('category')}. " \
                                      f"Type: {item.get('type')}. Description: {item.get('description')}. " \
                                      f"Synonyms: {', '.join(item.get('synonyms', []))}. Benchmarks: {item.get('benchmarks')}."
                            self.documents.append({
                                "id": f"skill_{item.get('name')}",
                                "category": category,
                                "title": item.get("name"),
                                "text": content,
                                "metadata": item
                            })

                    elif category == "roadmaps":
                        for item in data:
                            levels_text = " ".join([
                                f"Level {m.get('level')}: Focus: {m.get('focus')}. Skills: {', '.join(m.get('key_skills', []))}."
                                for m in item.get("milestones", [])
                            ])
                            content = f"Career Track: {item.get('track')}. Target Roles: {', '.join(item.get('target_roles', []))}. " \
                                      f"Milestones: {levels_text} Advice: {item.get('transition_advice')}."
                            self.documents.append({
                                "id": f"roadmap_{item.get('track')}",
                                "category": category,
                                "title": item.get("track"),
                                "text": content,
                                "metadata": item
                            })

                    elif category == "resources":
                        for item in data:
                            content = f"Resource: {item.get('name')}. Category: {item.get('category')}. " \
                                      f"Provider: {item.get('provider')}. Target Skills: {', '.join(item.get('target_skills', []))}. " \
                                      f"Level: {item.get('level')}. Description: {item.get('description')}."
                            self.documents.append({
                                "id": f"resource_{item.get('name')}",
                                "category": category,
                                "title": item.get("name"),
                                "text": content,
                                "metadata": item
                            })

                    elif category == "guidelines":
                        for item in data:
                            content = f"Guideline: {item.get('rule')}. Category: {item.get('category')}. " \
                                      f"Importance: {item.get('importance')}. Detail: {item.get('guideline')} " \
                                      f"Actionable Recommendation: {item.get('recommendation')}."
                            self.documents.append({
                                "id": f"guideline_{item.get('rule')}",
                                "category": category,
                                "title": item.get("rule"),
                                "text": content,
                                "metadata": item
                            })

            except Exception as e:
                logger.error(f"Error loading knowledge base file {filename}: {e}")

    def build_index(self):
        """Builds TF-IDF index over all documents in knowledge base."""
        if not self.documents:
            return

        texts = [doc["text"] for doc in self.documents]
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top_k most relevant documents for a given query,
        optionally filtered by categories.
        """
        if not self.documents or not self.vectorizer or not query.strip():
            return []

        # Filter candidate indices if categories requested
        candidate_indices = [
            i for i, doc in enumerate(self.documents)
            if categories is None or doc["category"] in categories
        ]

        if not candidate_indices:
            return []

        query_vec = self.vectorizer.transform([query])
        sub_matrix = self.tfidf_matrix[candidate_indices]
        sims = cosine_similarity(query_vec, sub_matrix).flatten()

        top_local_idx = np.argsort(sims)[::-1][:top_k]

        results = []
        for l_idx in top_local_idx:
            score = float(sims[l_idx])
            if score > 0.01:  # Filter out completely irrelevant chunks
                actual_idx = candidate_indices[l_idx]
                doc = self.documents[actual_idx].copy()
                doc["relevance_score"] = round(score, 4)
                results.append(doc)

        return results

    def get_all_skills(self) -> List[Dict[str, Any]]:
        """Returns the full dictionary of skills."""
        return self.raw_data.get("skills", [])

    def get_learning_resources_for_skills(self, skills: List[str]) -> List[Dict[str, Any]]:
        """Matches learning resources against a list of target skills."""
        resources = self.raw_data.get("resources", [])
        matched = []
        skills_lower = {s.lower() for s in skills}

        for res in resources:
            target_skills = [t.lower() for t in res.get("target_skills", [])]
            # Check overlap
            overlap = set(target_skills).intersection(skills_lower)
            if overlap:
                item = res.copy()
                item["matched_skills"] = list(overlap)
                matched.append(item)
        return matched

    def get_career_roadmaps(self) -> List[Dict[str, Any]]:
        """Returns all career roadmaps."""
        return self.raw_data.get("roadmaps", [])

    def get_resume_guidelines(self) -> List[Dict[str, Any]]:
        """Returns all resume writing guidelines."""
        return self.raw_data.get("guidelines", [])

    def format_context_for_prompt(self, docs: List[Dict[str, Any]]) -> str:
        """Formats retrieved documents into a clean context block."""
        if not docs:
            return "No specific knowledge base context found."

        formatted_chunks = []
        for i, doc in enumerate(docs, 1):
            category = doc.get("category", "General").title()
            title = doc.get("title", "Untitled")
            text = doc.get("text", "")
            score = doc.get("relevance_score", 0.0)
            formatted_chunks.append(f"[{i}] [{category}] {title} (Relevance: {score})\n{text}")

        return "\n\n".join(formatted_chunks)

# Global singleton RAG instance
rag_engine = RAGEngine()
