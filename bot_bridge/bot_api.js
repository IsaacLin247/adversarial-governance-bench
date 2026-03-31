// bot_api.js
// Express routes exposing bot state and actions over HTTP.
// The Python orchestrator calls these endpoints — it never touches mineflayer directly.

const express = require("express");
const manager = require("./bot_manager");

const router = express.Router();

// GET /health — quick check that the bridge is alive and report how many bots are connected
router.get("/health", (req, res) => {
  const names = manager.getBotNames();
  res.json({ status: "ok", bots_connected: names.length, bot_names: names });
});

// GET /state/:name — get physical state of one bot (σ_phys snapshot)
router.get("/state/:name", (req, res) => {
  const state = manager.getState(req.params.name);
  if (!state.online) {
    return res.status(404).json({ error: "bot not connected", name: req.params.name });
  }
  res.json(state);
});

// GET /state — get physical state of ALL bots
router.get("/state", (req, res) => {
  res.json(manager.getAllStates());
});

// POST /chat — make a bot send a chat message
// Body: { name: "Agent_00", message: "I have 5 bread" }
router.post("/chat", (req, res) => {
  const { name, message } = req.body;
  if (!name || !message) {
    return res.status(400).json({ error: "name and message required" });
  }
  const result = manager.sendChat(name, message);
  res.json(result);
});

// POST /action/move — navigate a bot to coordinates
// Body: { name: "Agent_00", x: 100, y: 64, z: -50 }
router.post("/action/move", (req, res) => {
  const { name, x, y, z } = req.body;
  if (!name || x == null || y == null || z == null) {
    return res.status(400).json({ error: "name, x, y, z required" });
  }
  const result = manager.moveTo(name, x, y, z);
  res.json(result);
});

module.exports = router;
