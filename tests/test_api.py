import sys
from pathlib import Path
import unittest
from fastapi.testclient import TestClient

# Set up paths
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.database import init_db
from app.services.seed_data import seed_initial_data

class TestAIResumeAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_initial_data()
        cls.client = TestClient(app)

    def test_01_health_check(self):
        """Verify system health endpoint and RAG index loading."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertGreater(data["rag_documents_indexed"], 0)

    def test_02_auth_flow(self):
        """Test user registration and login flow (FR-1)."""
        reg_payload = {
            "email": "testuser_unittest@example.com",
            "username": "unittest_user",
            "password": "securepassword123",
            "full_name": "Unit Tester",
            "role": "job_seeker"
        }
        r = self.client.post("/api/auth/register", json=reg_payload)
        self.assertIn(r.status_code, [201, 400])

        login_payload = {
            "email_or_username": "demo@resume.ai",
            "password": "password123"
        }
        r_login = self.client.post("/api/auth/login", json=login_payload)
        self.assertEqual(r_login.status_code, 200)
        login_data = r_login.json()
        self.assertIn("access_token", login_data)
        self.assertEqual(login_data["user"]["email"], "demo@resume.ai")

    def test_03_jobs_management_and_search(self):
        """Test FR-6 (Job Management) and FR-7 (Job Search)."""
        r = self.client.get("/api/jobs")
        self.assertEqual(r.status_code, 200)
        jobs = r.json()
        self.assertGreater(len(jobs), 0)

        # Search with keyword
        r_kw = self.client.get("/api/jobs?keyword=Python")
        self.assertEqual(r_kw.status_code, 200)
        self.assertGreater(len(r_kw.json()), 0)

        # Login to obtain token
        login_res = self.client.post("/api/auth/login", json={
            "email_or_username": "demo@resume.ai",
            "password": "password123"
        }).json()
        token = login_res["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create job
        new_job = {
            "title": "Automated Test Engineer",
            "company": "Quality Assurance Global",
            "location": "Remote",
            "employment_type": "Full-time",
            "experience_level": "Mid",
            "salary_range": "$95k - $125k",
            "department": "Engineering",
            "description": "Responsible for designing and executing automated API and UI tests using Pytest and Selenium.",
            "required_skills": ["Python", "Pytest", "Git", "REST APIs"],
            "preferred_skills": ["Docker", "CI/CD"]
        }
        r_create = self.client.post("/api/jobs", json=new_job, headers=headers)
        self.assertEqual(r_create.status_code, 201)
        created_id = r_create.json()["id"]

        # View job
        r_view = self.client.get(f"/api/jobs/{created_id}")
        self.assertEqual(r_view.status_code, 200)
        self.assertEqual(r_view.json()["title"], "Automated Test Engineer")

        # Delete job
        r_del = self.client.delete(f"/api/jobs/{created_id}", headers=headers)
        self.assertEqual(r_del.status_code, 200)

    def test_04_resume_upload_and_analysis(self):
        """Test FR-2 (Upload) and FR-3 (Analysis)."""
        login_res = self.client.post("/api/auth/login", json={
            "email_or_username": "demo@resume.ai",
            "password": "password123"
        }).json()
        token = login_res["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        sample_path = BASE_DIR / "sample_resumes" / "sample_software_engineer.docx"
        self.assertTrue(sample_path.exists())

        with open(sample_path, "rb") as f:
            r_upload = self.client.post(
                "/api/resumes/upload",
                files={"file": ("sample_software_engineer.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                headers=headers
            )

        self.assertEqual(r_upload.status_code, 201)
        resume_data = r_upload.json()
        self.assertIsNotNone(resume_data["analysis"])
        an = resume_data["analysis"]
        self.assertIn("Jordan Miller", an["candidate_name"])
        self.assertGreater(len(an["technical_skills"]), 0)
        self.assertGreater(an["ats_score"], 50)

        resume_id = resume_data["id"]

        # Test FR-4: Recommendations
        r_rec = self.client.get(f"/api/recommendations/resume/{resume_id}", headers=headers)
        self.assertEqual(r_rec.status_code, 200)
        rec_data = r_rec.json()
        self.assertGreater(len(rec_data["recommendations"]), 0)
        top_match = rec_data["recommendations"][0]
        self.assertIn("match_score", top_match)
        self.assertGreater(top_match["match_score"], 0)
        self.assertGreater(len(top_match["matched_skills"]), 0)

        # Test FR-5: Resume Improvements
        r_imp = self.client.get(f"/api/career/improve/{resume_id}", headers=headers)
        self.assertEqual(r_imp.status_code, 200)
        imp_data = r_imp.json()
        self.assertGreater(len(imp_data["strengths"]), 0)
        self.assertGreater(len(imp_data["actionable_improvements"]), 0)
        self.assertGreater(len(imp_data["recommended_certifications"]), 0)

        # Test Career Advisor Chat Agent with RAG
        chat_payload = {
            "resume_id": resume_id,
            "message": "What certifications should I pursue to strengthen my backend profile?"
        }
        r_chat = self.client.post("/api/career/chat", json=chat_payload, headers=headers)
        self.assertEqual(r_chat.status_code, 200)
        chat_data = r_chat.json()
        self.assertEqual(chat_data["role"], "assistant")
        self.assertGreater(len(chat_data["retrieved_sources"]), 0)

    def test_05_knowledge_base_search(self):
        """Test RAG knowledge base direct search."""
        r = self.client.get("/api/career/knowledge/search?query=FastAPI")
        self.assertEqual(r.status_code, 200)
        kb_data = r.json()
        self.assertGreater(kb_data["count"], 0)

if __name__ == "__main__":
    unittest.main()
