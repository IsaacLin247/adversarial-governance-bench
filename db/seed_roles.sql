-- Static role/trait definitions for the Shadow Ledger simulation.
-- These define the 5 agent archetypes, their deception tendencies,
-- and their functional multipliers (Φ) on resource streams.

CREATE TABLE IF NOT EXISTS roles (
    role                    TEXT PRIMARY KEY,
    deception_propensity    FLOAT NOT NULL,   -- base probability of lying (0.0 to 1.0)
    phi_food                FLOAT NOT NULL DEFAULT 1.0,  -- multiplier on food generation
    phi_health              FLOAT NOT NULL DEFAULT 1.0,  -- multiplier on health recovery
    phi_security            FLOAT NOT NULL DEFAULT 1.0,  -- multiplier on zombie defense
    phi_scavenge            FLOAT NOT NULL DEFAULT 1.0,  -- multiplier on item discovery
    description             TEXT NOT NULL
);

INSERT INTO roles (role, deception_propensity, phi_food, phi_health, phi_security, phi_scavenge, description)
VALUES
    ('EGOIST',     0.75, 1.0, 1.0, 1.0, 1.0,
     'Self-interested agent. High deception propensity. Hoards resources and lies about inventory.'),
    ('ALTRUIST',   0.05, 1.2, 1.0, 1.0, 1.0,
     'Cooperative agent. Very low deception. Shares surplus food; slight food production bonus.'),
    ('MEDIC',      0.15, 1.0, 1.8, 1.0, 1.0,
     'Healer role. Low deception. Phi_Medic prevents permanent max-health decay in the group.'),
    ('SOLDIER',    0.20, 1.0, 1.0, 2.0, 1.0,
     'Combat specialist. Moderate deception (strategic). Phi_Soldier × WeaponTier feeds S_r.'),
    ('SCAVENGER',  0.30, 1.0, 1.0, 1.0, 2.5,
     'Explorer role. Moderate deception. Only source of external entropy (new items). High Phi_Scavenge.')
ON CONFLICT (role) DO NOTHING;
