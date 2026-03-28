let activeGameId = "main";
const BACKEND_URL = "/api";
const POLL_INTERVAL = 700;
const CONNECT_RETRY_DELAY_MS = 2000;
const MAX_CONNECT_RETRIES = 20;

var fullUpdateCallBack = () => {};
var pixelUpdateCallBack = () => {};
var errorCallBack = () => {};
var connectCallBack = () => {};
var pollTimer = null;
var pollInFlight = false;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export const setGameId = (gameId) => {
  if (!gameId || !gameId.trim()) return;
  activeGameId = gameId.trim();
};

export const getGameId = () => activeGameId;

export const disconnect = () => {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
};

const ensureGame = async () => {
  let lastError;

  for (let attempt = 1; attempt <= MAX_CONNECT_RETRIES; attempt += 1) {
    try {
      const response = await fetch(`${BACKEND_URL}/games`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_id: activeGameId, title: `Pixel War - ${activeGameId}`, width: 50, height: 50 }),
      });

      if (response.ok || response.status === 409) {
        connectCallBack();
        return;
      }

      lastError = new Error(`create game failed with status ${response.status}`);
    } catch (e) {
      lastError = e;
    }

    await sleep(CONNECT_RETRY_DELAY_MS);
  }

  errorCallBack(lastError || new Error("unable to connect to backend"));
};

export const connect = (fullUpdateCB, pixelUpdateCB, connectCB, errorCB) => {
  fullUpdateCallBack = fullUpdateCB;
  pixelUpdateCallBack = pixelUpdateCB;
  connectCallBack = connectCB;
  errorCallBack = errorCB;
  ensureGame();
};

export const gridGet = () => {
  const loadGrid = async () => {
    let lastError;

    for (let attempt = 1; attempt <= MAX_CONNECT_RETRIES; attempt += 1) {
      try {
        const res = await fetch(`${BACKEND_URL}/games/${activeGameId}/grid`);
        if (!res.ok) throw new Error(`grid fetch failed with status ${res.status}`);

        const grid = await res.json();
        const height = grid.length;
        const width = height > 0 ? grid[0].length : 0;
        fullUpdateCallBack({ width, height, grid });

        if (pollTimer) clearInterval(pollTimer);
        pollTimer = setInterval(pollGrid, POLL_INTERVAL);
        return;
      } catch (e) {
        lastError = e;
      }

      await sleep(CONNECT_RETRY_DELAY_MS);
    }

    errorCallBack(lastError || new Error("unable to load game grid"));
  };

  loadGrid();
};

const pollGrid = () => {
  if (pollInFlight) return;
  pollInFlight = true;
  fetch(`${BACKEND_URL}/games/${activeGameId}/grid`)
    .then(async (res) => {
      if (!res.ok) return;
      const grid = await res.json();
      const height = grid.length;
      const width = height > 0 ? grid[0].length : 0;
      fullUpdateCallBack({ width, height, grid });
    })
    .catch(() => {})
    .finally(() => {
      pollInFlight = false;
    });
};

export const gridPlace = (x, y, color) => {
  fetch(`${BACKEND_URL}/games/${activeGameId}/pixel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ x, y, color }),
  })
    .then((res) => {
      if (res.ok) pixelUpdateCallBack({ x, y, color });
    })
    .catch((e) => console.error("place pixel error", e));
};
