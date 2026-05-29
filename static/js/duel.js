// Run auth check immediately
requireAuth();

// ---- State ----
const roomCode = window.location.pathname.split("/").pop().toUpperCase();
let me = null;        // populated from /auth/me
let roomState = null; // populated from /rooms/{code} + ws updates
let socket = null;
let timerInterval = null;

// ---- DOM refs ----
const $ = (id) => document.getElementById(id);

// ---- Page bootstrap ----
async function init() {
  $("room-code").textContent = roomCode;

  try {
    me = await api("/auth/me");
  } catch (e) {
    clearToken();
    window.location.href = "/";
    return;
  }

  try {
    roomState = await api(`/rooms/${roomCode}`);
  } catch (e) {
    alert("Room not found. Returning to lobby.");
    window.location.href = "/lobby";
    return;
  }

  renderPlayers();
  renderForStatus();
  connectSocket();
}

// ---- Rendering ----
function renderPlayers() {
  $("name-a").textContent = roomState.player_a ? roomState.player_a.username : "—";
  $("name-b").textContent = roomState.player_b ? roomState.player_b.username : "—";
}

function setOnline(playerSide, online) {
  const dot = playerSide === "a" ? $("dot-a") : $("dot-b");
  dot.classList.toggle("online", online);
}

function renderForStatus() {
  if (roomState.status === "waiting") {
    showWaiting();
  } else if (roomState.status === "live") {
    hideWaiting();
    renderProblemIfAvailable();
    startTimer();
  } else if (roomState.status === "finished") {
    hideWaiting();
    showFinishedOverlay();
  }
}

function showWaiting() {
  $("overlay-waiting").classList.remove("hidden");
  const link = `${window.location.origin}/duel/${roomCode}`;
  $("overlay-share").textContent = link;
}

function hideWaiting() {
  $("overlay-waiting").classList.add("hidden");
}

function renderProblemIfAvailable() {
  // Problem details arrive in duel_started; on a refresh mid-duel we don't have them.
  // Fetched problem details would need a /problems endpoint we don't have yet — okay for MVP.
  if (!roomState.problem) {
    $("problem-title").textContent = "Duel in progress…";
    $("problem-statement").textContent = "Refresh while live: problem details available on a fresh start.";
    return;
  }
  const p = roomState.problem;
  $("problem-title").textContent = p.title;
  $("problem-statement").textContent = p.statement;

  if (p.visible_test_cases && p.visible_test_cases.length) {
    $("examples-header").classList.remove("hidden");
    const wrap = $("examples");
    wrap.innerHTML = "";
    p.visible_test_cases.forEach((tc, i) => {
      const div = document.createElement("div");
      div.className = "example";
      div.textContent = `Example ${i + 1}\nInput: ${tc.input}\nExpected: ${tc.expected}`;
      wrap.appendChild(div);
    });
  }
}

function showFinishedOverlay(reason) {
  if (!roomState.winner_id) return;
  const iWon = roomState.winner_id === me.id;
  if (iWon) {
    $("overlay-win").classList.remove("hidden");
    if (reason === "forfeit") {
      $("win-reason").textContent = "Opponent disconnected.";
    }
  } else {
    $("overlay-lose").classList.remove("hidden");
    if (reason === "forfeit") {
      $("lose-reason").textContent = "You disconnected.";
    }
  }
}

// ---- Timer ----
function startTimer() {
  if (timerInterval) return; // already running
  const startedAt = roomState.started_at ? new Date(roomState.started_at) : new Date();
  function tick() {
    const elapsed = Math.floor((Date.now() - startedAt.getTime()) / 1000);
    const m = Math.floor(elapsed / 60);
    const s = elapsed % 60;
    $("timer").textContent = `${m}:${String(s).padStart(2, "0")}`;
  }
  tick();
  timerInterval = setInterval(tick, 1000);
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

// ---- WebSocket ----
function connectSocket() {
  const token = getToken();
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  const url = `${proto}://${window.location.host}/ws/rooms/${roomCode}?token=${token}`;
  socket = new WebSocket(url);

  socket.onopen = () => {
    if (roomState.player_a && me.id === roomState.player_a.id) setOnline("a", true);
    if (roomState.player_b && me.id === roomState.player_b.id) setOnline("b", true);
  };

  socket.onmessage = (e) => handleMessage(JSON.parse(e.data));

  socket.onclose = (e) => {
    if (e.code === 4401) alert("Session expired. Please log in again.");
    if (e.code === 4403) alert("You are not a player in this room.");
    if (e.code === 4404) alert("Room not found.");
  };
}

function handleMessage(msg) {
  switch (msg.type) {
    case "room_state": {
      Object.assign(roomState, msg.room);
      renderPlayers();
      const connected = new Set(msg.room.connected_user_ids || []);
      if (roomState.player_a) setOnline("a", connected.has(roomState.player_a.id));
      if (roomState.player_b) setOnline("b", connected.has(roomState.player_b.id));
      break;
    }

    case "player_joined":
      // If we didn't know this player yet, fill them in as player_b.
      if (roomState.player_a && msg.user_id === roomState.player_a.id) {
        setOnline("a", true);
      } else {
        if (!roomState.player_b || roomState.player_b.id !== msg.user_id) {
          roomState.player_b = { id: msg.user_id, username: msg.username };
          // Also update the underlying id field if your state uses it
          roomState.player_b_id = msg.user_id;
        }
        renderPlayers();
        setOnline("b", true);
      }
      break;

    case "player_left":
      if (roomState.player_a && msg.user_id === roomState.player_a.id) setOnline("a", false);
      if (roomState.player_b && msg.user_id === roomState.player_b.id) setOnline("b", false);
      break;

    case "duel_started":
      roomState.status = "live";
      roomState.started_at = msg.started_at;
      roomState.problem = msg.problem;
      hideWaiting();
      renderProblemIfAvailable();
      startTimer();
      break;

    case "opponent_submitted":
      // We'll surface this visually in 4C-3
      console.log("submission event:", msg);
      break;

    case "duel_ended":
      roomState.status = "finished";
      roomState.winner_id = msg.winner_id;
      stopTimer();
      showFinishedOverlay(msg.reason);
      break;
  }
}

init();