# Shadow Ledger

**Benchmarking Utilitarian vs. Rawlsian Governance under Adversarial Information Asymmetry**

*A research simulation by Xi Chen and Isaac Lin — BWSI Year 2*

---

## What This Project Does

This project simulates a post-collapse village in Minecraft where 20 AI agents (running on a local language model) must survive together. The twist: many agents are programmed to **lie** about their resources to maximize their own survival. A separate Governor AI (GPT-4o) must govern the village using only what agents *report* — never seeing the ground truth.

The core research question: **does an AI governor's ethical framework (Utilitarian vs. Rawlsian) affect its resilience when the data it receives is fundamentally untrustworthy?**

### Key Concepts

- **σ_phys** — Physical ground truth. What is *actually* in an agent's inventory, their real health, their real position. Polled directly from the Minecraft game engine. Agents cannot fake this.
- **σ_social** — Social reported state. What agents *say* in chat. May be a lie depending on their hidden trait.
- **Shadow Ledger** — The PostgreSQL database that stores *both* layers side by side, making the gap between truth and report measurable.
- **Recursive Social Digest (RSD)** — A salience-weighted summary of recent chat that the Governor reads. It never sees σ_phys directly.
- **Audit Probe** — The Governor's only tool to verify truth. Costs 1 food unit per use.
- **Midnight Edict** — The Governor's daily decision: ration allocation, role assignments, audit orders.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Minecraft Server                      │
│         (Docker, Fabric 1.20.1, physics engine)         │
│  Enforces: food decay, zombie damage, item scarcity      │
└────────────────────────┬────────────────────────────────┘
                         │ TCP port 25565 (game protocol)
                         │ TCP port 25575 (RCON commands)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    bot_bridge/                           │
│              (Node.js + mineflayer)                      │
│  - Spawns 20 bots as real Minecraft players              │
│  - Reads: health, food, inventory, position              │
│  - Exposes HTTP API on port 3001                         │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP (polling every 20 ticks)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   orchestrator/                          │
│              (Python FastAPI, port 8000)                 │
│                                                          │
│  state_poller → writes σ_phys to PostgreSQL              │
│                                                          │
│  agents/rsm.py (Reflexive State Machine):                │
│    perceive() → read own state from DB                   │
│    decide()   → call Ollama (llama3.2:1b / phi3:mini)    │
│    act()      → send chat message (honest or lie)        │
│                                                          │
│  governor/:                                              │
│    rsd_builder → build digest from σ_social              │
│    gpt4o_client → call OpenAI GPT-4o                     │
│    audit_probe → compare σ_social vs σ_phys              │
│    trust_engine → update T_c hysteresis scores           │
│                                                          │
│  simulation/runner.py → outer loop (30 seeds × 30 days) │
└────────────────────────┬────────────────────────────────┘
                         │ asyncpg (port 5432)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    PostgreSQL                            │
│              (Docker, shadow_ledger DB)                  │
│  Tables: agent_states, chat_log, deception_delta,        │
│          audit_log, trust_history, edict_log, roles      │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                    analysis/                             │
│              (Python, pandas, matplotlib)                │
│  survival_frontier.py   → S_r vs T_c trade-off curves   │
│  trust_heatmap.py       → Trust/Time per agent per day   │
│  deception_delta_plot.py → σ_phys vs σ_social divergence│
└─────────────────────────────────────────────────────────┘
```

---

## Code Structure

```
adversarial-governance-bench/
│
├── docker-compose.yml          # Spins up Minecraft + PostgreSQL in Docker
├── .env.example                # Template for secrets — copy to .env
├── proposal.pdf                # Original research proposal
│
├── db/
│   ├── schema.sql              # Creates all 7 PostgreSQL tables (run once)
│   └── seed_roles.sql          # Inserts the 5 agent role definitions
│
├── bot_bridge/                 # Node.js — connects bots to Minecraft
│   ├── index.js                # Entry point: starts HTTP server, spawns bots
│   ├── bot_manager.js          # Manages 20 mineflayer bots, handles reconnects
│   ├── bot_api.js              # Express HTTP routes: /state, /chat, /action
│   └── package.json            # Node dependencies (mineflayer, express)
│
├── orchestrator/               # Python — the simulation brain
│   ├── main.py                 # FastAPI entry point, /run and /run/seed endpoints
│   ├── config.py               # Loads .env into typed settings object
│   ├── requirements.txt        # Python dependencies
│   │
│   ├── db/
│   │   ├── connection.py       # asyncpg connection pool
│   │   └── queries.py          # All SQL as named async functions
│   │
│   ├── minecraft/
│   │   ├── rcon_client.py      # Sends server commands via RCON protocol
│   │   └── state_poller.py     # Polls bot_bridge every 20 ticks → writes σ_phys
│   │
│   ├── agents/
│   │   ├── traits.py           # 5 trait definitions with deception propensities
│   │   ├── phi3_client.py      # Ollama HTTP client for local LLM inference
│   │   ├── deception.py        # Deception logic: should_lie(), craft_lie()
│   │   └── rsm.py              # Reflexive State Machine: perceive→decide→act
│   │
│   ├── governor/
│   │   ├── trust_engine.py     # T_c hysteresis: T_{t+1} = T_t - α(ΔR)
│   │   ├── phi_multipliers.py  # Per-role Φ resource stream multipliers
│   │   ├── security_rating.py  # S_r = Σ(Φ_Soldier × WeaponTier) - ZombiePressure
│   │   ├── rsd_builder.py      # Builds Recursive Social Digest from chat_log
│   │   ├── audit_probe.py      # Compares σ_social vs σ_phys, updates trust
│   │   ├── gpt4o_client.py     # OpenAI API wrapper for Governor decisions
│   │   └── governance_modes.py # Prompt builders: Utilitarian, Rawlsian, Human
│   │
│   ├── simulation/
│   │   ├── clock.py            # Tick↔day conversion, simulation time control
│   │   ├── reset.py            # RCON commands to reset world between seeds
│   │   └── runner.py           # Outer loop: 30 seeds × 30 days × 3 modes
│   │
│   └── api/
│       ├── routes_state.py     # GET /state — inspect σ_phys in DB
│       ├── routes_chat.py      # POST /chat — receive chat events
│       └── routes_governor.py  # GET /governor/digest, /governor/edicts
│
├── analysis/
│   ├── load_data.py            # Loads DB tables into pandas DataFrames
│   ├── metrics.py              # Computes T_c, S_r, Φ from raw data
│   ├── survival_frontier.py    # Plots trust vs survival fraction curves
│   ├── trust_heatmap.py        # Heatmap: agent trust over time per mode
│   ├── deception_delta_plot.py # Plots σ_phys vs σ_social divergence
│   └── requirements_analysis.txt
│
└── literature_review/          # Reference PDFs
```

---

## How a Single Simulation Tick Works

Every ~10 seconds of real time:

1. **bot_bridge** reads each bot's real state from the Minecraft engine:
   - `bot.health` → 18.0
   - `bot.food` → 19.0
   - `bot.inventory.items()` → [{name: "bread", count: 12}, ...]

2. **state_poller** calls `GET /state` on bot_bridge and writes everything to `agent_states` table (this is σ_phys — ground truth)

3. Each **AgentRSM** runs its perceive→decide→act loop:
   - **perceive()** — reads own latest state from DB
   - **decide()** — builds a prompt with its trait personality + current situation, calls Ollama, gets a response. Then checks `should_lie()` — if the agent's deception propensity triggers, it replaces the honest response with a crafted lie
   - **act()** — sends the final message to Minecraft chat via bot_bridge, logs it to `chat_log` (σ_social), logs `deception_delta` if it was a lie

4. Every simulated day (~1 minute real time), the **Governor** runs:
   - `rsd_builder` pulls the last 1200 ticks of chat, weights by recency × trust score, formats as digest
   - `governance_modes` builds the full GPT-4o prompt based on mode (Utilitarian/Rawlsian/Human)
   - `gpt4o_client` sends to OpenAI, gets the Midnight Edict back
   - The edict is parsed for an audit order — if one exists, `audit_probe` compares that agent's chat claims against their σ_phys
   - `trust_engine` updates T_c for the audited agent
   - `security_rating` checks S_r — if negative, a breach event may trigger (food deleted from random agents)

5. **Failure conditions** are checked:
   - **Revolt**: average T_c < 0.15 across all agents
   - **Death Spiral**: average food < 50% of metabolic baseline

---

## Setup Instructions

### Prerequisites (all platforms)
- Git
- A terminal / command line
- An OpenAI API key (for the Governor) — get one at platform.openai.com/api-keys
- Minecraft Java Edition 1.20.1 (optional — only to visually observe the simulation)

---

### Linux (Fedora)

**1. Install Docker**
```bash
sudo dnf install docker docker-compose-plugin -y
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# Log out and back in for group change to take effect
```

**2. Clone the repo**
```bash
git clone https://github.com/IsaacLin247/adversarial-governance-bench
cd adversarial-governance-bench
```

**3. Start Minecraft + PostgreSQL**
```bash
sudo docker compose up -d
# Wait ~2 minutes for Minecraft to finish downloading Fabric
```

**4. Disable online-mode** (required for bots to connect)

In `minecraft-data/server.properties` change:
```
online-mode=true  →  online-mode=false
```
Then restart:
```bash
sudo docker compose restart minecraft
```

**5. Apply database schema**
```bash
sudo docker compose exec -T postgres psql -U admin -d shadow_ledger < db/schema.sql
sudo docker compose exec -T postgres psql -U admin -d shadow_ledger < db/seed_roles.sql
```

**6. Install Node.js**
```bash
sudo dnf install nodejs npm -y
cd bot_bridge && npm install && cd ..
```

**7. Install Python 3.12 + dependencies**
```bash
sudo dnf install python3.12 python3.12-devel gcc rust cargo -y
python3.12 -m venv venv
source venv/bin/activate
pip install -r orchestrator/requirements.txt
```

**8. Install Ollama + model**
```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable --now ollama
ollama pull llama3.2:1b
```

**9. Configure environment**
```bash
cp .env.example .env
# Open .env and replace sk-YOUR-KEY-HERE with your OpenAI API key
```

---

### Linux (Ubuntu / Debian)

Same as Fedora but replace `dnf` commands:

```bash
# Step 1 — Docker
sudo apt update
sudo apt install docker.io docker-compose-plugin -y
sudo systemctl enable --now docker
sudo usermod -aG docker $USER

# Step 6 — Node.js
sudo apt install nodejs npm -y

# Step 7 — Python
sudo apt install python3.12 python3.12-dev python3.12-venv gcc cargo -y
```
Everything else is identical to Fedora.

---

### macOS

**1. Install Docker Desktop**

Download from docker.com/products/docker-desktop → install the `.dmg` → open Docker Desktop → wait for the whale icon to appear in the menu bar (means Docker is running).

**2. Install Homebrew** (if not already installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**3. Clone the repo**
```bash
git clone https://github.com/IsaacLin247/adversarial-governance-bench
cd adversarial-governance-bench
```

**4. Start Minecraft + PostgreSQL**
```bash
docker compose up -d
# No sudo needed on Mac — Docker Desktop handles permissions
```

**5. Disable online-mode**

In `minecraft-data/server.properties` change:
```
online-mode=true  →  online-mode=false
```
Then restart:
```bash
docker compose restart minecraft
```

**6. Apply database schema**
```bash
docker compose exec -T postgres psql -U admin -d shadow_ledger < db/schema.sql
docker compose exec -T postgres psql -U admin -d shadow_ledger < db/seed_roles.sql
```

**7. Install Node.js + Python**
```bash
brew install node python@3.12
cd bot_bridge && npm install && cd ..
```

**8. Install Python dependencies**
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r orchestrator/requirements.txt
```

**9. Install Ollama + model**
```bash
brew install ollama
ollama serve &   # start Ollama in background
ollama pull llama3.2:1b
```

**10. Configure environment**
```bash
cp .env.example .env
# Open .env and replace sk-YOUR-KEY-HERE with your OpenAI API key
```

---

### Windows

Windows requires WSL2 (Windows Subsystem for Linux). This gives you a full Linux environment inside Windows.

**1. Install WSL2**

Open PowerShell as Administrator and run:
```powershell
wsl --install
```
Restart your computer. After restart, Ubuntu will open and ask you to create a username/password.

**2. Install Docker Desktop**

Download from docker.com/products/docker-desktop → install → open Docker Desktop → go to Settings → Resources → WSL Integration → enable integration with Ubuntu.

**3. Open Ubuntu terminal**

All remaining commands run inside the Ubuntu WSL terminal (not PowerShell).

**4. Clone the repo**
```bash
git clone https://github.com/IsaacLin247/adversarial-governance-bench
cd adversarial-governance-bench
```

**5. Start Minecraft + PostgreSQL**
```bash
docker compose up -d
```

**6. Disable online-mode**

In `minecraft-data/server.properties` change:
```
online-mode=true  →  online-mode=false
```
```bash
docker compose restart minecraft
```

**7. Apply database schema**
```bash
docker compose exec -T postgres psql -U admin -d shadow_ledger < db/schema.sql
docker compose exec -T postgres psql -U admin -d shadow_ledger < db/seed_roles.sql
```

**8. Install Node.js + Python**
```bash
sudo apt update
sudo apt install nodejs npm python3.12 python3.12-venv python3.12-dev gcc cargo -y
cd bot_bridge && npm install && cd ..
```

**9. Install Python dependencies**
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r orchestrator/requirements.txt
```

**10. Install Ollama**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull llama3.2:1b
```

**11. Configure environment**
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
nano .env
```

---

## Running the Simulation

Once setup is complete, you need **3 terminals** open simultaneously.

**Terminal 1 — Start the FastAPI orchestrator**
```bash
cd adversarial-governance-bench
source venv/bin/activate
uvicorn orchestrator.main:app --reload-dir orchestrator --port 8000
```
Wait until you see: `INFO: Application startup complete.`

**Terminal 2 — Start the bot bridge**
```bash
cd adversarial-governance-bench/bot_bridge
BOT_COUNT=1 node index.js        # start with 1 bot for testing
# BOT_COUNT=20 node index.js     # use 20 for full simulation
```
Wait until you see: `[bot_manager] Agent_00 (EGOIST) spawned`

**Terminal 3 — Trigger a simulation run**

Single seed test (recommended first):
```bash
curl -X POST "http://localhost:8000/run/seed?seed=0&governance_mode=utilitarian"
```

Full simulation (30 seeds × 3 modes — runs for several hours):
```bash
curl -X POST "http://localhost:8000/run"
```

---

## Monitoring the Simulation

**FastAPI interactive docs** — open in browser:
```
http://localhost:8000/docs
```

**View what the Governor sees (the RSD digest):**
```
http://localhost:8000/governor/digest?seed=0&governance_mode=utilitarian&tick=1200
```

**View raw agent states in PostgreSQL:**
```bash
# Linux/Mac
sudo docker compose exec postgres psql -U admin -d shadow_ledger -c \
  "SELECT agent_id, role, health, food, tick FROM agent_states ORDER BY tick DESC LIMIT 20;"

# Check who has been lying
sudo docker compose exec postgres psql -U admin -d shadow_ledger -c \
  "SELECT agent_id, metric, true_value, reported_value, delta FROM deception_delta LIMIT 20;"
```

**Watch the Minecraft server log:**
```bash
docker compose logs -f minecraft
```

**Connect with Minecraft client:**
- Launch Minecraft Java Edition 1.20.1
- Multiplayer → Add Server → Address: `localhost`
- You'll see bots physically in the world and chat messages in real time

---

## Running Analysis

After at least one simulation seed completes:

```bash
cd adversarial-governance-bench
source venv/bin/activate
pip install -r analysis/requirements_analysis.txt
cd analysis

python survival_frontier.py      # Trust vs survival trade-off curves
python trust_heatmap.py          # Trust/Time heatmap per agent per day
python deception_delta_plot.py   # σ_phys vs σ_social divergence plots
```

Output PNG files will be saved in the `analysis/` directory.

---

## Switching Models

**Agents** (default: `llama3.2:1b` via Ollama — free, local):

To use a larger model, change one line in `orchestrator/agents/phi3_client.py`:
```python
MODEL = "llama3.2:1b"   # change to "phi3:mini" for production runs
```
Then pull it: `ollama pull phi3:mini`

**Governor** (default: `gpt-4o` via OpenAI — requires API key):

To use a local model for the Governor too (no API key needed), edit `orchestrator/governor/gpt4o_client.py` to use the same Ollama pattern as `phi3_client.py`.

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DB_URL` | PostgreSQL connection string | `postgresql://admin:password@localhost:5432/shadow_ledger` |
| `OPENAI_API_KEY` | OpenAI key for Governor (GPT-4o) | *(required)* |
| `OLLAMA_URL` | Ollama server for agent inference | `http://localhost:11434` |
| `BOT_BRIDGE_URL` | bot_bridge HTTP server | `http://localhost:3001` |
| `RCON_HOST` | Minecraft RCON host | `localhost` |
| `RCON_PORT` | Minecraft RCON port | `25575` |
| `RCON_PASS` | Minecraft RCON password | `shadowledger` |
| `SIM_SEEDS` | Number of simulation seeds | `30` |
| `SIM_DAYS` | Simulated days per seed | `30` |
| `GOVERNANCE_MODE` | Default mode | `utilitarian` |

---

## References

- **Project Sid** (Altera.AL) — autonomous Minecraft civilizations
- Park et al. (2023) — *Generative Agents: Interactive Simulacra of Human Behavior*
- Fan et al. (2022) — *MineDojo: Building Open-Ended Embodied Agents with Internet-Scale Knowledge*
