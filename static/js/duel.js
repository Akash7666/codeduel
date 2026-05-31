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
// difficulty filled once room state loads

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

  $("room-diff").textContent = roomState.difficulty || "—";

  // If we're not already in this room, try to join it.
  const isPlayerA = roomState.player_a && roomState.player_a.id === me.id;
  const isPlayerB = roomState.player_b && roomState.player_b.id === me.id;
  if (!isPlayerA && !isPlayerB) {
    try {
      roomState = await api(`/rooms/${roomCode}/join`, "POST");
    } catch (e) {
      alert(e.message);
      window.location.href = "/lobby";
      return;
    }
  }

  renderPlayers();
  mountEditor(
    document.getElementById("editor"),
    roomState.starter_code || "# waiting for problem...\n"
  );
  renderForStatus();
  connectSocket();
  renderForStatus();
  connectSocket();
}

// ---- Rendering ----
function renderPlayers() {
  // "Me" row
  document.getElementById("name-me").textContent = me.username;

  // "Opponent" row
  const opp = getOpponent();
  document.getElementById("name-opp").textContent = opp ? opp.username : "Waiting…";
}


function getOpponent() {
  if (!roomState) return null;
  if (roomState.player_a && roomState.player_a.id !== me.id) return roomState.player_a;
  if (roomState.player_b && roomState.player_b.id !== me.id) return roomState.player_b;
  return null;
}

function setOpponentOnline(online) {
  document.getElementById("dot-opp").classList.toggle("online", online);
}

function setMeOnline(online) {
  document.getElementById("dot-me").classList.toggle("online", online);
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
    setMeOnline(true);
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
      setMeOnline(connected.has(me.id));
      const opp = getOpponent();
      setOpponentOnline(opp ? connected.has(opp.id) : false);
      break;
    }

    case "player_joined":
      if (msg.user_id === me.id) {
        setMeOnline(true);
      } else {
        if (roomState.player_a && roomState.player_a.id !== me.id) {
          roomState.player_a = { id: msg.user_id, username: msg.username };
        } else if (!roomState.player_b || roomState.player_b.id !== me.id) {
          roomState.player_b = { id: msg.user_id, username: msg.username };
        }
        renderPlayers();
        setOpponentOnline(true);
      }
      break;

    case "player_left":
      if (msg.user_id === me.id) setMeOnline(false);
      else setOpponentOnline(false);
      break;

   case "duel_started":
      roomState.status = "live";
      roomState.started_at = msg.started_at;
      roomState.problem = msg.problem;
      hideWaiting();
      renderProblemIfAvailable();
      setEditorContent(msg.problem.starter_code);
      setEditorReadOnly(false);
      document.getElementById("submit-btn").disabled = false;
      startTimer();
      break;

    case "opponent_submitted":
      // Ignore our own echo (the broadcast goes to everyone)
      if (msg.user_id === me.id) break;
      showOpponentActivity(msg);
      break;
    
    case "opponent_tab_switch":
      if (msg.user_id === me.id) break;  // ignore our own echo
      showTabSwitchWarning(msg);
      break;


      

    case "duel_ended":
      roomState.status = "finished";
      roomState.winner_id = msg.winner_id;
      stopTimer();
      setEditorReadOnly(true);
      showFinishedOverlay(msg.reason);
      break;
  }
}

const submitBtn = document.getElementById("submit-btn");
const verdictEl = document.getElementById("verdict");

submitBtn.onclick = async () => {
  if (roomState.status !== "live") return;

  submitBtn.disabled = true;
  submitBtn.textContent = "Running…";
  verdictEl.className = "verdict";  // reset
  verdictEl.classList.remove("show");

  const code = getEditorContent();

  try {
    const verdict = await api(`/rooms/${roomCode}/submit`, "POST", { code });
    showVerdict(verdict);
  } catch (e) {
    verdictEl.textContent = "Error: " + e.message;
    verdictEl.className = "verdict fail show";
  } finally {
    // Re-enable only if the duel is still live (a win flips status to finished)
    if (roomState.status === "live") {
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit";
    } else {
      submitBtn.textContent = "Submit";
    }
  }
};

function showVerdict(verdict) {
  if (verdict.all_passed) {
    verdictEl.className = "verdict pass show";
    verdictEl.textContent = `Accepted — all ${verdict.total} tests passed!`;
  } else {
    verdictEl.className = "verdict fail show";
    let text = `Failed — ${verdict.passed}/${verdict.total} tests passed.`;
    if (verdict.first_failure) {
      const f = verdict.first_failure;
      text += `\nFirst failing case:\nInput: ${f.input}\nExpected: ${f.expected}\nGot: ${f.actual}`;
    }
    verdictEl.textContent = text;
  }
}

function showOpponentActivity(msg) {
  // Find which pill is the opponent and append a small status line
  const isOpponentA = roomState.player_a && msg.user_id === roomState.player_a.id;
  const statusText = msg.all_passed
    ? "solved it!"
    : `tried (${msg.passed}/${msg.total})`;
  // Lightweight: show a transient note under the timer
  let note = document.getElementById("opponent-note");
  if (!note) {
    note = document.createElement("div");
    note.id = "opponent-note";
    note.style.cssText = "text-align:center;font-size:0.8rem;color:#6b7280;margin-top:0.3rem;";
    document.querySelector(".duel-header").appendChild(note);
  }
  note.textContent = `${msg.username} ${statusText}`;
}

function showTabSwitchWarning(msg) {
  // Opponent switched — show count in their row
  document.getElementById("tabs-opp").textContent = `⚠ ${msg.count}×`;
}


// Report when this player switches away from the duel tab.
document.addEventListener("visibilitychange", () => {
  // Only report while a duel is actually live
  if (document.hidden && roomState && roomState.status === "live") {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "tab_switch" }));
    }
  }
});


init();