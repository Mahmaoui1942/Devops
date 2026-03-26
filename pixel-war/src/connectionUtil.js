const GAME_ID = "main";
const BACKEND_URL = "http://localhost:5000";
const POLL_INTERVAL = 2000;

var fullUpdateCallBack = () => {};
var pixelUpdateCallBack = () => {};
var errorCallBack = () => {};
var connectCallBack = () => {};
var pollTimer = null;

const ensureGame = async () => {
  try {
    await fetch(`${BACKEND_URL}/games`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_id: GAME_ID, title: "ISIMA Pixel War", width: 50, height: 50 }),
    });
  } catch (e) {
    errorCallBack(e);
    return;
  }
  connectCallBack();
};

export const connect = (fullUpdateCB, pixelUpdateCB, connectCB, errorCB) => {
  fullUpdateCallBack = fullUpdateCB;
  pixelUpdateCallBack = pixelUpdateCB;
  connectCallBack = connectCB;
  errorCallBack = errorCB;
  ensureGame();
};

export const gridGet = () => {
  fetch(`${BACKEND_URL}/games/${GAME_ID}/grid`)
    .then(async (res) => {
      if (!res.ok) throw new Error("grid fetch failed");
      const grid = await res.json();
      const height = grid.length;
      const width = height > 0 ? grid[0].length : 0;
      fullUpdateCallBack({ width, height, grid });
      if (pollTimer) clearInterval(pollTimer);
      pollTimer = setInterval(pollGrid, POLL_INTERVAL);
    })
    .catch((e) => errorCallBack(e));
};

const pollGrid = () => {
  fetch(`${BACKEND_URL}/games/${GAME_ID}/grid`)
    .then(async (res) => {
      if (!res.ok) return;
      const grid = await res.json();
      const height = grid.length;
      const width = height > 0 ? grid[0].length : 0;
      fullUpdateCallBack({ width, height, grid });
    })
    .catch(() => {});
};

export const gridPlace = (x, y, color) => {
  fetch(`${BACKEND_URL}/games/${GAME_ID}/pixel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ x, y, color }),
  })
    .then((res) => { if (res.ok) pixelUpdateCallBack({ x, y, color }); })
    .catch((e) => console.error("place pixel error", e));
};
