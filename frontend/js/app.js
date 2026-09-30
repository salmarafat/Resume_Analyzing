/**
 * Main application coordinator.
 * Manages tab transitions, global toasts, and initialization.
 */

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'}</span>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

const app = {
  activeTab: "dashboard-tab",

  init() {
    this.setupNavigation();
    auth.init();
    resumeManager.init();
    jobManager.init();
    recommendationManager.init();
    careerAdvisor.init();

    this.loadInitialData();
  },

  setupNavigation() {
    document.querySelectorAll(".nav-link").forEach(link => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const tabTarget = link.dataset.tab;
        if (tabTarget) {
          this.switchTab(tabTarget);
        }
      });
    });

    // Close modals on overlay click or close button
    document.querySelectorAll(".modal-overlay").forEach(overlay => {
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) overlay.classList.remove("active");
      });
    });

    document.querySelectorAll(".modal-close").forEach(btn => {
      btn.addEventListener("click", () => {
        btn.closest(".modal-overlay")?.classList.remove("active");
      });
    });
  },

  switchTab(tabId) {
    this.activeTab = tabId;

    // Update nav links active class
    document.querySelectorAll(".nav-link").forEach(link => {
      if (link.dataset.tab === tabId) {
        link.classList.add("active");
      } else {
        link.classList.remove("active");
      }
    });

    // Update tab panes
    document.querySelectorAll(".tab-pane").forEach(pane => {
      if (pane.id === tabId) {
        pane.classList.add("active");
      } else {
        pane.classList.remove("active");
      }
    });

    // Update Header title
    const titles = {
      "dashboard-tab": "Overview & Intelligence Dashboard",
      "resume-tab": "Resume Upload & Semantic Analyzer",
      "jobs-tab": "Job Board & Management",
      "recommendations-tab": "AI Job Recommendations & Fit Scoring",
      "improvements-tab": "Resume Improvement & Gap Roadmaps",
      "advisor-tab": "Interactive AI Career Advisor (RAG)",
      "kb-tab": "Knowledge Base & Guidelines Explorer"
    };

    const headerTitle = document.getElementById("header-page-title");
    if (headerTitle) {
      headerTitle.textContent = titles[tabId] || "AI Resume Analyzer";
    }

    // Refresh tab specific data
    if (tabId === "recommendations-tab") {
      recommendationManager.fetchRecommendations();
    } else if (tabId === "improvements-tab") {
      careerAdvisor.fetchImprovements();
    } else if (tabId === "dashboard-tab") {
      this.refreshDashboardStats();
    }
  },

  async loadInitialData() {
    await resumeManager.fetchMyResumes();
    await jobManager.fetchJobs();
    this.refreshDashboardStats();
  },

  refreshDashboardStats() {
    const totalJobsElem = document.getElementById("dash-total-jobs");
    const totalResumesElem = document.getElementById("dash-total-resumes");
    const activeScoreElem = document.getElementById("dash-active-score");

    if (totalJobsElem) totalJobsElem.textContent = jobManager.jobs.length;
    if (totalResumesElem) totalResumesElem.textContent = resumeManager.resumes.length;
    if (activeScoreElem) {
      activeScoreElem.textContent = resumeManager.activeResume?.analysis?.ats_score 
        ? `${resumeManager.activeResume.analysis.ats_score}%`
        : "--";
    }
  }
};

window.app = app;
window.auth = auth;
window.resumeManager = resumeManager;
window.jobManager = jobManager;
window.recommendationManager = recommendationManager;
window.careerAdvisor = careerAdvisor;

document.addEventListener("DOMContentLoaded", () => {
  app.init();
});
