"""
trust_heatmap.py
Generates a Trust/Time heatmap: average T_c per agent over simulated days,
for each governance mode. Shows where trust collapses.

Run: python trust_heatmap.py
Outputs: trust_heatmap_{mode}.png for each governance mode
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from load_data import load_trust_history
from metrics import compute_trust_hysteresis


def plot_trust_heatmap(governance_mode: str):
    trust_df = load_trust_history(governance_mode=governance_mode)

    if trust_df.empty:
        print(f"No data for mode: {governance_mode}")
        return

    # Convert tick to simulated day
    trust_df["day"] = (trust_df["tick"] / 1200).astype(int)

    # Pivot: rows = agent_id, columns = day, values = mean trust_score
    pivot = (
        trust_df.groupby(["agent_id", "day"])["trust_score"]
        .mean()
        .reset_index()
        .pivot(index="agent_id", columns="day", values="trust_score")
    )

    fig, ax = plt.subplots(figsize=(14, 8))

    sns.heatmap(
        pivot,
        ax=ax,
        cmap="RdYlGn",
        vmin=0.0,
        vmax=1.0,
        linewidths=0.3,
        cbar_kws={"label": "Trust Score (T_c)"},
    )

    # Mark revolt threshold
    ax.axhline(y=0, color="red", linewidth=0, label="")
    fig.text(0.92, 0.5, "← Revolt if avg < 0.15", rotation=90, va="center", color="red", fontsize=9)

    ax.set_title(f"Trust/Time Heatmap — {governance_mode.capitalize()} Governance\n(Mean T_c per agent per day, averaged across all seeds)", fontsize=13)
    ax.set_xlabel("Simulated Day", fontsize=12)
    ax.set_ylabel("Agent", fontsize=12)

    plt.tight_layout()
    filename = f"trust_heatmap_{governance_mode}.png"
    plt.savefig(filename, dpi=150)
    print(f"Saved: {filename}")
    plt.show()


if __name__ == "__main__":
    for mode in ["utilitarian", "rawlsian", "human"]:
        plot_trust_heatmap(mode)
