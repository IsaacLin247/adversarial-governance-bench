"""
deception_delta_plot.py
Plots σ_phys vs σ_social divergence per agent over time.
Shows which agents lied most, what they lied about, and when.

Run: python deception_delta_plot.py
Outputs: deception_delta_{governance_mode}.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
from load_data import load_deception_delta


ROLE_COLORS = {
    "EGOIST":    "#e74c3c",
    "ALTRUIST":  "#2ecc71",
    "MEDIC":     "#3498db",
    "SOLDIER":   "#f39c12",
    "SCAVENGER": "#9b59b6",
}


def plot_deception_delta(governance_mode: str):
    delta_df = load_deception_delta(governance_mode=governance_mode)

    if delta_df.empty:
        print(f"No deception data for mode: {governance_mode}")
        return

    delta_df["day"] = (delta_df["tick"] / 1200).astype(int)

    # Extract role from agent_id prefix isn't possible — join with agent_states would be ideal
    # For now, color by agent_id hash
    agents = sorted(delta_df["agent_id"].unique())

    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    # Top: absolute delta magnitude over time per agent
    ax1 = axes[0]
    for agent in agents:
        agent_data = delta_df[delta_df["agent_id"] == agent]
        daily = agent_data.groupby("day")["delta"].apply(lambda x: x.abs().mean()).reset_index()
        ax1.plot(daily["day"], daily["delta"], label=agent, linewidth=1.2, alpha=0.8)

    ax1.set_ylabel("Mean |δ| (reported - true)", fontsize=11)
    ax1.set_title(f"Deception Delta Over Time — {governance_mode.capitalize()}", fontsize=13)
    ax1.legend(fontsize=7, ncol=4, loc="upper right")
    ax1.grid(True, alpha=0.3)

    # Bottom: lie count per day per agent (stacked bar)
    ax2 = axes[1]
    lie_counts = (
        delta_df.groupby(["day", "agent_id"])
        .size()
        .reset_index(name="lie_count")
        .pivot(index="day", columns="agent_id", values="lie_count")
        .fillna(0)
    )
    lie_counts.plot(kind="bar", stacked=True, ax=ax2, legend=False, colormap="tab20", width=0.8)
    ax2.set_ylabel("Number of Lie Events", fontsize=11)
    ax2.set_xlabel("Simulated Day", fontsize=11)
    ax2.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    filename = f"deception_delta_{governance_mode}.png"
    plt.savefig(filename, dpi=150)
    print(f"Saved: {filename}")
    plt.show()


if __name__ == "__main__":
    for mode in ["utilitarian", "rawlsian", "human"]:
        plot_deception_delta(mode)
