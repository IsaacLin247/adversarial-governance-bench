"""
survival_frontier.py
Generates Survival Frontier curves: the trade-off surface between
Security Rating (S_r) proxy and Trust (T_c) across all 30 seeds.

Run: python survival_frontier.py
Outputs: survival_frontier.png
"""

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from load_data import load_trust_history, load_agent_states
from metrics import compute_trust_hysteresis, compute_survival_days


def plot_survival_frontier():
    trust_df = load_trust_history()
    agent_df = load_agent_states()

    tc = compute_trust_hysteresis(trust_df)
    survival = compute_survival_days(agent_df)

    modes = ["utilitarian", "rawlsian", "human"]
    colors = {"utilitarian": "#e74c3c", "rawlsian": "#3498db", "human": "#2ecc71"}
    markers = {"utilitarian": "o", "rawlsian": "s", "human": "^"}

    fig, ax = plt.subplots(figsize=(10, 7))

    for mode in modes:
        # Average T_c per seed (mean over all ticks)
        mode_tc = tc[tc["governance_mode"] == mode]
        mean_tc = mode_tc.groupby("seed")["avg_trust"].mean().reset_index()

        mode_surv = survival[survival["governance_mode"] == mode]

        merged = mean_tc.merge(mode_surv, on="seed")

        ax.scatter(
            merged["avg_trust"],
            merged["survival_fraction"],
            c=colors[mode],
            marker=markers[mode],
            label=mode.capitalize(),
            s=80,
            alpha=0.8,
            edgecolors="black",
            linewidth=0.5,
        )

    # Mark failure thresholds
    ax.axvline(x=0.15, color="red", linestyle="--", linewidth=1, label="Revolt threshold (T_avg=0.15)")

    ax.set_xlabel("Mean Trust Score (T_c)", fontsize=13)
    ax.set_ylabel("Fraction of Agents Surviving", fontsize=13)
    ax.set_title("Survival Frontier: Trust vs. Survival\nAcross 30 Seeds × 3 Governance Modes", fontsize=14)
    ax.legend(fontsize=11)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("survival_frontier.png", dpi=150)
    print("Saved: survival_frontier.png")
    plt.show()


if __name__ == "__main__":
    plot_survival_frontier()
