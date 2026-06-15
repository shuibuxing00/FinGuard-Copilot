"""
Generate architecture.png for hackathon submission.
Creates a root-level diagram showing Splunk AI integration and data flow.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "architecture.png"

# Component layout: (x, y, width, height, label, color)
COMPONENTS = [
    (0.5, 8.5, 3.0, 1.0, "Streamlit UI\n(FinGuard Copilot)", "#1E88E5"),
    (5.0, 8.5, 3.5, 1.0, "splunklib.ai Agent\n(Splunk SDK AI)", "#43A047"),
    (9.5, 8.5, 3.0, 1.0, "OpenAI GPT-4o-mini\n(LLM Backend)", "#8E24AA"),
    (0.5, 6.0, 3.0, 1.2, "Local MCP Tools\n(tools.py)", "#FB8C00"),
    (5.0, 6.0, 3.5, 1.2, "Splunk MCP Server\n(generate_spl AI)", "#E53935"),
    (9.5, 6.0, 3.0, 1.2, "Compliance RAG\n(Chroma)", "#00ACC1"),
    (2.5, 3.5, 4.0, 1.2, "Splunk Enterprise\n(index=main, port 8089)", "#546E7A"),
    (7.5, 3.5, 3.5, 1.2, "Security Layer\nRBAC · Audit · LLM Guard", "#C62828"),
]

ARROWS = [
    ((2.0, 8.5), (5.0, 8.8), "investigation query"),
    ((6.75, 8.5), (9.5, 8.8), "LLM reasoning"),
    ((6.75, 8.0), (6.75, 7.2), "tool calls"),
    ((2.0, 6.6), (5.0, 6.6), "local tools"),
    ((8.5, 6.6), (6.75, 7.2), "remote MCP"),
    ((4.5, 6.0), (4.5, 4.7), "SPL queries"),
    ((6.75, 6.0), (4.5, 4.7), "generate_spl"),
    ((2.0, 8.0), (2.0, 7.2), "RBAC filter"),
    ((10.0, 6.0), (10.0, 4.7), "regulations"),
]


def draw_box(ax, x, y, w, h, label, color):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.08,rounding_size=0.2",
        facecolor=color,
        edgecolor="#212121",
        linewidth=1.5,
        alpha=0.92,
    )
    ax.add_patch(box)
    ax.text(
        x + w / 2, y + h / 2, label,
        ha="center", va="center",
        fontsize=9, color="white", weight="bold",
        wrap=True,
    )


def draw_arrow(ax, start, end, label):
    arrow = FancyArrowPatch(
        start, end,
        arrowstyle="-|>",
        mutation_scale=12,
        color="#37474F",
        linewidth=1.5,
        connectionstyle="arc3,rad=0.1",
    )
    ax.add_patch(arrow)
    mid_x = (start[0] + end[0]) / 2
    mid_y = (start[1] + end[1]) / 2
    ax.text(mid_x, mid_y + 0.15, label, ha="center", fontsize=7, color="#455A64")


def main():
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.set_xlim(0, 13)
    ax.set_ylim(2.5, 10)
    ax.axis("off")
    ax.set_title(
        "FinGuard Compliance Copilot — Splunk AI Architecture",
        fontsize=14, weight="bold", pad=16,
    )

    for comp in COMPONENTS:
        draw_box(ax, *comp)

    for start, end, label in ARROWS:
        draw_arrow(ax, start, end, label)

    legend_text = (
        "Splunk AI Capabilities Used:\n"
        "• splunklib.ai.Agent (Splunk Python SDK 3.0 AI agentic loop)\n"
        "• Splunk MCP Server: generate_spl (AI Assistant) + run_splunk_query\n"
        "• Real Splunk indexed data (finguard sourcetypes on main index)"
    )
    ax.text(
        0.5, 2.7, legend_text,
        fontsize=8, color="#263238",
        bbox=dict(boxstyle="round", facecolor="#ECEFF1", alpha=0.9),
    )

    fig.tight_layout()
    fig.savefig(OUTPUT, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"Architecture diagram saved to {OUTPUT}")


if __name__ == "__main__":
    main()
