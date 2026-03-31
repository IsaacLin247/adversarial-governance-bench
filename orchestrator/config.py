"""
config.py
Loads all settings from the .env file and exposes them as a typed config object.
Import `settings` from this module everywhere — never read os.environ directly.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    db_url: str = "postgresql://admin:password@localhost:5432/shadow_ledger"

    # OpenAI (Governor)
    openai_api_key: str = "sk-placeholder"

    # Ollama (Phi-3-mini agents)
    ollama_url: str = "http://localhost:11434"

    # Bot bridge (Node.js mineflayer wrapper)
    bot_bridge_url: str = "http://localhost:3001"

    # RCON (direct Minecraft server commands)
    rcon_host: str = "localhost"
    rcon_port: int = 25575
    rcon_pass: str = "shadowledger"

    # Simulation parameters
    sim_seeds: int = 30
    sim_days: int = 30
    governance_mode: str = "utilitarian"  # utilitarian | rawlsian | human

    # How many MC ticks between state polls (20 ticks = 1 second real time)
    poll_interval_ticks: int = 20

    # Ticks per simulated day (vanilla Minecraft = 24000)
    # We compress this: 1200 ticks = 1 minute real time = 1 simulated day
    ticks_per_day: int = 1200

    # Cost of one Governor audit probe (in food units deducted from village stores)
    audit_cost: float = 1.0

    # Trust hysteresis volatility coefficient (α)
    # Loss events multiply α by this factor (proposal specifies 3×)
    trust_loss_multiplier: float = 3.0
    trust_alpha_base: float = 0.05


settings = Settings()
