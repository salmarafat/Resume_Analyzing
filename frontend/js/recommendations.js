/**
 * Job Recommendation Module (FR-4).
 * Evaluates candidate resume against job opportunities, computes matching scores,
 * and renders AI-generated fit explanations and skill gap analyses.
 */

const recommendationManager = {
  recommendations: [],

  init() {
    // Initialized by app
  },

  async fetchRecommendations() {
    const resume = resumeManager.activeResume;
    const container = document.getElementById("recommendations-list");
    if (!container) return;

    if (!resume) {
      container.innerHTML = `
        <div class="card" style="text-align:center;padding:3rem 1rem;">
          <div style="font-size:3rem;margin-bottom:1rem;">🎯</div>
          <h3>Select or Upload a Resume First</h3>
          <p style="color:var(--text-muted);max-width:450px;margin:0 auto 1.5rem;">
            Job recommendations are computed dynamically by comparing your active resume against all database job opportunities.
          </p>
          <button class="btn btn-primary" onclick="window.app.switchTab('resume-tab')">Go to Resume Upload</button>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div style="text-align:center;padding:2rem;">
        <div class="upload-icon" style="animation: spin 1s infinite linear;">⚙️</div>
        <p>Job Matching Agent is calculating similarity scores & skill overlaps...</p>
      </div>
    `;

    try {
      const data = await api.get(`/api/recommendations/resume/${resume.id}`);
      this.recommendations = data.recommendations || [];
      this.renderRecommendations(data);
    } catch (err) {
      console.error("Failed to fetch recommendations:", err);
      container.innerHTML = `
        <div class="card" style="text-align:center;padding:2rem;">
          <div style="color:var(--danger);font-size:2rem;margin-bottom:0.5rem;">⚠️</div>
          <p>${err.detail || "Unable to compute recommendations. Please ensure resume is analyzed."}</p>
        </div>
      `;
    }
  },

  renderRecommendations(data) {
    const container = document.getElementById("recommendations-list");
    if (!container) return;

    if (this.recommendations.length === 0) {
      container.innerHTML = `
        <div class="card" style="text-align:center;padding:3rem 1rem;">
          <h3>No Job Postings Available</h3>
          <p style="color:var(--text-muted);">Post some jobs on the Job Board to see AI matches.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div style="margin-bottom:1.5rem;display:flex;justify-content:space-between;align-items:center;">
        <div>
          <h2 style="font-size:1.3rem;font-weight:700;">
            Ranked Recommendations for <span style="color:var(--primary);">${data.candidate_name || "You"}</span>
          </h2>
          <p style="font-size:0.85rem;color:var(--text-muted);">
            Evaluated against ${data.total_jobs_evaluated} industry roles using TF-IDF Semantic Similarity & Skill Matrix
          </p>
        </div>
        <button class="btn btn-sm btn-outline" onclick="recommendationManager.fetchRecommendations()">🔄 Refresh Matches</button>
      </div>

      <div style="display:flex;flex-direction:column;gap:1.25rem;">
        ${this.recommendations.map(item => {
          const score = item.match_score;
          const scoreClass = score >= 75 ? "high" : score >= 50 ? "med" : "low";
          const scoreColor = score >= 75 ? "var(--success)" : score >= 50 ? "var(--warning)" : "var(--danger)";
          
          return `
            <div class="card match-card" id="match-card-${item.job.id}" style="border-left: 5px solid ${scoreColor};margin-bottom:0;">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;">
                <div style="flex:1;min-width:280px;">
                  <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.25rem;">
                    <h3 style="font-size:1.2rem;font-weight:700;">${item.job.title}</h3>
                    <span class="badge badge-gray">${item.job.experience_level}</span>
                  </div>
                  <div style="font-size:0.9rem;font-weight:600;color:var(--primary);margin-bottom:0.4rem;">
                    ${item.job.company} • 📍 ${item.job.location} • 💰 ${item.job.salary_range || "Competitive"}
                  </div>
                </div>

                <div style="text-align:right;min-width:140px;">
                  <div style="font-size:1.6rem;font-weight:800;color:${scoreColor};line-height:1;">
                    ${score}%
                  </div>
                  <div style="font-size:0.75rem;font-weight:600;text-transform:uppercase;color:var(--text-muted);">
                    Match Score
                  </div>
                </div>
              </div>

              <!-- Score Meter -->
              <div class="match-bar-container">
                <div class="match-bar-fill ${scoreClass}" style="width: ${score}%;"></div>
              </div>

              <!-- Skills Overview -->
              <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:1rem;margin:1rem 0;background:#f8fafc;padding:1rem;border-radius:var(--radius-md);">
                <div>
                  <div style="font-size:0.78rem;font-weight:700;color:#047857;text-transform:uppercase;margin-bottom:0.4rem;">
                    ✓ Matched Skills (${item.matched_skills.length})
                  </div>
                  <div class="skill-chips">
                    ${item.matched_skills.length 
                      ? item.matched_skills.map(s => `<span class="skill-chip matched" style="font-size:0.75rem;">${s}</span>`).join("")
                      : `<span style="font-size:0.8rem;color:var(--text-muted);">None detected</span>`}
                  </div>
                </div>

                <div>
                  <div style="font-size:0.78rem;font-weight:700;color:#b91c1c;text-transform:uppercase;margin-bottom:0.4rem;">
                    ✗ Missing Required Skills (${item.missing_skills.length})
                  </div>
                  <div class="skill-chips">
                    ${item.missing_skills.length 
                      ? item.missing_skills.map(s => `<span class="skill-chip missing" style="font-size:0.75rem;">${s}</span>`).join("")
                      : `<span style="font-size:0.8rem;color:var(--success);">All required skills satisfied! 🎉</span>`}
                  </div>
                </div>
              </div>

              <!-- Explanation Accordion -->
              <div style="margin-top:0.75rem;">
                <details style="background:#fff;border:1px solid var(--border-color);border-radius:var(--radius-md);padding:0.75rem 1rem;">
                  <summary style="font-weight:600;font-size:0.88rem;cursor:pointer;color:var(--primary);">
                    🤖 View AI Matching Explanation & Strategic Insights
                  </summary>
                  <div style="margin-top:0.75rem;font-size:0.88rem;line-height:1.6;color:#334155;white-space:pre-wrap;">
                    ${item.match_explanation}
                  </div>
                </details>
              </div>

              <div style="display:flex;justify-content:flex-end;gap:0.75rem;margin-top:1rem;padding-top:0.75rem;border-top:1px solid var(--border-color);">
                <button class="btn btn-sm btn-outline" onclick="jobManager.viewJobDetails(${item.job.id})">Full Job Description</button>
                <button class="btn btn-sm btn-primary" onclick="recommendationManager.askAdvisorAboutJob('${item.job.title}')">Ask Career Advisor About This Role</button>
              </div>
            </div>
          `;
        }).join("")}
      </div>
    `;
  },

  highlightJobMatch(jobId) {
    setTimeout(() => {
      const card = document.getElementById(`match-card-${jobId}`);
      if (card) {
        card.scrollIntoView({ behavior: "smooth", block: "center" });
        card.style.outline = "3px solid var(--primary)";
        setTimeout(() => card.style.outline = "none", 2500);
      }
    }, 300);
  },

  askAdvisorAboutJob(jobTitle) {
    window.app.switchTab("advisor-tab");
    const input = document.getElementById("chat-user-input");
    if (input) {
      input.value = `How should I tailor my resume to maximize my chances for the ${jobTitle} role, and what skill gaps should I prioritize?`;
      document.getElementById("chat-send-btn")?.click();
    }
  }
};
