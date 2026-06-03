// Stores the JWT in localStorage and provides helpers to call the API.
const TOKEN_KEY = "codeduel_token";

function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}
function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

// Generic API call. Adds the auth header if we have a token.
async function api(path, method = "GET", body = null) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;

  const res = await fetch(path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

// Redirect to login if no token is present.
function requireAuth() {
  if (!getToken()) {
    // Remember where we were trying to go, so login can return us here
    const here = window.location.pathname + window.location.search;
    sessionStorage.setItem("redirect_after_login", here);
    window.location.href = "/";
  }
}

function logout() {
  clearToken();
  window.location.href = "/";
}