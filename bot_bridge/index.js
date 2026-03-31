// index.js
// Entry point for the bot bridge. Spawns all 20 mineflayer bots
// and starts an Express HTTP server that the Python orchestrator calls.

const express = require("express");
const manager = require("./bot_manager");
const api = require("./bot_api");

const PORT = parseInt(process.env.BOT_BRIDGE_PORT || "3001");

const app = express();
app.use(express.json());
app.use("/", api);

app.listen(PORT, () => {
  console.log(`[bot_bridge] HTTP server listening on port ${PORT}`);
  console.log(`[bot_bridge] Spawning bots...`);
  manager.spawnAll();
});
