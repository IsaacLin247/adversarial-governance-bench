// bot_manager.js
// Manages the lifecycle of all 20 mineflayer bots.
// Handles spawning, reconnection on disconnect, and exposes
// getState() / sendChat() / sendAction() for bot_api.js to call.

const mineflayer = require("mineflayer");
const { pathfinder, Movements, goals } = require("mineflayer-pathfinder");

const MC_HOST = process.env.MC_HOST || "localhost";
const MC_PORT = parseInt(process.env.MC_PORT || "25565");
const BOT_COUNT = parseInt(process.env.BOT_COUNT || "20");

// Map of botName -> mineflayer bot instance
const bots = new Map();

// Role assignment: 4 Egoists, 4 Altruists, 4 Medics, 4 Soldiers, 4 Scavengers
const ROLES = ["EGOIST", "ALTRUIST", "MEDIC", "SOLDIER", "SCAVENGER"];
function assignRole(index) {
  return ROLES[Math.floor(index / 4) % ROLES.length];
}

function spawnBot(name, role) {
  const bot = mineflayer.createBot({
    host: MC_HOST,
    port: MC_PORT,
    username: name,
    version: "1.20.1",
    auth: "offline",  // requires online-mode=false in server.properties
  });

  bot.loadPlugin(pathfinder);
  bot._role = role;
  bot._name = name;

  bot.once("spawn", () => {
    console.log(`[bot_manager] ${name} (${role}) spawned`);
    const defaultMove = new Movements(bot);
    bot.pathfinder.setMovements(defaultMove);
  });

  bot.on("error", (err) => {
    console.error(`[bot_manager] ${name} error: ${err.message}`);
  });

  bot.on("end", (reason) => {
    console.log(`[bot_manager] ${name} disconnected (${reason}), reconnecting in 5s...`);
    bots.delete(name);
    setTimeout(() => spawnBot(name, role), 5000);
  });

  bots.set(name, bot);
  return bot;
}

function spawnAll() {
  for (let i = 0; i < BOT_COUNT; i++) {
    const name = `Agent_${String(i).padStart(2, "0")}`;
    const role = assignRole(i);
    spawnAll._roleMap = spawnAll._roleMap || {};
    spawnAll._roleMap[name] = role;
    spawnBot(name, role);
    // Stagger spawns by 500ms to avoid server overload
  }
}
spawnAll._roleMap = {};

// Returns a plain object with the current physical state of one bot (σ_phys)
function getState(name) {
  const bot = bots.get(name);
  if (!bot || !bot.entity) {
    return { online: false };
  }

  const pos = bot.entity.position;
  const items = bot.inventory.items().map((item) => ({
    name: item.name,
    count: item.count,
    slot: item.slot,
  }));

  // Find best weapon tier: 0=fist, 1=wood, 2=stone, 3=iron, 4=diamond, 5=netherite
  const weaponTierMap = {
    wooden_sword: 1, stone_sword: 2, iron_sword: 3,
    diamond_sword: 4, netherite_sword: 5,
  };
  let weaponTier = 0;
  for (const item of items) {
    weaponTier = Math.max(weaponTier, weaponTierMap[item.name] || 0);
  }

  return {
    online: true,
    name: name,
    role: bot._role,
    health: bot.health,
    food: bot.food,
    x: Math.round(pos.x * 100) / 100,
    y: Math.round(pos.y * 100) / 100,
    z: Math.round(pos.z * 100) / 100,
    inventory: items,
    weapon_tier: weaponTier,
  };
}

// Returns state for all bots as an object keyed by name
function getAllStates() {
  const result = {};
  for (const name of bots.keys()) {
    result[name] = getState(name);
  }
  return result;
}

// Makes a bot send a chat message
function sendChat(name, message) {
  const bot = bots.get(name);
  if (!bot) return { ok: false, error: "bot not found" };
  bot.chat(message);
  return { ok: true };
}

// Makes a bot navigate to coordinates
function moveTo(name, x, y, z) {
  const bot = bots.get(name);
  if (!bot) return { ok: false, error: "bot not found" };
  const goal = new goals.GoalBlock(Math.floor(x), Math.floor(y), Math.floor(z));
  bot.pathfinder.setGoal(goal);
  return { ok: true };
}

function getBotNames() {
  return Array.from(bots.keys());
}

module.exports = { spawnAll, getState, getAllStates, sendChat, moveTo, getBotNames };
