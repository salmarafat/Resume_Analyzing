/**
 * Career Advisor & Resume Improvement Module (FR-5, AI Agent & RAG).
 * Provides weakness and gap analysis, learning resources, and an interactive RAG chat agent.
 */

const careerAdvisor = {
  chatHistory: [],

  init() {
    this.attachEventListeners();
  },

  attachEventListeners() {
    const chatForm = document.getElementById("chat-form");
    if (chatForm) {
      chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        await this.handleSendMessage();
      });
    }

    // Quick prompt buttons
    document.querySelectorAll(".quick-prompt-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const text = btn.textContent.replace(/^[^\w]+/, "").trim();
        const input = document.getElementById("chat-user-input");
        if (input) {
          input.value = text;
          this.handleSendMessage();
        }
      });
    });

    // Knowledge base search
    const kbForm = document.getElementById("kb-search-form");
    if (kbForm) {
      kbForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        await this.handleKBSearch();
      });
    }
  },

  async fetchImprovements() {
    const resume = resumeManager.activeResume;
    const container = document.getElementById("improvements-content");
    if (!container) return;

    if (!resume) {
      container.innerHTML = `
        <div class="card" style="text-align:center;padding:3rem 1rem;">
          <div style="font-size:3rem;margin-bottom:1rem;">🚀</div>
          <h3>Select or Upload a Resume First</h3>
          <p style="color:var(--text-muted);max-width:450px;margin:0 auto 1.5rem;">
            Resume improvement guidance, roadmap milestones, and certification recommendations require an active resume.
          </p>
          <button class="btn btn-primary" onclick="window.app.switchTab('resume-tab')">Upload Resume</button>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div style="text-align:center;padding:2rem;">
        <div class="upload-icon" style="animation: spin 1s infinite linear;">⚙️</div>
        <p>Career Advisor Agent is synthesizing RAG roadmaps and learning resources...</p>
      </div>
    `;

    try {
      const data = await api.get(`/api/career/improve/${resume.id}`);
      this.renderImprovements(data);
    } catch (err) {
      console.error("Failed to fetch improvements:", err);
      container.innerHTML = `
        <div class="card" style="text-align:center;padding:2rem;">
          <p style="color:var(--danger);">${err.detail || "Unable to load improvements."}</p>
        </div>
      `;
    }
  },

  renderImprovements(data) {
    const container = document.getElementById("improvements-content");
    if (!container) return;

    container.innerHTML = `
      <!-- Strengths and Weaknesses -->
      <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(320px, 1fr));gap:1.5rem;margin-bottom:1.5rem;">
        <div class="card" style="margin-bottom:0;border-top:4px solid var(--success);">
          <h3 class="card-title" style="color:var(--success);">✓ Key Profile Strengths</h3>
          <ul style="padding-left:1.25rem;margin-top:0.75rem;">
            ${data.strengths.map(s => `<li style="margin-bottom:0.5rem;font-size:0.9rem;">${s}</li>`).join("")}
          </ul>
        </div>

        <div class="card" style="margin-bottom:0;border-top:4px solid var(--danger);">
          <h3 class="card-title" style="color:var(--danger);">⚠️ Identified Weaknesses & Gaps</h3>
          <ul style="padding-left:1.25rem;margin-top:0.75rem;">
            ${data.weaknesses.map(w => `<li style="margin-bottom:0.5rem;font-size:0.9rem;">${w}</li>`).join("")}
          </ul>
        </div>
      </div>

      <!-- Actionable Improvements -->
      <div class="card">
        <h3 class="card-title">📝 Actionable Resume Enhancements (RAG Guidelines)</h3>
        <p class="card-subtitle">Recommended immediate revisions to increase recruiter callbacks and ATS pass rates.</p>
        <div style="display:flex;flex-direction:column;gap:0.75rem;margin-top:1rem;">
          ${data.actionable_improvements.map((tip, idx) => `
            <div style="display:flex;align-items:flex-start;gap:0.75rem;background:#f8fafc;padding:0.85rem 1rem;border-radius:var(--radius-md);border-left:3px solid var(--primary);">
              <span style="font-weight:700;color:var(--primary);min-width:24px;">#${idx + 1}</span>
              <span style="font-size:0.9rem;line-height:1.4;">${tip}</span>
            </div>
          `).join("")}
        </div>
      </div>

      <!-- Recommended Certifications -->
      <div class="card">
        <h3 class="card-title">🎓 High-Impact Industry Certifications</h3>
        <p class="card-subtitle">Verified credentials retrieved from our Knowledge Base that validate your target competencies.</p>
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:1rem;margin-top:1rem;">
          ${data.recommended_certifications.map(cert => `
            <div style="border:1px solid var(--border-color);border-radius:var(--radius-md);padding:1rem;background:#fff;display:flex;flex-direction:column;justify-content:space-between;">
              <div>
                <span class="badge badge-primary" style="font-size:0.7rem;margin-bottom:0.4rem;">${cert.provider}</span>
                <h4 style="font-size:0.95rem;font-weight:700;margin-bottom:0.3rem;">${cert.name}</h4>
                <p style="font-size:0.82rem;color:var(--text-muted);margin-bottom:0.75rem;">${cert.description}</p>
              </div>
              <div>
                <a href="${cert.url}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-outline" style="width:100%;">
                  View Official Certification ↗
                </a>
              </div>
            </div>
          `).join("")}
        </div>
      </div>

      <!-- Missing Skills & Curated Learning Roadmap -->
      <div class="card">
        <h3 class="card-title">📚 Targeted Skill Roadmap & Learning Resources</h3>
        <p class="card-subtitle">Curated courses, docs, and tutorials to close your identified skill gaps.</p>
        <div style="display:flex;flex-direction:column;gap:1rem;margin-top:1rem;">
          ${data.missing_skills_roadmap.map(item => `
            <div style="background:#f8fafc;border:1px solid var(--border-color);border-radius:var(--radius-md);padding:1.25rem;">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;flex-wrap:wrap;gap:0.5rem;">
                <div style="display:flex;align-items:center;gap:0.5rem;">
                  <span class="skill-chip missing" style="font-weight:700;">${item.skill}</span>
                  <span class="badge badge-gray">${item.category}</span>
                </div>
              </div>
              <p style="font-size:0.85rem;color:#475569;margin-bottom:0.75rem;">${item.description}</p>
              
              ${item.learning_resources && item.learning_resources.length ? `
                <div style="font-size:0.78rem;font-weight:700;text-transform:uppercase;color:var(--text-muted);margin-bottom:0.4rem;">Recommended Courses:</div>
                <div style="display:flex;flex-direction:column;gap:0.4rem;">
                  ${item.learning_resources.map(res => `
                    <div style="display:flex;justify-content:space-between;align-items:center;background:#fff;padding:0.5rem 0.75rem;border-radius:var(--radius-sm);border:1px solid #e2e8f0;font-size:0.85rem;">
                      <div>
                        <strong>${res.name}</strong> <span style="color:var(--text-muted);">(${res.provider})</span>
                      </div>
                      <a href="${res.url}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-outline" style="padding:0.15rem 0.5rem;font-size:0.75rem;">Open ↗</a>
                    </div>
                  `).join("")}
                </div>
              ` : ''}
            </div>
          `).join("")}
        </div>
      </div>
    `;
  },

  async handleSendMessage() {
    const input = document.getElementById("chat-user-input");
    const message = input.value.trim();
    if (!message) return;

    if (!auth.isAuthenticated()) {
      showToast("Please log in to chat with the AI Career Advisor.", "error");
      auth.openModal("login");
      return;
    }

    input.value = "";
    this.appendMessage("user", message);

    const sendBtn = document.getElementById("chat-send-btn");
    if (sendBtn) sendBtn.disabled = true;

    const resumeId = resumeManager.activeResume?.id || null;

    try {
      const res = await api.post("/api/career/chat", {
        resume_id: resumeId,
        message: message
      });
      this.appendMessage("assistant", res.message, res.retrieved_sources);
    } catch (err) {
      this.appendMessage("assistant", `Error: ${err.detail || "Failed to reach AI Career Advisor."}`);
    } finally {
      if (sendBtn) sendBtn.disabled = false;
    }
  },

  appendMessage(role, text, sources = []) {
    const chatContainer = document.getElementById("chat-messages-box");
    if (!chatContainer) return;

    const bubble = document.createElement("div");
    bubble.className = `message-bubble ${role}`;

    // Simple markdown renderer for headers, bold, bullets
    let formatted = text
      .replace(/^### (.*$)/gim, '<h4 style="margin:0.5rem 0 0.25rem;font-size:1rem;color:var(--primary);">$1</h4>')
      .replace(/^## (.*$)/gim, '<h3 style="margin:0.5rem 0 0.25rem;font-size:1.1rem;color:var(--primary);">$1</h3>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener" style="color:var(--primary);text-decoration:underline;">$1</a>')
      .replace(/\n/g, '<br>');

    let sourcesHtml = "";
    if (sources && sources.length > 0) {
      sourcesHtml = `
        <div class="message-sources">
          <strong>🔍 Grounded in Knowledge Base Sources (${sources.length}):</strong>
          <div style="display:flex;flex-wrap:wrap;gap:0.3rem;margin-top:0.3rem;">
            ${sources.map(s => `
              <span class="badge badge-gray" title="${s.title}" style="cursor:help;">
                📚 ${s.category.toUpperCase()}: ${s.title} (${Math.round(s.relevance_score * 100)}%)
              </span>
            `).join("")}
          </div>
        </div>
      `;
    }

    bubble.innerHTML = formatted + sourcesHtml;
    chatContainer.appendChild(bubble);
    chatContainer.scrollTop = chatContainer.scrollHeight;
  },

  async handleKBSearch() {
    const query = document.getElementById("kb-query-input").value.trim();
    const category = document.getElementById("kb-category-select").value;
    const resultsContainer = document.getElementById("kb-results-list");

    if (!query) return;

    resultsContainer.innerHTML = `<p style="color:var(--text-muted);">Searching Knowledge Base...</p>`;

    try {
      const url = `/api/career/knowledge/search?query=${encodeURIComponent(query)}${category ? `&category=${category}` : ''}&top_k=6`;
      const data = await api.get(url);

      if (data.results.length === 0) {
        resultsContainer.innerHTML = `<p style="color:var(--text-muted);">No matching knowledge chunks found.</p>`;
        return;
      }

      resultsContainer.innerHTML = data.results.map(r => `
        <div style="padding:0.75rem;background:#fff;border:1px solid var(--border-color);border-radius:var(--radius-md);margin-bottom:0.75rem;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.25rem;">
            <strong style="font-size:0.92rem;color:var(--primary);">${r.title}</strong>
            <span class="badge badge-primary">${r.category}</span>
          </div>
          <p style="font-size:0.84rem;color:#475569;line-height:1.4;">${r.text}</p>
          <div style="font-size:0.75rem;color:var(--text-muted);margin-top:0.35rem;">Relevance Score: ${(r.relevance_score * 100).toFixed(1)}%</div>
        </div>
      `).join("");
    } catch (e) {
      resultsContainer.innerHTML = `<p style="color:var(--danger);">Search failed.</p>`;
    }
  }
};
