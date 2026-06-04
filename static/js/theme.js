// Theme toggle: light default, dark optional. Persists in localStorage.
(function () {
  const KEY = "codeduel-theme";
  const saved = localStorage.getItem(KEY) || "light";
  document.documentElement.setAttribute("data-theme", saved);

  function wire() {
    const btn = document.getElementById("theme-toggle");
    if (!btn) return;
    btn.onclick = () => {
      const current = document.documentElement.getAttribute("data-theme");
      const next = current === "light" ? "dark" : "light";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem(KEY, next);
    };
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wire);
  } else {
    wire();
  }
})();