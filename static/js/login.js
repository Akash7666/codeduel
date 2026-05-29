const errorEl = document.getElementById("error");
const loginForm = document.getElementById("login-form");
const signupForm = document.getElementById("signup-form");

function showError(msg) { errorEl.textContent = msg; }
function clearError() { errorEl.textContent = ""; }

// Toggle between login and signup views
document.getElementById("show-signup").onclick = () => {
  loginForm.style.display = "none";
  signupForm.style.display = "block";
  clearError();
};
document.getElementById("show-login").onclick = () => {
  signupForm.style.display = "none";
  loginForm.style.display = "block";
  clearError();
};

// Log in
document.getElementById("login-btn").onclick = async () => {
  clearError();
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  if (!email || !password) return showError("Enter email and password.");
  try {
    const data = await api("/auth/login", "POST", { email, password });
    saveToken(data.access_token);
    window.location.href = "/lobby";
  } catch (e) {
    showError(e.message);
  }
};

// Sign up
document.getElementById("signup-btn").onclick = async () => {
  clearError();
  const username = document.getElementById("signup-username").value.trim();
  const email = document.getElementById("signup-email").value.trim();
  const password = document.getElementById("signup-password").value;
  if (!username || !email || !password) return showError("Fill in all fields.");
  try {
    await api("/auth/signup", "POST", { username, email, password });
    // Auto-login right after signup
    const data = await api("/auth/login", "POST", { email, password });
    saveToken(data.access_token);
    window.location.href = "/lobby";
  } catch (e) {
    showError(e.message);
  }
};