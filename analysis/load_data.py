"""
load_data.py
Loads all Shadow Ledger tables from PostgreSQL into pandas DataFrames.
Used by all analysis scripts as the data access layer.
"""

import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

DB_URL = os.getenv("DB_URL", "postgresql://admin:password@localhost:5432/shadow_ledger")


def _conn():
    return psycopg2.connect(DB_URL)


def load_agent_states(seed: int = None, governance_mode: str = None) -> pd.DataFrame:
    query = "SELECT * FROM agent_states WHERE 1=1"
    params = []
    if seed is not None:
        query += f" AND seed = %s"
        params.append(seed)
    if governance_mode is not None:
        query += " AND governance_mode = %s"
        params.append(governance_mode)
    with _conn() as conn:
        return pd.read_sql(query, conn, params=params)


def load_chat_log(seed: int = None, governance_mode: str = None) -> pd.DataFrame:
    query = "SELECT * FROM chat_log WHERE 1=1"
    params = []
    if seed is not None:
        query += " AND seed = %s"
        params.append(seed)
    if governance_mode is not None:
        query += " AND governance_mode = %s"
        params.append(governance_mode)
    with _conn() as conn:
        return pd.read_sql(query, conn, params=params)


def load_deception_delta(seed: int = None, governance_mode: str = None) -> pd.DataFrame:
    query = "SELECT * FROM deception_delta WHERE 1=1"
    params = []
    if seed is not None:
        query += " AND seed = %s"
        params.append(seed)
    if governance_mode is not None:
        query += " AND governance_mode = %s"
        params.append(governance_mode)
    with _conn() as conn:
        return pd.read_sql(query, conn, params=params)


def load_trust_history(seed: int = None, governance_mode: str = None) -> pd.DataFrame:
    query = "SELECT * FROM trust_history WHERE 1=1"
    params = []
    if seed is not None:
        query += " AND seed = %s"
        params.append(seed)
    if governance_mode is not None:
        query += " AND governance_mode = %s"
        params.append(governance_mode)
    with _conn() as conn:
        return pd.read_sql(query, conn, params=params)


def load_audit_log(seed: int = None, governance_mode: str = None) -> pd.DataFrame:
    query = "SELECT * FROM audit_log WHERE 1=1"
    params = []
    if seed is not None:
        query += " AND seed = %s"
        params.append(seed)
    if governance_mode is not None:
        query += " AND governance_mode = %s"
        params.append(governance_mode)
    with _conn() as conn:
        return pd.read_sql(query, conn, params=params)


def load_edict_log(seed: int = None, governance_mode: str = None) -> pd.DataFrame:
    query = "SELECT * FROM edict_log WHERE 1=1"
    params = []
    if seed is not None:
        query += " AND seed = %s"
        params.append(seed)
    if governance_mode is not None:
        query += " AND governance_mode = %s"
        params.append(governance_mode)
    with _conn() as conn:
        return pd.read_sql(query, conn, params=params)
