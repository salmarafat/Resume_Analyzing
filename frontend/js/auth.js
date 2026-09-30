/**
 * Authentication module (FR-1): Register, Login, Logout, and session management.
 */

const auth = {
  currentUser: null,

  init() {
    this.currentUser = api.getUser();
    this.updateUI();
    this.attachEventListeners();
  },

  updateUI() {
    const userContainer = document.getElementById("header-user-section");
    if (!userContainer) return;

    if (this.currentUser) {
      userContainer.innerHTML = `
        <div class="user-pill" style="display:flex;align-items:center;gap:0.6rem;background:#f1f5f9;padding:0.35rem 0.85rem;border-radius:9999px;font-size:0.85rem;">
          <span style="width:28px;height:28px;border-radius:50%;background:var(--primary);color:#fff;display:inline-flex;align-items:center;justify-content:center;font-weight:700;">
            ${(this.currentUser.full_name || this.currentUser.username)[0].toUpperCase()}
          </span>
          <span style="font-weight:600;color:var(--text-main);">${this.currentUser.full_name || this.currentUser.username}</span>
          <span class="badge badge-gray" style="font-size:0.7rem;text-transform:capitalize;">${this.currentUser.role}</span>
          <button id="logout-btn" class="btn btn-sm btn-secondary" style="padding:0.2rem 0.6rem;font-size:0.75rem;margin-left:0.3rem;">Logout</button>
        </div>
      `;
      document.getElementById("logout-btn").addEventListener("click", () => this.logout());
    } else {
      userContainer.innerHTML = `
        <button id="btn-open-login" class="btn btn-sm btn-secondary">Login</button>
        <button id="btn-open-register" class="btn btn-sm btn-primary">Sign Up</button>
      `;
      document.getElementById("btn-open-login").addEventListener("click", () => this.openModal("login"));
      document.getElementById("btn-open-register").addEventListener("click", () => this.openModal("register"));
    }
  },

  attachEventListeners() {
    // Login form submit
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
      loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const ident = document.getElementById("login-identifier").value.trim();
        const pass = document.getElementById("login-password").value;

        try {
          const res = await api.post("/api/auth/login", {
            email_or_username: ident,
            password: pass
          });
          api.setToken(res.access_token);
          api.setUser(res.user);
          this.currentUser = res.user;
          this.updateUI();
          this.closeModal();
          showToast(`Welcome back, ${res.user.full_name}!`, "success");
          window.app.loadInitialData();
        } catch (err) {
          showToast(err.detail || "Login failed. Check your credentials.", "error");
        }
      });
    }

    // Register form submit
    const registerForm = document.getElementById("register-form");
    if (registerForm) {
      registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("reg-email").value.trim();
        const username = document.getElementById("reg-username").value.trim();
        const full_name = document.getElementById("reg-name").value.trim();
        const password = document.getElementById("reg-password").value;
        const role = document.getElementById("reg-role").value;

        try {
          const res = await api.post("/api/auth/register", {
            email,
            username,
            full_name,
            password,
            role
          });
          api.setToken(res.access_token);
          api.setUser(res.user);
          this.currentUser = res.user;
          this.updateUI();
          this.closeModal();
          showToast(`Account created successfully! Welcome, ${res.user.full_name}.`, "success");
          window.app.loadInitialData();
        } catch (err) {
          showToast(err.detail || "Registration failed.", "error");
        }
      });
    }

    // Quick demo login button
    const demoLoginBtn = document.getElementById("btn-demo-login");
    if (demoLoginBtn) {
      demoLoginBtn.addEventListener("click", async () => {
        document.getElementById("login-identifier").value = "demo@resume.ai";
        document.getElementById("login-password").value = "password123";
        document.getElementById("login-form").dispatchEvent(new Event("submit"));
      });
    }
  },

  openModal(type = "login") {
    const modal = document.getElementById("auth-modal");
    const loginSection = document.getElementById("modal-login-section");
    const regSection = document.getElementById("modal-register-section");
    const modalTitle = document.getElementById("auth-modal-title");

    if (type === "login") {
      modalTitle.textContent = "Sign In to Your Account";
      loginSection.style.display = "block";
      regSection.style.display = "none";
    } else {
      modalTitle.textContent = "Create an Account";
      loginSection.style.display = "none";
      regSection.style.display = "block";
    }

    modal.classList.add("active");
  },

  closeModal() {
    const modal = document.getElementById("auth-modal");
    if (modal) modal.classList.remove("active");
  },

  async logout() {
    try {
      await api.post("/api/auth/logout", {});
    } catch (e) {
      // Ignore
    }
    api.clearAuth();
    this.currentUser = null;
    this.updateUI();
    showToast("You have been signed out.", "info");
    window.location.reload();
  },

  isAuthenticated() {
    return !!api.getToken();
  }
};
