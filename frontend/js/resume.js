/**
 * Resume management and analysis module (FR-2, FR-3).
 * Handles file uploads, drag-and-drop, analysis report rendering, and active resume selection.
 */

const resumeManager = {
  resumes: [],
  activeResume: null,

  init() {
    this.attachEventListeners();
  },

  attachEventListeners() {
    const dropZone = document.getElementById("resume-drop-zone");
    const fileInput = document.getElementById("resume-file-input");

    if (dropZone && fileInput) {
      dropZone.addEventListener("click", () => fileInput.click());

      dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
      });

      dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("dragover");
      });

      dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        if (e.dataTransfer.files.length) {
          this.handleFileUpload(e.dataTransfer.files[0]);
        }
      });

      fileInput.addEventListener("change", (e) => {
        if (e.target.files.length) {
          this.handleFileUpload(e.target.files[0]);
        }
      });
    }

    // Re-analyze button
    const reanalyzeBtn = document.getElementById("btn-reanalyze-resume");
    if (reanalyzeBtn) {
      reanalyzeBtn.addEventListener("click", () => this.reanalyzeCurrent());
    }

    // Sample resume load shortcuts
    const sampleSeBtn = document.getElementById("btn-load-sample-se");
    if (sampleSeBtn) {
      sampleSeBtn.addEventListener("click", () => this.loadSampleResume("sample_software_engineer.docx"));
    }
    const sampleDsBtn = document.getElementById("btn-load-sample-ds");
    if (sampleDsBtn) {
      sampleDsBtn.addEventListener("click", () => this.loadSampleResume("sample_data_scientist.docx"));
    }
  },

  async fetchMyResumes() {
    if (!auth.isAuthenticated()) return;
    try {
      this.resumes = await api.get("/api/resumes/my");
      this.renderResumeList();

      if (this.resumes.length > 0 && !this.activeResume) {
        this.setActiveResume(this.resumes[0]);
      } else if (this.resumes.length === 0) {
        this.activeResume = null;
        this.updateActiveBadge();
        this.renderEmptyAnalysis();
      }
    } catch (err) {
      console.error("Failed to fetch resumes:", err);
    }
  },

  async handleFileUpload(file) {
    if (!auth.isAuthenticated()) {
      showToast("Please sign in or use the demo login to upload resumes.", "error");
      auth.openModal("login");
      return;
    }

    const ext = file.name.split(".").pop().toLowerCase();
    if (ext !== "pdf" && ext !== "docx") {
      showToast("Only PDF (.pdf) and Word (.docx) files are supported.", "error");
      return;
    }

    const loader = document.getElementById("upload-spinner");
    const dropContent = document.getElementById("drop-zone-content");
    if (loader) loader.style.display = "block";
    if (dropContent) dropContent.style.opacity = "0.3";

    try {
      showToast("Analyzing resume with AI Agents...", "info");
      const uploaded = await api.upload("/api/resumes/upload", file);
      showToast("Resume parsed and analyzed successfully!", "success");
      await this.fetchMyResumes();
      this.setActiveResume(uploaded);
    } catch (err) {
      showToast(err.detail || "Failed to analyze resume.", "error");
    } finally {
      if (loader) loader.style.display = "none";
      if (dropContent) dropContent.style.opacity = "1";
    }
  },

  async loadSampleResume(filename) {
    if (!auth.isAuthenticated()) {
      showToast("Signing into demo account for sample...", "info");
      try {
        const res = await api.post("/api/auth/login", {
          email_or_username: "demo@resume.ai",
          password: "password123"
        });
        api.setToken(res.access_token);
        api.setUser(res.user);
        auth.currentUser = res.user;
        auth.updateUI();
      } catch (e) {
        showToast("Authentication required.", "error");
        return;
      }
    }

    try {
      showToast(`Loading ${filename}...`, "info");
      // Fetch sample docx from static server
      const response = await fetch(`/sample_resumes/${filename}`);
      const blob = await response.blob();
      const file = new File([blob], filename, { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });
      await this.handleFileUpload(file);
    } catch (e) {
      showToast("Could not load sample file directly. Please use the Upload button.", "error");
    }
  },

  setActiveResume(resume) {
    this.activeResume = resume;
    this.updateActiveBadge();
    this.renderAnalysis(resume);
    this.highlightResumeCard(resume.id);

    // Notify other modules to refresh based on active resume
    if (window.recommendationManager) {
      window.recommendationManager.fetchRecommendations();
    }
    if (window.careerAdvisor) {
      window.careerAdvisor.fetchImprovements();
    }
  },

  updateActiveBadge() {
    const badge = document.getElementById("active-resume-badge");
    if (!badge) return;
    if (this.activeResume) {
      const name = this.activeResume.analysis?.candidate_name || this.activeResume.file_name;
      badge.innerHTML = `📄 Active: <strong>${name}</strong>`;
      badge.style.display = "inline-flex";
    } else {
      badge.innerHTML = `📄 No Resume Active`;
      badge.style.display = "none";
    }
  },

  renderResumeList() {
    const container = document.getElementById("uploaded-resumes-list");
    if (!container) return;

    if (this.resumes.length === 0) {
      container.innerHTML = `<div style="color:var(--text-muted);font-size:0.85rem;padding:0.5rem 0;">No resumes uploaded yet.</div>`;
      return;
    }

    container.innerHTML = this.resumes.map(r => `
      <div class="resume-pill ${this.activeResume?.id === r.id ? 'active' : ''}" 
           data-id="${r.id}"
           style="display:flex;align-items:center;justify-content:space-between;padding:0.75rem 1rem;background:#f8fafc;border:1px solid ${this.activeResume?.id === r.id ? 'var(--primary)' : 'var(--border-color)'};border-radius:var(--radius-md);margin-bottom:0.5rem;cursor:pointer;">
        <div style="min-width:0;flex:1;">
          <div style="font-weight:600;font-size:0.88rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
            ${r.analysis?.candidate_name || r.file_name}
          </div>
          <div style="font-size:0.75rem;color:var(--text-muted);">
            Score: <strong style="color:var(--primary);">${r.analysis?.ats_score || 0}/100</strong> • ${r.file_type.toUpperCase()} • ${(r.file_size / 1024).toFixed(1)} KB
          </div>
        </div>
        <div style="display:flex;gap:0.4rem;margin-left:0.5rem;">
          <button class="btn btn-sm btn-outline select-resume-btn" data-id="${r.id}" style="padding:0.2rem 0.5rem;font-size:0.75rem;">View</button>
          <button class="btn btn-sm btn-danger delete-resume-btn" data-id="${r.id}" style="padding:0.2rem 0.5rem;font-size:0.75rem;">×</button>
        </div>
      </div>
    `).join("");

    container.querySelectorAll(".select-resume-btn").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const id = parseInt(btn.dataset.id);
        const selected = this.resumes.find(x => x.id === id);
        if (selected) this.setActiveResume(selected);
      });
    });

    container.querySelectorAll(".resume-pill").forEach(pill => {
      pill.addEventListener("click", () => {
        const id = parseInt(pill.dataset.id);
        const selected = this.resumes.find(x => x.id === id);
        if (selected) this.setActiveResume(selected);
      });
    });

    container.querySelectorAll(".delete-resume-btn").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const id = parseInt(btn.dataset.id);
        if (confirm("Are you sure you want to delete this resume?")) {
          try {
            await api.delete(`/api/resumes/${id}`);
            showToast("Resume deleted successfully.", "info");
            await this.fetchMyResumes();
          } catch (err) {
            showToast("Failed to delete resume.", "error");
          }
        }
      });
    });
  },

  highlightResumeCard(activeId) {
    document.querySelectorAll(".resume-pill").forEach(p => {
      if (parseInt(p.dataset.id) === activeId) {
        p.style.borderColor = "var(--primary)";
        p.style.backgroundColor = "var(--primary-light)";
      } else {
        p.style.borderColor = "var(--border-color)";
        p.style.backgroundColor = "#f8fafc";
      }
    });
  },

  renderAnalysis(resume) {
    const container = document.getElementById("analysis-report-view");
    if (!container) return;

    const an = resume.analysis;
    if (!an) {
      this.renderEmptyAnalysis();
      return;
    }

    container.style.display = "block";

    // ATS Gauge
    const atsScore = an.ats_score || 0;
    const scoreBox = document.getElementById("ats-score-display");
    if (scoreBox) {
      scoreBox.innerHTML = `
        <div class="ats-score-circle" style="--score-pct: ${atsScore};">
          <div class="ats-score-inner">
            <span>${atsScore}</span>
            <span>ATS Score</span>
          </div>
        </div>
        <div>
          <h4 style="font-size:1.1rem;margin-bottom:0.25rem;">
            ${atsScore >= 80 ? "✨ Excellent ATS Match" : atsScore >= 65 ? "👍 Competitive Profile" : "⚠️ Needs Improvement"}
          </h4>
          <p style="font-size:0.85rem;color:var(--text-muted);">
            Evaluated on section structure, action verbs, quantified accomplishments, and skill density.
          </p>
        </div>
      `;
    }

    // Candidate Info
    const candidateName = document.getElementById("report-candidate-name");
    const candidateContact = document.getElementById("report-candidate-contact");
    if (candidateName) candidateName.textContent = an.candidate_name || "Candidate Profile";
    if (candidateContact) {
      candidateContact.innerHTML = `
        <span>📧 ${an.email || "No email detected"}</span> • 
        <span>📱 ${an.phone || "No phone detected"}</span> • 
        <span>📁 ${resume.file_name}</span>
      `;
    }

    // Executive Summary
    const summaryElem = document.getElementById("report-summary-text");
    if (summaryElem) summaryElem.textContent = an.summary || "No executive summary available.";

    // Technical Skills
    const techContainer = document.getElementById("report-tech-skills");
    if (techContainer) {
      if (an.technical_skills && an.technical_skills.length) {
        techContainer.innerHTML = an.technical_skills.map(s => `
          <span class="skill-chip tech">💻 ${s}</span>
        `).join("");
      } else {
        techContainer.innerHTML = `<span style="color:var(--text-muted);font-size:0.85rem;">No technical skills detected.</span>`;
      }
    }

    // Soft Skills
    const softContainer = document.getElementById("report-soft-skills");
    if (softContainer) {
      if (an.soft_skills && an.soft_skills.length) {
        softContainer.innerHTML = an.soft_skills.map(s => `
          <span class="skill-chip soft">🤝 ${s}</span>
        `).join("");
      } else {
        softContainer.innerHTML = `<span style="color:var(--text-muted);font-size:0.85rem;">No soft skills detected.</span>`;
      }
    }

    // Experience
    const expContainer = document.getElementById("report-experience-list");
    if (expContainer) {
      if (an.experience && an.experience.length) {
        expContainer.innerHTML = an.experience.map(e => `
          <div style="margin-bottom:1rem;padding-left:1rem;border-left:3px solid var(--primary);">
            <div style="font-weight:700;font-size:0.95rem;">${e.title}</div>
            <div style="font-size:0.8rem;color:var(--text-muted);">${e.company || ""} • ${e.duration || ""}</div>
            <div style="font-size:0.88rem;margin-top:0.35rem;line-height:1.4;">${e.description}</div>
          </div>
        `).join("");
      } else {
        expContainer.innerHTML = `<span style="color:var(--text-muted);font-size:0.85rem;">No experience entries extracted.</span>`;
      }
    }

    // Education
    const eduContainer = document.getElementById("report-education-list");
    if (eduContainer) {
      if (an.education && an.education.length) {
        eduContainer.innerHTML = an.education.map(ed => `
          <div style="margin-bottom:0.75rem;padding-left:1rem;border-left:3px solid var(--accent);">
            <div style="font-weight:700;font-size:0.95rem;">${ed.degree}</div>
            <div style="font-size:0.82rem;color:var(--text-muted);">${ed.institution || ""} ${ed.year ? `(${ed.year})` : ""}</div>
          </div>
        `).join("");
      } else {
        eduContainer.innerHTML = `<span style="color:var(--text-muted);font-size:0.85rem;">No education history extracted.</span>`;
      }
    }

    // Tips from RAG Guidelines
    const tipsContainer = document.getElementById("report-tips-list");
    if (tipsContainer) {
      if (an.improvement_tips && an.improvement_tips.length) {
        tipsContainer.innerHTML = an.improvement_tips.map(t => `
          <li style="margin-bottom:0.5rem;font-size:0.9rem;display:flex;align-items:flex-start;gap:0.5rem;">
            <span style="color:var(--warning);">⚡</span>
            <span>${t}</span>
          </li>
        `).join("");
      } else {
        tipsContainer.innerHTML = `<li>No critical issues found! Resume looks solid.</li>`;
      }
    }
  },

  renderEmptyAnalysis() {
    const container = document.getElementById("analysis-report-view");
    if (container) {
      container.innerHTML = `
        <div class="card" style="text-align:center;padding:3rem 1rem;">
          <div style="font-size:3rem;margin-bottom:1rem;">📄</div>
          <h3>No Resume Uploaded</h3>
          <p style="color:var(--text-muted);max-width:400px;margin:0 auto 1.5rem;">
            Upload your resume in PDF or Word (.docx) format above to generate a comprehensive AI analysis report.
          </p>
        </div>
      `;
    }
  },

  async reanalyzeCurrent() {
    if (!this.activeResume) return;
    try {
      showToast("Re-analyzing resume with AI...", "info");
      const updated = await api.post(`/api/resumes/${this.activeResume.id}/reanalyze`, {});
      this.setActiveResume(updated);
      showToast("Resume re-analysis complete!", "success");
    } catch (e) {
      showToast("Failed to re-analyze resume.", "error");
    }
  }
};
