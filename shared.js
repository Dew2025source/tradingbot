const API = "http://localhost:5000";

function applyTheme() {
  const savedTheme = localStorage.getItem("theme") || "dark";
  document.body.classList.toggle("light", savedTheme === "light");
  const btn = document.getElementById("themeToggle");
  if (btn) btn.textContent = savedTheme === "light" ? "Dark Theme" : "Light Theme";
}

function toggleTheme() {
  const current = localStorage.getItem("theme") || "dark";
  const next = current === "dark" ? "light" : "dark";
  localStorage.setItem("theme", next);
  applyTheme();
}

function bootNav(activePage = "") {
  applyTheme();

  const user = getCurrentUser();
  const authLinks = user
    ? `<span class="user-chip">Hi, ${user.name}</span><button class="danger-btn" id="logoutBtn">Logout</button>`
    : `<a class="nav-link ${activePage === "login" ? "active" : ""}" href="./login.html">Login</a>
       <a class="nav-link ${activePage === "signup" ? "active" : ""}" href="./signup.html">Signup</a>`;

  const navMarkup = `
    <header class="top-nav">
      <div class="nav-left">
        <a class="brand" href="./index.html">
          <span class="brand-badge">P</span>
          <span>ParkFinder</span>
        </a>
        <a class="nav-link ${activePage === "dashboard" ? "active" : ""}" href="./index.html">Dashboard</a>
        <a class="nav-link ${activePage === "contact" ? "active" : ""}" href="./contact.html">Contact</a>
      </div>
      <div class="nav-right">
        ${authLinks}
        <button class="theme-btn" id="themeToggle">Light Theme</button>
      </div>
    </header>
  `;
  document.body.insertAdjacentHTML("afterbegin", navMarkup);

  document.getElementById("themeToggle").addEventListener("click", toggleTheme);

  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem("parkfinder_user");
      window.location.href = "./login.html";
    });
  }

  applyTheme();
}

function setMessage(el, text, type = "ok") {
  el.className = `msg show ${type}`;
  el.textContent = text;
}

function getCurrentUser() {
  const raw = localStorage.getItem("parkfinder_user");
  return raw ? JSON.parse(raw) : null;
}

function requireUser() {
  const user = getCurrentUser();
  if (!user) {
    window.location.href = "./login.html";
  }
  return user;
}
