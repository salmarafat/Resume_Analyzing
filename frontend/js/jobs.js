/**
 * Job Management (FR-6) & Job Search (FR-7) module.
 * Provides search filters, job listing, creation, modification, and deletion.
 */

const jobManager = {
  jobs: [],
  selectedJob: null,

  init() {
    this.attachEventListeners();
    this.fetchJobs();
  },

  attachEventListeners() {
    // Search & Filter Form
    const searchForm = document.getElementById("jobs-search-form");
    if (searchForm) {
      searchForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.fetchJobs();
      });
    }

    const resetBtn = document.getElementById("btn-reset-filters");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        document.getElementById("job-search-keyword").value = "";
        document.getElementById("job-filter-location").value = "";
        document.getElementById("job-filter-dept").value = "";
        document.getElementById("job-filter-exp").value = "";
        this.fetchJobs();
      });
    }

    // Open Add Job Modal
    const btnOpenAddJob = document.getElementById("btn-open-add-job");
    if (btnOpenAddJob) {
      btnOpenAddJob.addEventListener("click", () => {
        if (!auth.isAuthenticated()) {
          showToast("Please log in to post or manage jobs.", "error");
          auth.openModal("login");
          return;
        }
        this.openJobModal("add");
      });
    }

    // Job Form Submission (Add or Edit)
    const jobForm = document.getElementById("job-form");
    if (jobForm) {
      jobForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        await this.handleSaveJob();
      });
    }
  },

  async fetchJobs() {
    const keyword = document.getElementById("job-search-keyword")?.value.trim() || "";
    const location = document.getElementById("job-filter-location")?.value.trim() || "";
    const department = document.getElementById("job-filter-dept")?.value || "";
    const exp = document.getElementById("job-filter-exp")?.value || "";

    const params = new URLSearchParams();
    if (keyword) params.append("keyword", keyword);
    if (location) params.append("location", location);
    if (department) params.append("department", department);
    if (exp) params.append("experience_level", exp);

    const queryStr = params.toString() ? `?${params.toString()}` : "";

    try {
      this.jobs = await api.get(`/api/jobs${queryStr}`);
      this.renderJobs();
      // Update badge count
      const countBadge = document.getElementById("total-jobs-count");
      if (countBadge) countBadge.textContent = this.jobs.length;
    } catch (err) {
      console.error("Failed to fetch jobs:", err);
      showToast("Error loading jobs.", "error");
    }
  },

  renderJobs() {
    const container = document.getElementById("jobs-grid-container");
    if (!container) return;

    if (this.jobs.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; background: #fff; border-radius: var(--radius-lg); border: 1px dashed var(--border-color);">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🔍</div>
          <h3>No Jobs Found</h3>
          <p style="color: var(--text-muted);">Try adjusting your search keywords or clearing filters.</p>
        </div>
      `;
      return;
    }

    const currentUserId = auth.currentUser?.id;
    const isAdmin = auth.currentUser?.role === "admin";

    container.innerHTML = this.jobs.map(job => {
      const isOwner = currentUserId && (job.posted_by === currentUserId || isAdmin);
      return `
        <div class="card job-card" style="display:flex;flex-direction:column;justify-content:space-between;height:100%;">
          <div>
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.75rem;">
              <div>
                <h3 style="font-size:1.15rem;font-weight:700;color:var(--text-main);margin-bottom:0.2rem;">${job.title}</h3>
                <div style="font-size:0.9rem;font-weight:600;color:var(--primary);">${job.company}</div>
              </div>
              <span class="badge badge-primary">${job.experience_level}</span>
            </div>

            <div style="font-size:0.82rem;color:var(--text-muted);display:flex;gap:0.75rem;margin-bottom:0.75rem;flex-wrap:wrap;">
              <span>📍 ${job.location}</span>
              <span>💼 ${job.employment_type}</span>
              <span>💰 ${job.salary_range || "Competitive"}</span>
            </div>

            <p style="font-size:0.88rem;color:#475569;margin-bottom:1rem;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;">
              ${job.description.replace(/\n/g, " ")}
            </p>

            <div style="margin-bottom:1rem;">
              <div style="font-size:0.75rem;font-weight:600;text-transform:uppercase;color:var(--text-muted);margin-bottom:0.3rem;">Required Skills:</div>
              <div class="skill-chips">
                ${job.required_skills.slice(0, 5).map(s => `<span class="skill-chip tech" style="font-size:0.75rem;">${s}</span>`).join("")}
                ${job.required_skills.length > 5 ? `<span class="badge badge-gray">+${job.required_skills.length - 5}</span>` : ""}
              </div>
            </div>
          </div>

          <div style="display:flex;justify-content:space-between;align-items:center;padding-top:1rem;border-top:1px solid var(--border-color);margin-top:auto;">
            <button class="btn btn-sm btn-outline btn-view-job" data-id="${job.id}">View Details</button>
            <div style="display:flex;gap:0.4rem;">
              ${isOwner ? `
                <button class="btn btn-sm btn-secondary btn-edit-job" data-id="${job.id}">Edit</button>
                <button class="btn btn-sm btn-danger btn-delete-job" data-id="${job.id}">Delete</button>
              ` : `
                <button class="btn btn-sm btn-primary btn-match-job" data-id="${job.id}">Match with Resume</button>
              `}
            </div>
          </div>
        </div>
      `;
    }).join("");

    // Attach card event listeners
    container.querySelectorAll(".btn-view-job").forEach(btn => {
      btn.addEventListener("click", () => this.viewJobDetails(parseInt(btn.dataset.id)));
    });

    container.querySelectorAll(".btn-edit-job").forEach(btn => {
      btn.addEventListener("click", () => this.openEditJob(parseInt(btn.dataset.id)));
    });

    container.querySelectorAll(".btn-delete-job").forEach(btn => {
      btn.addEventListener("click", () => this.deleteJob(parseInt(btn.dataset.id)));
    });

    container.querySelectorAll(".btn-match-job").forEach(btn => {
      btn.addEventListener("click", () => {
        const jobId = parseInt(btn.dataset.id);
        if (!resumeManager.activeResume) {
          showToast("Please upload or select an active resume first.", "error");
          window.app.switchTab("resume-tab");
          return;
        }
        window.app.switchTab("recommendations-tab");
        window.recommendationManager.highlightJobMatch(jobId);
      });
    });
  },

  viewJobDetails(jobId) {
    const job = this.jobs.find(j => j.id === jobId);
    if (!job) return;

    const modal = document.getElementById("job-details-modal");
    document.getElementById("view-job-title").textContent = job.title;
    document.getElementById("view-job-company").textContent = `${job.company} • ${job.location}`;
    document.getElementById("view-job-details-meta").innerHTML = `
      <span class="badge badge-primary">${job.experience_level}</span>
      <span class="badge badge-success">${job.employment_type}</span>
      <span class="badge badge-gray">${job.department}</span>
      <span style="font-weight:600;font-size:0.9rem;">${job.salary_range || "Negotiable"}</span>
    `;

    document.getElementById("view-job-description").innerHTML = job.description.replace(/\n/g, "<br>");
    
    document.getElementById("view-job-req-skills").innerHTML = job.required_skills.map(s => `
      <span class="skill-chip tech">${s}</span>
    `).join("");

    document.getElementById("view-job-pref-skills").innerHTML = (job.preferred_skills && job.preferred_skills.length)
      ? job.preferred_skills.map(s => `<span class="skill-chip soft">${s}</span>`).join("")
      : "<span style='color:var(--text-muted);font-size:0.85rem;'>None specified</span>";

    modal.classList.add("active");
  },

  openJobModal(mode = "add", job = null) {
    const modal = document.getElementById("job-edit-modal");
    const title = document.getElementById("job-modal-title");
    document.getElementById("job-form").reset();
    document.getElementById("job-form-id").value = "";

    if (mode === "edit" && job) {
      title.textContent = "Edit Job Posting";
      document.getElementById("job-form-id").value = job.id;
      document.getElementById("job-input-title").value = job.title;
      document.getElementById("job-input-company").value = job.company;
      document.getElementById("job-input-location").value = job.location;
      document.getElementById("job-input-type").value = job.employment_type;
      document.getElementById("job-input-level").value = job.experience_level;
      document.getElementById("job-input-salary").value = job.salary_range || "";
      document.getElementById("job-input-dept").value = job.department;
      document.getElementById("job-input-desc").value = job.description;
      document.getElementById("job-input-req-skills").value = job.required_skills.join(", ");
      document.getElementById("job-input-pref-skills").value = (job.preferred_skills || []).join(", ");
    } else {
      title.textContent = "Post a New Job Opportunity";
    }

    modal.classList.add("active");
  },

  openEditJob(jobId) {
    const job = this.jobs.find(j => j.id === jobId);
    if (job) this.openJobModal("edit", job);
  },

  async handleSaveJob() {
    const id = document.getElementById("job-form-id").value;
    const title = document.getElementById("job-input-title").value.trim();
    const company = document.getElementById("job-input-company").value.trim();
    const location = document.getElementById("job-input-location").value.trim();
    const employment_type = document.getElementById("job-input-type").value;
    const experience_level = document.getElementById("job-input-level").value;
    const salary_range = document.getElementById("job-input-salary").value.trim();
    const department = document.getElementById("job-input-dept").value.trim();
    const description = document.getElementById("job-input-desc").value.trim();
    
    const req_skills_raw = document.getElementById("job-input-req-skills").value;
    const pref_skills_raw = document.getElementById("job-input-pref-skills").value;

    const required_skills = req_skills_raw.split(",").map(s => s.trim()).filter(Boolean);
    const preferred_skills = pref_skills_raw.split(",").map(s => s.trim()).filter(Boolean);

    if (required_skills.length === 0) {
      showToast("Please enter at least one required skill.", "error");
      return;
    }

    const payload = {
      title,
      company,
      location,
      employment_type,
      experience_level,
      salary_range: salary_range || null,
      department,
      description,
      required_skills,
      preferred_skills
    };

    try {
      if (id) {
        await api.put(`/api/jobs/${id}`, payload);
        showToast("Job updated successfully!", "success");
      } else {
        await api.post("/api/jobs", payload);
        showToast("Job posted successfully!", "success");
      }
      document.getElementById("job-edit-modal").classList.remove("active");
      await this.fetchJobs();
    } catch (err) {
      showToast(err.detail || "Failed to save job posting.", "error");
    }
  },

  async deleteJob(jobId) {
    if (!confirm("Are you sure you want to delete this job posting?")) return;
    try {
      await api.delete(`/api/jobs/${jobId}`);
      showToast("Job deleted successfully.", "info");
      await this.fetchJobs();
    } catch (err) {
      showToast(err.detail || "Failed to delete job.", "error");
    }
  }
};
