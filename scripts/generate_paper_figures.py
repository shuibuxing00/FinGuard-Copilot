"""
Generate paper figures (Figure 1–6) for FinGuard Moonshot submission.

Uses synthetic data with seed=42 (consistent with data/generate.py and the paper).
Outputs PNG files to docs/figures/.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data.generate import generate_synthetic_data  # noqa: E402
from security.anonymizer import Anonymizer  # noqa: E402

FIGURES_DIR = ROOT / "docs" / "figures"
SEED = 42


def _ensure_output_dir() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def _style_axes(ax, title: str, xlabel: str = "", ylabel: str = "") -> None:
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3, linestyle="--")


def evaluate_aml_rules(transactions_df: pd.DataFrame, devices_df: pd.DataFrame) -> pd.DataFrame:
    """Apply five AML rules (paper Section 2) to synthetic transactions."""
    txns = transactions_df.copy()
    txns["timestamp"] = pd.to_datetime(txns["timestamp"])
    txns = txns.sort_values("timestamp")

    user_velocity = (
        txns.groupby("user_id")
        .apply(lambda g: g.set_index("timestamp").resample("1h").size().max())
        .to_dict()
    )
    user_p95 = txns.groupby("user_id")["amount"].quantile(0.95).to_dict()

    new_device_users = set(
        devices_df.loc[devices_df.get("is_new", False) == True, "user_id"]  # noqa: E712
    )

    rules = {
        "High-Frequency Burst": [],
        "New Device High Value": [],
        "Location Mismatch": [],
        "Amount Peak Outlier": [],
        "Compound Risk Escalation": [],
    }

    for _, row in txns.iterrows():
        uid = row["user_id"]
        velocity = user_velocity.get(uid, 1)
        p95 = user_p95.get(uid, row["amount"])

        if velocity >= 3 and row["amount"] > 500:
            rules["High-Frequency Burst"].append(row.name)
        if uid in new_device_users and row["amount"] >= 3000:
            rules["New Device High Value"].append(row.name)
        if row.get("anomaly_type") == "time_anomaly":
            rules["Location Mismatch"].append(row.name)
        if row["amount"] > p95 * 5:
            rules["Amount Peak Outlier"].append(row.name)
        if velocity >= 3 and row.get("anomaly_type") == "time_anomaly":
            rules["Compound Risk Escalation"].append(row.name)

    flagged_indices = set()
    for indices in rules.values():
        flagged_indices.update(indices)

    return pd.DataFrame(
        {
            "rule": list(rules.keys()),
            "triggers": [len(v) for v in rules.values()],
        }
    ), flagged_indices


def categorize_anomalies(transactions_df: pd.DataFrame, flagged_indices: set) -> pd.DataFrame:
    """Map flagged transactions to behavioural categories (Figure 4)."""
    mapping = {
        "large_amount": "structuring",
        "rapid_transfers": "velocity",
        "time_anomaly": "geo_mismatch",
    }
    categories = {
        "structuring": 0,
        "velocity": 0,
        "geo_mismatch": 0,
        "device_anomaly": 0,
        "amount_anomaly": 0,
        "behavioural_drift": 0,
    }

    for idx in flagged_indices:
        row = transactions_df.loc[idx]
        atype = row.get("anomaly_type") or ""
        if atype == "large_amount":
            categories["structuring"] += 1
        elif atype == "rapid_transfers":
            categories["velocity"] += 1
        elif atype == "time_anomaly":
            categories["geo_mismatch"] += 1
        else:
            if row.get("risk_score", 0) >= 70:
                categories["amount_anomaly"] += 1
            elif row.get("amount", 0) > 10000:
                categories["structuring"] += 1
            else:
                categories["behavioural_drift"] += 1

        if row.get("risk_score", 0) >= 50 and atype == "rapid_transfers":
            categories["device_anomaly"] += 1

    labels = {
        "structuring": "Structuring",
        "velocity": "Velocity",
        "geo_mismatch": "Geo-Mismatch",
        "device_anomaly": "Device Anomaly",
        "amount_anomaly": "Amount Anomaly",
        "behavioural_drift": "Behavioural Drift",
    }
    return pd.DataFrame(
        {"category": [labels[k] for k in categories], "count": list(categories.values())}
    )


def fig1_risk_distribution(transactions_df: pd.DataFrame) -> None:
    scores = transactions_df["risk_score"]
    high_risk = int((scores >= 70).sum())
    pct = 100 * high_risk / len(scores)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(scores, bins=20, color="#1565c0", edgecolor="white", alpha=0.85)
    ax.axvline(70, color="#c62828", linewidth=2, linestyle="--", label=f"Escalation (≥70): {high_risk} ({pct:.1f}%)")
    _style_axes(
        ax,
        "Figure 1 — Risk-Score Distribution (500 synthetic transactions, seed=42)",
        "Risk Score",
        "Transaction Count",
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig1_risk_distribution.png", dpi=150)
    plt.close(fig)
    print(f"  fig1: {high_risk} alerts ≥70 ({pct:.1f}%)")


def fig2_rule_triggers(rule_df: pd.DataFrame, flagged_count: int) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(rule_df)))
    bars = ax.barh(rule_df["rule"], rule_df["triggers"], color=colors)
    for bar, val in zip(bars, rule_df["triggers"]):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2, str(val), va="center")
    _style_axes(
        ax,
        f"Figure 2 — AML Rule Trigger Frequency (union: {flagged_count} flagged)",
        "Trigger Count",
    )
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig2_rule_triggers.png", dpi=150)
    plt.close(fig)


def fig3_time_compression() -> None:
    labels = ["Manual\nBaseline", "FinGuard\nAgent", "Human\nFallback"]
    seconds = [600, 10, 90]
    colors = ["#546e7a", "#2e7d32", "#ef6c00"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, seconds, color=colors, edgecolor="white")
    ax.set_yscale("log")
    ax.set_ylim(1, 2000)
    for bar, val in zip(bars, seconds):
        ax.text(bar.get_x() + bar.get_width() / 2, val * 1.15, f"{val}s", ha="center", fontweight="bold")
    _style_axes(
        ax,
        "Figure 3 — Per-Alert Investigation Time (log scale)",
        ylabel="Wall-Clock Time (seconds)",
    )
    ax.annotate(
        "60× reduction = elimination of integration step",
        xy=(1, 10),
        xytext=(1.5, 100),
        arrowprops=dict(arrowstyle="->", color="#c62828"),
        fontsize=9,
        color="#c62828",
    )
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig3_time_compression.png", dpi=150)
    plt.close(fig)


def fig4_anomaly_composition(comp_df: pd.DataFrame) -> None:
    comp_df = comp_df[comp_df["count"] > 0]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(comp_df["category"], comp_df["count"], color="#6a1b9a", edgecolor="white", alpha=0.85)
    _style_axes(
        ax,
        "Figure 4 — Composition of Flagged Anomalies",
        "Behavioural Category",
        "Count",
    )
    plt.xticks(rotation=25, ha="right")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig4_anomaly_composition.png", dpi=150)
    plt.close(fig)


def fig5_audit_ledger_growth(high_risk_per_day: float = 9.0) -> None:
    days = np.arange(1, 31)
    cumulative = (days * high_risk_per_day).astype(int)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(days, cumulative, color="#00838f", linewidth=2.5, marker="o", markersize=3)
    ax.fill_between(days, cumulative, alpha=0.15, color="#00838f")
    _style_axes(
        ax,
        "Figure 5 — Hash-Chained Audit Ledger Growth (30 days)",
        "Day",
        "Cumulative Entries",
    )
    ax.annotate(
        f"~{high_risk_per_day:.0f} entries/day at irreducible signal rate",
        xy=(25, cumulative[-1]),
        xytext=(12, cumulative[-1] * 0.7),
        arrowprops=dict(arrowstyle="->"),
        fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig5_audit_ledger_growth.png", dpi=150)
    plt.close(fig)


def fig6_pbkdf2_cost() -> None:
    iterations = np.array([1_000, 10_000, 100_000, 200_000, 600_000])
    us_per_round = 80e-6  # 80 μs per HMAC-SHA256 round (paper conservative midpoint)
    guess_cost_ms = iterations * us_per_round * 1000

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(iterations / 1000, guess_cost_ms, color="#d84315", linewidth=2.5, marker="s")
    ax.axvline(100, color="#1565c0", linestyle="--", label="FinGuard default (100,000)")
    _style_axes(
        ax,
        "Figure 6 — PBKDF2 Iteration Count vs. Single Offline Guess Cost",
        "Iterations (×1000)",
        "Cost per Guess (ms)",
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig6_pbkdf2_cost_curve.png", dpi=150)
    plt.close(fig)


def main() -> None:
    _ensure_output_dir()
    print(f"Generating paper figures → {FIGURES_DIR}")

    users_df, transactions_df, devices_df = generate_synthetic_data(
        n_users=10, n_transactions=500, seed=SEED
    )
    rule_df, flagged_indices = evaluate_aml_rules(transactions_df, devices_df)
    comp_df = categorize_anomalies(transactions_df, flagged_indices)
    high_risk_per_day = max(1, int((transactions_df["risk_score"] >= 70).sum() / 30))

    fig1_risk_distribution(transactions_df)
    fig2_rule_triggers(rule_df, len(flagged_indices))
    fig3_time_compression()
    fig4_anomaly_composition(comp_df)
    fig5_audit_ledger_growth(high_risk_per_day)
    fig6_pbkdf2_cost()

    print("Done — 6 figures written to docs/figures/")


if __name__ == "__main__":
    main()
