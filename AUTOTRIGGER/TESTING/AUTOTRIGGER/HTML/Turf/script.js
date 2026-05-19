
const storageKey = "vbr-live-scoreboard";

const teamANameInput = document.getElementById("teamAName");
const teamBNameInput = document.getElementById("teamBName");
const teamAPlayersInput = document.getElementById("teamAPlayers");
const teamBPlayersInput = document.getElementById("teamBPlayers");
const teamAAddBtn = document.getElementById("teamAAdd");
const teamBAddBtn = document.getElementById("teamBAdd");
const teamAList = document.getElementById("teamAList");
const teamBList = document.getElementById("teamBList");
const saveTeamsBtn = document.getElementById("saveTeamsBtn");
const editTeamsBtn = document.getElementById("editTeamsBtn");

const setupStep1 = document.getElementById("setupStep1");
const setupStep2 = document.getElementById("setupStep2");
const setupStep3 = document.getElementById("setupStep3");
const setupStep4 = document.getElementById("setupStep4");
const tossNextBtn = document.getElementById("tossNextBtn");
const tossWinnerSelect = document.getElementById("tossWinnerSelect");
const tossWinnerNextBtn = document.getElementById("tossWinnerNextBtn");
const confirmDecisionBtn = document.getElementById("confirmDecisionBtn");
const tossOutcome = document.getElementById("tossOutcome");
const decisionStatus = document.getElementById("decisionStatus");
const oversInput = document.getElementById("oversInput");
const oversNextBtn = document.getElementById("oversNextBtn");
const oversHelper = document.getElementById("oversHelper");

const playerSelectionPanel = document.getElementById("playerSelectionPanel");
const strikerSelect = document.getElementById("strikerSelect");
const nonStrikerSelect = document.getElementById("nonStrikerSelect");
const bowlerSelect = document.getElementById("bowlerSelect");
const confirmPlayersBtn = document.getElementById("confirmPlayersBtn");
const playerSelectionStatus = document.getElementById("playerSelectionStatus");
const outBatsmanSelect = document.getElementById("outBatsmanSelect");

const scoreValueEl = document.getElementById("scoreValue");
const oversDisplay = document.getElementById("oversDisplay");
const currentOverBallsEl = document.getElementById("currentOverBalls");
const ballsThisOverEl = document.getElementById("ballsThisOver");
const strikerDisplay = document.getElementById("strikerDisplay");
const nonStrikerDisplay = document.getElementById("nonStrikerDisplay");
const bowlerDisplay = document.getElementById("bowlerDisplay");
const matchResultEl = document.getElementById("matchResult");
const ballHistoryEl = document.getElementById("ballHistory");
const scoringMessageEl = document.getElementById("scoringMessage");

const scoreButtons = document.querySelectorAll("[data-action]");
const wicketPrompt = document.getElementById("wicketPrompt");
const nextBatsmanSelect = document.getElementById("nextBatsmanSelect");
const confirmNextBatsmanBtn = document.getElementById("confirmNextBatsman");
const scoringPanel = document.getElementById("scoringPanel");
const undoBtn = document.getElementById("undoBtn");
const redoBtn = document.getElementById("redoBtn");
const completeMatchBtn = document.getElementById("completeMatchBtn");
const resetMatchBtn = document.getElementById("resetMatchBtn");
const downloadScoreboardBtn = document.getElementById("downloadScoreboardBtn");
const resetScorecardBtn = document.getElementById("resetScorecardBtn");
const resetScoreboardBtn = document.getElementById("resetScoreboardBtn");
const resetAllBtn = document.getElementById("resetAllBtn");
const scorecardPanel = document.getElementById("scorecardPanel");
const batsmanTableBody = document.getElementById("batsmanTableBody");
const bowlerTableBody = document.getElementById("bowlerTableBody");
const overHistoryDisplay = document.getElementById("overHistoryDisplay");
const completedMatchesList = document.getElementById("completedMatchesList");
const sectionLinks = document.querySelectorAll(".section-links button");
const teamsPanel = document.getElementById("teamsPanel");
const setupPanel = document.getElementById("setupPanel");
const toggleSetupBtn = document.getElementById("toggleSetupBtn");
const actionToast = document.getElementById("actionToast");
let toastTimer;

const setupSteps = [setupStep1, setupStep2, setupStep3, setupStep4];
const setupSections = [teamsPanel, setupPanel, playerSelectionPanel];
let setupVisible = true;
let undoStack = [];
let redoStack = [];

function createDefaultState() {
  return {
    teams: {
      a: { name: "Team A", players: [], captain: "" },
      b: { name: "Team B", players: [], captain: "" },
    },
    teamsSaved: false,
    setupStep: 1,
    toss: { call: "heads", result: "", winner: "", decision: "" },
    maxOvers: 6,
    battingTeam: null,
    bowlingTeam: null,
    striker: "",
    nonStriker: "",
    bowler: "",
    runs: 0,
    wickets: 0,
    balls: 0,
    legalBallsThisOver: 0,
    currentOverBalls: [],
    overHistory: [],
    history: [],
    awaitingBowler: false,
    awaitingBatsman: false,
    pendingDismissal: null,
    availableBatsmen: [],
    matchStarted: false,
    matchCompleted: false,
    matchResult: "",
    battingStats: { a: {}, b: {} },
    bowlingStats: { a: {}, b: {} },
    completedMatches: [],
  };
}

let state = createDefaultState();
function persistState() {
  localStorage.setItem(storageKey, JSON.stringify(state));
}

function showToast(message, variant = "success") {
  if (!actionToast) return;
  actionToast.textContent = message;
  actionToast.dataset.variant = variant;
  actionToast.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => actionToast.classList.add("hidden"), 2400);
}

function loadState() {
  const saved = localStorage.getItem(storageKey);
  if (!saved) return;
  try {
    const parsed = JSON.parse(saved);
    const base = createDefaultState();
    state = {
      ...base,
      ...parsed,
      teams: {
        a: { ...base.teams.a, ...(parsed.teams?.a || {}) },
        b: { ...base.teams.b, ...(parsed.teams?.b || {}) },
      },
      battingStats: {
        a: { ...base.battingStats.a, ...(parsed.battingStats?.a || {}) },
        b: { ...base.battingStats.b, ...(parsed.battingStats?.b || {}) },
      },
      bowlingStats: {
        a: { ...base.bowlingStats.a, ...(parsed.bowlingStats?.a || {}) },
        b: { ...base.bowlingStats.b, ...(parsed.bowlingStats?.b || {}) },
      },
      completedMatches: parsed.completedMatches || [],
    };
  } catch (error) {
    console.warn("Unable to load state", error);
  }
}

function createStateSnapshot() {
  return {
    ...state,
    teams: JSON.parse(JSON.stringify(state.teams)),
    battingStats: JSON.parse(JSON.stringify(state.battingStats)),
    bowlingStats: JSON.parse(JSON.stringify(state.bowlingStats)),
    overHistory: [...state.overHistory],
    currentOverBalls: [...state.currentOverBalls],
    history: [...state.history],
    availableBatsmen: [...state.availableBatsmen],
  };
}

function restoreSnapshot(snapshot) {
  state = { ...state, ...snapshot };
  renderScoreboard();
  renderCompletedMatches();
  refreshPanelState();
  updateScoringButtons();
  persistState();
}
function updateTeamLists() {
  renderTeamList("a", teamAList);
  renderTeamList("b", teamBList);
  updateTossOptions();
  updateTeamInputs();
}

function updateTeamInputs() {
  if (teamANameInput) teamANameInput.value = state.teams.a.name;
  if (teamBNameInput) teamBNameInput.value = state.teams.b.name;
}

function renderTeamList(teamKey, listEl) {
  listEl.innerHTML = "";
  const team = state.teams[teamKey];
  team.players.forEach((player) => {
    const li = document.createElement("li");
    const nameSpan = document.createElement("span");
    nameSpan.className = "player-name";
    nameSpan.textContent = player;
    if (team.captain === player) {
      const badge = document.createElement("span");
      badge.className = "captain-badge";
      badge.textContent = "★";
      nameSpan.appendChild(badge);
    }
    li.appendChild(nameSpan);
    const actions = document.createElement("div");
    actions.className = "player-actions";
    ["captain", "edit", "remove"].forEach((actionType) => {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.team = teamKey;
      button.dataset.player = player;
      button.dataset.action = actionType;
      button.textContent =
        actionType === "captain"
          ? "Captain"
          : actionType === "edit"
          ? "Edit"
          : "Remove";
      button.addEventListener("click", handlePlayerAction);
      actions.appendChild(button);
    });
    li.appendChild(actions);
    listEl.appendChild(li);
  });
}

function handlePlayerAction(event) {
  const { team, player, action } = event.currentTarget.dataset;
  if (!team || !player) return;
  const roster = state.teams[team];
  if (action === "captain") {
    roster.captain = player;
    showToast(`${player} is now captain of ${roster.name}`, "info");
  } else if (action === "edit") {
    const updated = prompt("Rename player", player)?.trim();
    if (!updated) return;
    if (roster.players.includes(updated)) {
      alert("Player already exists");
      return;
    }
    roster.players = roster.players.map((item) => (item === player ? updated : item));
    if (roster.captain === player) roster.captain = updated;
    showToast(`${player} renamed to ${updated}`, "info");
  } else if (action === "remove") {
    if (!confirm(`Remove ${player} from ${roster.name}?`)) return;
    roster.players = roster.players.filter((item) => item !== player);
    if (roster.captain === player) roster.captain = "";
    showToast(`${player} removed from ${roster.name}`, "error");
  }
  persistState();
  updateTeamLists();
}

function updateTossOptions() {
  tossWinnerSelect.innerHTML = '<option value="" disabled selected>Select team</option>';
  ["a", "b"].forEach((key) => {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = state.teams[key].name;
    tossWinnerSelect.appendChild(option);
  });
}

function addPlayers(teamKey, raw) {
  const names = raw
    .split(/[\n,]+/)
    .map((name) => name.trim())
    .filter(Boolean);
  if (!names.length) {
    showToast("Add some names", "info");
    return;
  }
  const team = state.teams[teamKey];
  const added = names.filter((name) => !team.players.includes(name));
  if (!added.length) {
    showToast("No new players added", "info");
    return;
  }
  team.players.push(...added);
  persistState();
  updateTeamLists();
  if (teamKey === "a") teamAPlayersInput.value = "";
  if (teamKey === "b") teamBPlayersInput.value = "";
  showToast(`${added.length} player${added.length === 1 ? "" : "s"} added`, "success");
}

function toggleTeamEditing(enabled) {
  [teamANameInput, teamBNameInput, teamAPlayersInput, teamBPlayersInput].forEach(
    (el) => {
      if (el) el.disabled = !enabled;
    }
  );
  [teamAAddBtn, teamBAddBtn, saveTeamsBtn].forEach((btn) => {
    if (btn) btn.disabled = !enabled;
  });
}
function showSetupStep(stepNumber) {
  state.setupStep = stepNumber;
  setupSteps.forEach((element, index) => {
    element.classList.toggle("hidden", index + 1 !== stepNumber);
  });
}

function updateSetupVisibility(forceVisible = null) {
  if (!state.matchStarted) {
    setupSections.forEach((section) => section?.classList?.remove("hidden"));
    toggleSetupBtn?.classList?.add("hidden");
    return;
  }
  if (forceVisible !== null) setupVisible = forceVisible;
  setupSections.forEach((section) =>
    section?.classList?.toggle("hidden", !setupVisible)
  );
  if (toggleSetupBtn) {
    toggleSetupBtn.textContent = setupVisible ? "Hide setup" : "Show setup";
    toggleSetupBtn.classList.remove("hidden");
  }
}

toggleSetupBtn?.addEventListener("click", () => {
  setupVisible = !setupVisible;
  updateSetupVisibility();
});

function resetMatchSetup() {
  state = {
    ...state,
    striker: "",
    nonStriker: "",
    bowler: "",
    runs: 0,
    wickets: 0,
    balls: 0,
    legalBallsThisOver: 0,
    currentOverBalls: [],
    overHistory: [],
    history: [],
    awaitingBowler: false,
    awaitingBatsman: false,
    pendingDismissal: null,
    availableBatsmen: [],
    matchStarted: false,
    matchCompleted: false,
    matchResult: "",
  };
  playerSelectionPanel.classList.add("hidden");
  scoringPanel.classList.add("hidden");
  wicketPrompt.classList.add("hidden");
  showSetupStep(state.setupStep < 4 ? state.setupStep : 4);
  updateSetupVisibility(true);
  updateScoringButtons();
  renderScoreboard();
}

teamAAddBtn.addEventListener("click", () => addPlayers("a", teamAPlayersInput.value));
teamBAddBtn.addEventListener("click", () => addPlayers("b", teamBPlayersInput.value));

teamANameInput.addEventListener("input", () => {
  state.teams.a.name = teamANameInput.value.trim() || "Team A";
  persistState();
  updateTeamLists();
});

teamBNameInput.addEventListener("input", () => {
  state.teams.b.name = teamBNameInput.value.trim() || "Team B";
  persistState();
  updateTeamLists();
});

saveTeamsBtn.addEventListener("click", () => {
  const minPlayers = 4;
  if (
    state.teams.a.players.length < minPlayers ||
    state.teams.b.players.length < minPlayers
  ) {
    alert(`Add at least ${minPlayers} players per team.`);
    return;
  }
  state.teamsSaved = true;
  toggleTeamEditing(false);
  showSetupStep(1);
  persistState();
  showToast("Teams saved successfully", "success");
});

editTeamsBtn.addEventListener("click", () => {
  state.teamsSaved = false;
  toggleTeamEditing(true);
  resetMatchSetup();
  persistState();
  showToast("Teams unlocked for editing", "info");
});

loadState();
updateTeamLists();
toggleTeamEditing(!state.teamsSaved);
showSetupStep(state.setupStep);
function handleTossNext() {
  const selection = document.querySelector('input[name="tossCall"]:checked');
  if (!selection) {
    tossOutcome.textContent = "Pick head or tail to toss.";
    return;
  }
  const flip = Math.random() < 0.5 ? "heads" : "tails";
  state.toss.call = selection.value;
  state.toss.result = flip;
  tossOutcome.textContent = `Coin shows ${flip.toUpperCase()}.`;
  showToast(`Coin shows ${flip}`, "info");
  showSetupStep(2);
  persistState();
}

tossNextBtn.addEventListener("click", handleTossNext);

tossWinnerNextBtn.addEventListener("click", () => {
  const winner = tossWinnerSelect.value;
  if (!winner) {
    tossOutcome.textContent = "Select the winning team.";
    return;
  }
  state.toss.winner = winner;
  showToast(`${state.teams[winner].name} won the toss`, "info");
  showSetupStep(3);
  persistState();
});

confirmDecisionBtn.addEventListener("click", () => {
  const decisionInput = document.querySelector('input[name="tossDecision"]:checked');
  if (!decisionInput) {
    decisionStatus.textContent = "Choose bat or bowl.";
    return;
  }
  state.toss.decision = decisionInput.value;
  state.battingTeam =
    decisionInput.value === "bat" ? state.toss.winner : state.toss.winner === "a" ? "b" : "a";
  state.bowlingTeam = state.battingTeam === "a" ? "b" : "a";
  oversInput.value = state.maxOvers;
  oversHelper.textContent = `Set overs for ${state.teams[state.battingTeam].name}.`;
  showToast(`${state.teams[state.battingTeam].name} will bat first`, "success");
  showSetupStep(4);
  populatePlayerSelects();
  persistState();
});

oversNextBtn.addEventListener("click", () => {
  const oversValue = Number(oversInput.value) || 6;
  state.maxOvers = Math.min(Math.max(oversValue, 1), 50);
  oversInput.value = state.maxOvers;
  oversHelper.textContent = `Match set for ${state.maxOvers} overs.`;
  playerSelectionPanel.classList.remove("hidden");
  persistState();
});

function populatePlayerSelects() {
  if (!state.battingTeam || !state.bowlingTeam) return;
  fillSelect(strikerSelect, state.teams[state.battingTeam].players, "Select striker");
  fillSelect(nonStrikerSelect, state.teams[state.battingTeam].players, "Select non-striker");
  fillSelect(bowlerSelect, state.teams[state.bowlingTeam].players, "Select bowler");
}

function fillSelect(select, options, placeholder) {
  select.innerHTML = `<option value="" disabled selected>${placeholder}</option>`;
  options.forEach((player) => {
    const option = document.createElement("option");
    option.value = player;
    option.textContent = player;
    select.appendChild(option);
  });
}
function initializePlayerStats() {
  ["a", "b"].forEach((teamKey) => {
    const batting = {};
    const bowling = {};
    state.teams[teamKey].players.forEach((player) => {
      batting[player] = {
        runs: 0,
        balls: 0,
        fours: 0,
        sixes: 0,
        status: "Yet to bat",
      };
      bowling[player] = {
        balls: 0,
        runs: 0,
        wickets: 0,
      };
    });
    state.battingStats[teamKey] = batting;
    state.bowlingStats[teamKey] = bowling;
  });
}

confirmPlayersBtn.addEventListener("click", () => {
  if (!state.battingTeam || !state.bowlingTeam) return;
  const striker = strikerSelect.value;
  const nonStriker = nonStrikerSelect.value;
  const bowler = bowlerSelect.value;
  if (!striker || !nonStriker || !bowler) {
    playerSelectionStatus.textContent = "Select striker, non-striker, and bowler.";
    return;
  }
  if (striker === nonStriker) {
    playerSelectionStatus.textContent = "Striker and non-striker cannot be the same.";
    return;
  }
  initializePlayerStats();
  state.striker = striker;
  state.nonStriker = nonStriker;
  state.bowler = bowler;
  state.availableBatsmen = state.teams[state.battingTeam].players.filter(
    (player) => ![striker, nonStriker].includes(player)
  );
  state.battingStats[state.battingTeam][striker].status = "Not out";
  state.battingStats[state.battingTeam][nonStriker].status = "Not out";
  state.matchStarted = true;
  state.matchCompleted = false;
  state.awaitingBowler = false;
  state.awaitingBatsman = false;
  state.pendingDismissal = null;
  state.balls = 0;
  state.runs = 0;
  state.wickets = 0;
  state.history = [];
  state.overHistory = [];
  state.currentOverBalls = [];
  state.legalBallsThisOver = 0;
  playerSelectionPanel.classList.add("hidden");
  scoringPanel.classList.remove("hidden");
  strikerSelect.disabled = true;
  nonStrikerSelect.disabled = true;
  bowlerSelect.disabled = true;
  showToast("Players locked — scoring live", "success");
  updateSetupVisibility(false);
  renderScoreboard();
  updateScoringButtons();
  persistState();
});
scoreButtons.forEach((button) => {
  button.addEventListener("click", () => handleScoreButton(button));
});

function handleScoreButton(button) {
  if (!state.matchStarted || state.matchCompleted) return;
  if (state.awaitingBowler || state.awaitingBatsman) return;
  pushStateSnapshot();
  const action = button.dataset.action;
  const value = Number(button.dataset.value || 0);
  if (action === "run") {
    recordRun(value);
  } else if (action === "wide") {
    recordExtra("Wd");
  } else if (action === "nobb") {
    recordExtra("Nb");
  } else if (action === "wicket") {
    recordWicket();
  }
  renderScoreboard();
  persistState();
}

function recordRun(runs) {
  state.runs += runs;
  state.balls += 1;
  state.legalBallsThisOver += 1;
  state.currentOverBalls.push(`${runs}`);
  updateBatsmanStats(state.striker, runs, true);
  updateBowlerStats(state.bowler, runs, true);
  if (runs === 1 || runs === 3) swapStrikers();
  appendHistory(`${runs}`);
  checkOverCompletion();
}

function recordExtra(symbol) {
  state.runs += 1;
  state.currentOverBalls.push(symbol);
  updateBowlerStats(state.bowler, 1, false);
  appendHistory(symbol);
}

function recordWicket() {
  state.wickets += 1;
  state.balls += 1;
  state.legalBallsThisOver += 1;
  state.currentOverBalls.push("W");
  updateBowlerStats(state.bowler, 0, true);
  appendHistory("W");
  state.awaitingBatsman = true;
  state.pendingDismissal = [state.striker, state.nonStriker];
  showWicketPrompt();
  scoringMessageEl.textContent = "Select the next batsman.";
  checkOverCompletion();
}

function updateBatsmanStats(player, runs, legal) {
  if (!player) return;
  const stats = state.battingStats[state.battingTeam]?.[player];
  if (!stats) return;
  stats.runs += runs;
  if (legal) stats.balls += 1;
  if (runs === 4) stats.fours += 1;
  if (runs === 6) stats.sixes += 1;
  stats.status = "Not out";
}

function updateBowlerStats(player, runs, legal) {
  if (!player) return;
  const stats = state.bowlingStats[state.bowlingTeam]?.[player];
  if (!stats) return;
  stats.runs += runs;
  if (legal) stats.balls += 1;
  if (runs === 0 && legal) stats.wickets += 1;
}

function swapStrikers() {
  const temp = state.striker;
  state.striker = state.nonStriker;
  state.nonStriker = temp;
}

function appendHistory(symbol) {
  state.history.push(symbol);
  const maxEntries = Math.max(state.maxOvers || 6, 6) * 8;
  while (state.history.length > maxEntries) {
    state.history.shift();
  }
}

function checkOverCompletion() {
  if (state.legalBallsThisOver >= 6) {
    state.overHistory.push({
      over: Math.floor(state.balls / 6),
      balls: [...state.currentOverBalls],
    });
    state.currentOverBalls = [];
    state.legalBallsThisOver = 0;
    if (state.balls >= state.maxOvers * 6) {
      finalizeMatch(`${state.teams[state.battingTeam].name} completed ${state.maxOvers} overs.`, true);
      return;
    }
    state.awaitingBowler = true;
    state.bowler = "";
    bowlerSelect.disabled = false;
    scoringMessageEl.textContent = "Over complete. Pick the next bowler.";
    if (playerSelectionPanel) {
      playerSelectionPanel.classList.remove("hidden");
      playerSelectionStatus.textContent = "Pick the next bowler.";
    }
  }
  updateScoringButtons();
}

bowlerSelect.addEventListener("change", () => {
  if (!state.awaitingBowler) return;
  const selection = bowlerSelect.value;
  if (!selection) return;
  state.bowler = selection;
  state.awaitingBowler = false;
  bowlerSelect.disabled = true;
  scoringMessageEl.textContent = "New over started.";
  if (playerSelectionPanel) {
    playerSelectionPanel.classList.add("hidden");
    playerSelectionStatus.textContent = `${state.teams[state.bowlingTeam].name} bowler selected.`;
  }
  renderScoreboard();
  persistState();
});
function showWicketPrompt() {
  if (!state.availableBatsmen.length) {
    finalizeMatch("All out – match complete", true);
    return;
  }
  wicketPrompt.classList.remove("hidden");
  nextBatsmanSelect.innerHTML = '<option value="" disabled selected>Select next batsman</option>';
  outBatsmanSelect.innerHTML = '<option value="" disabled selected>Select out batsman</option>';
  state.pendingDismissal?.forEach((player) => {
    if (!player) return;
    const option = document.createElement("option");
    option.value = player;
    option.textContent = player;
    outBatsmanSelect.appendChild(option);
  });
  state.availableBatsmen.forEach((player) => {
    const option = document.createElement("option");
    option.value = player;
    option.textContent = player;
    nextBatsmanSelect.appendChild(option);
  });
  updateScoringButtons();
}

confirmNextBatsmanBtn.addEventListener("click", () => {
  const nextPlayer = nextBatsmanSelect.value;
  const outPlayer = outBatsmanSelect.value;
  if (!nextPlayer || !outPlayer) return;
  if (state.striker === outPlayer) {
    state.striker = nextPlayer;
  } else {
    state.nonStriker = nextPlayer;
  }
  state.battingStats[state.battingTeam][nextPlayer].status = "Not out";
  state.battingStats[state.battingTeam][outPlayer].status = "Out";
  state.availableBatsmen = state.availableBatsmen.filter((player) => player !== nextPlayer);
  wicketPrompt.classList.add("hidden");
  state.awaitingBatsman = false;
  renderScoreboard();
  updateScoringButtons();
  persistState();
});
function pushStateSnapshot() {
  if (!state.matchStarted) return;
  undoStack.push(createStateSnapshot());
  if (undoStack.length > 20) undoStack.shift();
  redoStack = [];
  updateScoringButtons();
}

undoBtn.addEventListener("click", () => {
  if (!undoStack.length) return;
  const snapshot = undoStack.pop();
  redoStack.push(createStateSnapshot());
  restoreSnapshot(snapshot);
  showToast("Undo applied", "info");
});

redoBtn.addEventListener("click", () => {
  if (!redoStack.length) return;
  const snapshot = redoStack.pop();
  undoStack.push(createStateSnapshot());
  restoreSnapshot(snapshot);
  showToast("Redo applied", "success");
});

completeMatchBtn?.addEventListener("click", () => {
  if (!state.matchStarted) return;
  finalizeMatch(`${state.teams[state.battingTeam].name} innings complete`, true);
});

resetMatchBtn?.addEventListener("click", () => {
  if (!confirm("Resetting will clear the current match. Continue?")) return;
  resetMatchSetup();
  showToast("Match reset. Begin setup again", "info");
  persistState();
});

resetScoreboardBtn?.addEventListener("click", () => {
  if (!confirm("Clear the scoreboard and archived stats?")) return;
  resetMatchSetup();
  showToast("Scoreboard cleared", "info");
  persistState();
});

resetScorecardBtn?.addEventListener("click", () => {
  if (!confirm("Reset the displayed scorecard?")) return;
  resetMatchSetup();
  showToast("Scorecard reset", "info");
  persistState();
});

resetAllBtn?.addEventListener("click", () => {
  if (!confirm("Clear all teams, players, and match data?")) return;
  localStorage.removeItem(storageKey);
  state = createDefaultState();
  toggleTeamEditing(true);
  updateTeamLists();
  resetMatchSetup();
  showToast("Everything cleared", "info");
});

function finalizeMatch(reason, notify = false) {
  state.matchCompleted = true;
  state.matchStarted = false;
  state.awaitingBowler = false;
  state.awaitingBatsman = false;
  state.matchResult = reason;
  scoringPanel.classList.add("hidden");
  const summary = {
    timestamp: new Date().toLocaleString(),
    batting: state.teams[state.battingTeam]?.name || "Unknown",
    bowling: state.teams[state.bowlingTeam]?.name || "Unknown",
    score: `${state.runs}/${state.wickets}`,
    overs: `${Math.floor(state.balls / 6)}.${state.balls % 6}`,
    reason,
    hero: findHero(),
  };
  state.completedMatches.unshift(summary);
  if (state.completedMatches.length > 6) state.completedMatches.pop();
  renderCompletedMatches();
  if (notify) showToast("Match completed", "success");
  renderScoreboard();
  persistState();
}

function findHero() {
  const stats = state.battingStats[state.battingTeam] || {};
  let hero = { name: "-", runs: 0 };
  Object.entries(stats).forEach(([name, player]) => {
    if (player.runs >= hero.runs) hero = { name, runs: player.runs };
  });
  return `${hero.name} (${hero.runs} runs)`;
}
function renderScoreboard() {
  scoreValueEl.textContent = `${state.runs}/${state.wickets}`;
  oversDisplay.textContent = `${Math.floor(state.balls / 6)}.${state.balls % 6} overs`;
  currentOverBallsEl.textContent = state.currentOverBalls.length
    ? state.currentOverBalls.join(" ")
    : "-";
  ballsThisOverEl.textContent = `Balls this over: ${state.legalBallsThisOver}`;
  strikerDisplay.textContent = `Striker ${state.striker || "-"}`;
  nonStrikerDisplay.textContent = `Non-striker ${state.nonStriker || "-"}`;
  bowlerDisplay.textContent = state.bowler || "-";
  ballHistoryEl.textContent = state.history.length ? state.history.join(" · ") : "-";
  matchResultEl.textContent =
    state.matchResult || (state.matchStarted ? "Match in progress" : "Awaiting setup");
  renderBatsmanTable();
  renderBowlerTable();
  renderOverHistory();
}

function renderBatsmanTable() {
  batsmanTableBody.innerHTML = "";
  const battingPlayers = state.teams[state.battingTeam]?.players || [];
  if (!battingPlayers.length) {
    batsmanTableBody.innerHTML = "<tr><td colspan=\"6\">No batting data</td></tr>";
    return;
  }
  battingPlayers.forEach((player) => {
    const stats = state.battingStats[state.battingTeam]?.[player] || {
      runs: 0,
      balls: 0,
      fours: 0,
      sixes: 0,
      status: "Yet to bat",
    };
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${player}${player === state.striker ? " ★" : player === state.nonStriker ? " ☆" : ""}</td>
      <td>${stats.runs}</td>
      <td>${stats.balls}</td>
      <td>${stats.fours}</td>
      <td>${stats.sixes}</td>
      <td>${stats.status}</td>
    `;
    batsmanTableBody.appendChild(tr);
  });
}

function renderBowlerTable() {
  bowlerTableBody.innerHTML = "";
  const bowlers = state.teams[state.bowlingTeam]?.players || [];
  if (!bowlers.length) {
    bowlerTableBody.innerHTML = "<tr><td colspan=\"5\">No bowling data</td></tr>";
    return;
  }
  bowlers.forEach((player) => {
    const stats = state.bowlingStats[state.bowlingTeam]?.[player] || {
      balls: 0,
      runs: 0,
      wickets: 0,
    };
    const overs = `${Math.floor(stats.balls / 6)}.${stats.balls % 6}`;
    const economy = stats.balls ? (stats.runs / (stats.balls / 6)).toFixed(2) : "0.00";
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${player}${player === state.bowler ? " 🌀" : ""}</td>
      <td>${overs}</td>
      <td>${stats.runs}</td>
      <td>${stats.wickets}</td>
      <td>${economy}</td>
    `;
    bowlerTableBody.appendChild(tr);
  });
}

function renderOverHistory() {
  const entries = [];
  state.overHistory.forEach((over) => {
    entries.push(`Over ${over.over}: ${over.balls.join(" ")}`);
  });
  if (state.currentOverBalls.length) {
    const nextOver = Math.floor(state.balls / 6) + 1;
    entries.push(`Over ${nextOver}: ${state.currentOverBalls.join(" ")}`);
  }
  overHistoryDisplay.textContent = entries.length ? entries.join(" | ") : "-";
}

function renderCompletedMatches() {
  completedMatchesList.innerHTML = "";
  if (!state.completedMatches.length) {
    completedMatchesList.innerHTML = "<p class=\"helper\">No matches recorded</p>";
    return;
  }
  state.completedMatches.forEach((match) => {
    const card = document.createElement("article");
    card.className = "match-card";
    card.innerHTML = `
      <h4>${match.batting} ${match.score} in ${match.overs} overs</h4>
      <p>${match.reason}</p>
      <p>${match.timestamp} • Hero: ${match.hero}</p>
    `;
    completedMatchesList.appendChild(card);
  });
}

function updateScoringButtons() {
  const disabled = !state.matchStarted || state.awaitingBowler || state.awaitingBatsman || state.matchCompleted;
  scoreButtons.forEach((button) => (button.disabled = disabled));
  completeMatchBtn.disabled = !state.matchStarted || state.matchCompleted;
  undoBtn.disabled = undoStack.length === 0;
  redoBtn.disabled = redoStack.length === 0;
}
function downloadScoreboardImage() {
  const width = 640;
  const lines = [
    "VBR Live Scoreboard",
    `Score: ${state.runs}/${state.wickets}`,
    `Overs: ${Math.floor(state.balls / 6)}.${state.balls % 6} / ${state.maxOvers}`,
    `Striker: ${state.striker || "-"} | Non-striker: ${state.nonStriker || "-"}`,
    `Bowler: ${state.bowler || "-"}`,
    `Status: ${state.matchResult || "In progress"}`,
  ];
  const lineHeight = 28;
  const height = 120 + lines.length * lineHeight;
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
      <rect width="100%" height="100%" fill="#030712" />
      <style>text{fill:#f4f6fb;font:600 18px 'Inter',sans-serif;}</style>
      ${lines
        .map((line, index) => `<text x="30" y="${40 + index * lineHeight}">${line}</text>`)
        .join("")}
    </svg>
  `;
  const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const img = new Image();
  img.onload = () => {
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#030712";
    ctx.fillRect(0, 0, width, height);
    ctx.drawImage(img, 0, 0);
    canvas.toBlob((png) => {
      const link = document.createElement("a");
      link.href = URL.createObjectURL(png);
      link.download = `VBR-score-${Date.now()}.png`;
      link.click();
      URL.revokeObjectURL(link.href);
    });
    URL.revokeObjectURL(url);
  };
  img.src = url;
}

downloadScoreboardBtn?.addEventListener("click", downloadScoreboardImage);

sectionLinks.forEach((button) => {
  button.addEventListener("click", () => {
    const target = document.getElementById(button.dataset.target);
    if (!target) return;
    target.classList.remove("hidden");
    target.scrollIntoView({ behavior: "smooth" });
  });
});

function refreshPanelState() {
  scoringPanel?.classList.toggle("hidden", !state.matchStarted || state.matchCompleted);
  if (state.matchStarted) {
    setupVisible = false;
    updateSetupVisibility(false);
  } else {
    setupVisible = true;
    updateSetupVisibility(true);
  }
}

resetMatchSetup();
updateTeamLists();
populatePlayerSelects();
renderScoreboard();
renderCompletedMatches();
updateScoringButtons();
refreshPanelState();
