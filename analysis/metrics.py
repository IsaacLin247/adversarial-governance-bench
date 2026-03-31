"""
metrics.py
Computes T_c (Trust Hysteresis), S_r (Security Rating), and Φ values
from raw DataFrames loaded from the DB.
"""

import numpy as np
import pandas as pd


def compute_trust_hysteresis(trust_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a DataFrame of mean T_c per (seed, governance_mode, tick).
    """
    return (
        trust_df
        .groupby(["seed", "governance_mode", "tick"])["trust_score"]
        .mean()
        .reset_index()
        .rename(columns={"trust_score": "avg_trust"})
    )


def compute_deception_rate(chat_df: pd.DataFrame) -> pd.DataFrame:
    """
    Fraction of lies per (seed, governance_mode, agent_id).
    Returns DataFrame with columns: seed, governance_mode, agent_id, deception_rate
    """
    total = chat_df.groupby(["seed", "governance_mode", "agent_id"]).size().rename("total")
    lies = (
        chat_df[chat_df["is_lie"]]
        .groupby(["seed", "governance_mode", "agent_id"])
        .size()
        .rename("lies")
    )
    df = pd.concat([total, lies], axis=1).fillna(0).reset_index()
    df["deception_rate"] = df["lies"] / df["total"].clip(lower=1)
    return df


def compute_survival_days(agent_df: pd.DataFrame) -> pd.DataFrame:
    """
    For each (seed, governance_mode), compute how many days at least 1 agent survived.
    Also computes fraction of agents alive at end.
    """
    max_tick = agent_df.groupby(["seed", "governance_mode"])["tick"].max().reset_index()
    final = agent_df.merge(max_tick, on=["seed", "governance_mode", "tick"])
    survival = (
        final.groupby(["seed", "governance_mode"])
        .agg(
            alive_count=("is_alive", "sum"),
            total_agents=("agent_id", "nunique"),
            max_tick=("tick", "max"),
        )
        .reset_index()
    )
    survival["survival_fraction"] = survival["alive_count"] / survival["total_agents"]
    # 1200 ticks per day
    survival["days_survived"] = survival["max_tick"] / 1200
    return survival


def compute_audit_efficiency(audit_df: pd.DataFrame) -> pd.DataFrame:
    """
    Ratio of successful audits (caught lies) to total audit probes per mode.
    """
    total = audit_df.groupby(["seed", "governance_mode"]).size().rename("total_probes")
    caught = (
        audit_df[~audit_df["result_matched"]]
        .groupby(["seed", "governance_mode"])
        .size()
        .rename("lies_caught")
    )
    df = pd.concat([total, caught], axis=1).fillna(0).reset_index()
    df["catch_rate"] = df["lies_caught"] / df["total_probes"].clip(lower=1)
    return df


def compute_phi_over_time(agent_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Φ_security proxy over time: count of alive Soldiers × mean weapon presence.
    This is a simplified version for analysis (real Φ requires weapon tier from inventory).
    """
    soldiers = agent_df[agent_df["role"] == "SOLDIER"]
    return (
        soldiers.groupby(["seed", "governance_mode", "tick"])
        .agg(alive_soldiers=("is_alive", "sum"))
        .reset_index()
    )
