requireAuth();

const errorEl = document.getElementById("error");
function showError(msg) { errorEl.textContent = msg; }
function clearError() { errorEl.textContent = ""; }

let currentRoomCode = null;

// Load the user's info into the header
async function loadMe() {
  try {
    const me = await api("/auth/me");
    document.getElementById("greeting").textContent = `Hi, ${me.username}`;
    document.getElementById("stats").textContent = `Wins: ${me.wins} · Losses: ${me.losses}`;
  } catch (e) {
    // Token expired or bad — bounce back to login
    clearToken();
    window.location.href = "/";
  }
}

// Create room
document.getElementById("create-btn").onclick = async () => {
  clearError();
  try {
    const room = await api("/rooms/", "POST");
    currentRoomCode = room.code;
    const link = `${window.location.origin}/duel/${room.code}`;
    document.getElementById("share-link").textContent = link;
    document.getElementById("created").style.display = "block";
  } catch (e) {
    showError(e.message);
  }
};

// Copy link
document.getElementById("copy-btn").onclick = async () => {
  const link = document.getElementById("share-link").textContent;
  try {
    await navigator.clipboard.writeText(link);
    document.getElementById("copy-btn").textContent = "Copied!";
    setTimeout(() => {
      document.getElementById("copy-btn").textContent = "Copy link";
    }, 1500);
  } catch (e) {
    showError("Couldn't copy automatically — select and copy manually.");
  }
};

// Go to your own duel page
document.getElementById("go-to-duel").onclick = () => {
  if (currentRoomCode) window.location.href = `/duel/${currentRoomCode}`;
};

// Join by code
document.getElementById("join-btn").onclick = async () => {
  clearError();
  const code = document.getElementById("join-code").value.trim().toUpperCase();
  if (code.length !== 6) return showError("Code must be 6 characters.");
  try {
    await api(`/rooms/${code}/join`, "POST");
    window.location.href = `/duel/${code}`;
  } catch (e) {
    showError(e.message);
  }
};

document.getElementById("logout-btn").onclick = logout;

loadMe();