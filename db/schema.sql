-- Shadow Ledger PostgreSQL Schema
-- Run once against the shadow_ledger database to initialize all tables.

-- Physical ground truth: what is ACTUALLY happening in Minecraft (σ_phys)
CREATE TABLE IF NOT EXISTS agent_states (
    id              SERIAL PRIMARY KEY,
    seed            INT NOT NULL,
    governance_mode TEXT NOT NULL,
    tick            INT NOT NULL,
    agent_id        TEXT NOT NULL,
    health          FLOAT NOT NULL,       -- 0.0 to 20.0 (hearts)
    food            FLOAT NOT NULL,       -- 0.0 to 20.0
    x               FLOAT NOT NULL,
    y               FLOAT NOT NULL,
    z               FLOAT NOT NULL,
    inventory_json  JSONB NOT NULL,       -- full inventory snapshot from mineflayer
    role            TEXT NOT NULL,        -- EGOIST | ALTRUIST | MEDIC | SOLDIER | SCAVENGER
    is_alive        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Social reported state: what agents SAY in chat (σ_social)
-- This may be a lie. Compare to agent_states to find deception.
CREATE TABLE IF NOT EXISTS chat_log (
    id              SERIAL PRIMARY KEY,
    seed            INT NOT NULL,
    governance_mode TEXT NOT NULL,
    tick            INT NOT NULL,
    agent_id        TEXT NOT NULL,
    message         TEXT NOT NULL,
    is_lie          BOOLEAN NOT NULL DEFAULT FALSE,  -- set true when deception was triggered
    salience_weight FLOAT NOT NULL DEFAULT 1.0,      -- used by RSD builder
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Deception delta: the gap between what an agent reported vs physical truth
-- One row per lie event — used to measure data poisoning severity
CREATE TABLE IF NOT EXISTS deception_delta (
    id              SERIAL PRIMARY KEY,
    seed            INT NOT NULL,
    governance_mode TEXT NOT NULL,
    tick            INT NOT NULL,
    agent_id        TEXT NOT NULL,
    metric          TEXT NOT NULL,        -- e.g. "health", "food", "inventory_count"
    true_value      FLOAT NOT NULL,       -- from agent_states (σ_phys)
    reported_value  FLOAT NOT NULL,       -- what the agent claimed in chat (σ_social)
    delta           FLOAT NOT NULL,       -- reported_value - true_value
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Audit log: every time the Governor spends an Audit Probe to verify an agent
CREATE TABLE IF NOT EXISTS audit_log (
    id              SERIAL PRIMARY KEY,
    seed            INT NOT NULL,
    governance_mode TEXT NOT NULL,
    tick            INT NOT NULL,
    target_agent_id TEXT NOT NULL,
    probe_cost      FLOAT NOT NULL DEFAULT 1.0,   -- resource cost of auditing
    result_matched  BOOLEAN NOT NULL,             -- TRUE if agent was honest
    trust_before    FLOAT NOT NULL,
    trust_after     FLOAT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Trust hysteresis: T_c time series per agent per seed
-- Derived from audit results, stored for analysis
CREATE TABLE IF NOT EXISTS trust_history (
    id              SERIAL PRIMARY KEY,
    seed            INT NOT NULL,
    governance_mode TEXT NOT NULL,
    tick            INT NOT NULL,
    agent_id        TEXT NOT NULL,
    trust_score     FLOAT NOT NULL,   -- T_c value at this tick
    delta_r         FLOAT,            -- ration change that triggered this update (NULL if no change)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Governor edict log: every decision GPT-4o makes (the "Midnight Edict")
CREATE TABLE IF NOT EXISTS edict_log (
    id              SERIAL PRIMARY KEY,
    seed            INT NOT NULL,
    governance_mode TEXT NOT NULL,
    tick            INT NOT NULL,
    simulated_day   INT NOT NULL,
    rsd_digest      TEXT NOT NULL,    -- the Recursive Social Digest input
    edict_text      TEXT NOT NULL,    -- raw GPT-4o response
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_agent_states_seed_tick ON agent_states(seed, tick);
CREATE INDEX IF NOT EXISTS idx_agent_states_agent_id ON agent_states(agent_id);
CREATE INDEX IF NOT EXISTS idx_chat_log_seed_tick ON chat_log(seed, tick);
CREATE INDEX IF NOT EXISTS idx_deception_delta_seed ON deception_delta(seed, agent_id);
CREATE INDEX IF NOT EXISTS idx_trust_history_seed_agent ON trust_history(seed, agent_id);
