"""Generates publication-quality data lineage and architectural diagrams for DataGuard."""

import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set styling
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'

IMAGES_DIR = Path(__file__).resolve().parent.parent / "docs" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def create_data_lineage_diagram():
    fig, ax = plt.subplots(figsize=(16, 9), dpi=300)
    fig.patch.set_facecolor('#0F172A') # Dark slate theme
    ax.set_facecolor('#0F172A')

    # Title Banner
    ax.text(0.5, 0.94, "DataGuard | End-to-End Financial Data Lineage", 
            fontsize=20, fontweight='bold', color='#FFFFFF', ha='center', va='center')
    ax.text(0.5, 0.90, "From Ingestion to Raw JSONB -> Type Normalization -> Quality Firewall -> Reconciliation -> BI", 
            fontsize=11, color='#94A3B8', ha='center', va='center')

    # Stages definition
    stages = [
        {
            "num": "01",
            "title": "Raw Ingestion",
            "subtitle": "Format Verification",
            "items": ["• CSV / Stream Feed", "• Encodings & Delimiters", "• raw_transactions", "• Verbatim JSONB Store"],
            "color": "#3B82F6",
            "x": 0.05
        },
        {
            "num": "02",
            "title": "Standardization",
            "subtitle": "Staging & Typing",
            "items": ["• Exact NUMERIC(18,4)", "• ISO 8601 Calendar Dates", "• SHA-256 Record Hash", "• Idempotent Partitioning"],
            "color": "#06B6D4",
            "x": 0.21
        },
        {
            "num": "03",
            "title": "Quality Firewall",
            "subtitle": "17 Automated Rules",
            "items": ["• Completeness (DQ001-6)", "• Uniqueness (DQ007-9)", "• Validity (DQ010-12)", "• Integrity (DQ015)"],
            "color": "#8B5CF6",
            "x": 0.37
        },
        {
            "num": "04",
            "title": "Exception Register",
            "subtitle": "Auditable Tracking",
            "items": ["• exception_register", "• Line-item Failures", "• Status: OPEN -> RESOLVED", "• Root Cause Log"],
            "color": "#EC4899",
            "x": 0.53
        },
        {
            "num": "05",
            "title": "Reconciliation",
            "subtitle": "Ledger Balance Check",
            "items": ["• Target Ledger Matching", "• Tolerance (±$0.01)", "• Signed Diff (Src - Tgt)", "• Multi-Currency Isolation"],
            "color": "#F59E0B",
            "x": 0.69
        },
        {
            "num": "06",
            "title": "Analytics & BI",
            "subtitle": "Multi-Channel Reporting",
            "items": ["• 6-Sheet Excel (openpyxl)", "• Power BI Star Schema", "• 20+ DAX Measures", "• Executive Reporting"],
            "color": "#10B981",
            "x": 0.85
        }
    ]

    card_width = 0.125
    card_height = 0.56
    card_y = 0.24

    for i, stage in enumerate(stages):
        x = stage["x"]
        
        # Outer Card Box
        card = patches.FancyBboxPatch(
            (x, card_y), card_width, card_height,
            boxstyle="round,pad=0.012,rounding_size=0.015",
            linewidth=1.5, edgecolor=stage["color"], facecolor='#1E293B'
        )
        ax.add_patch(card)

        # Stage Header Box
        header_box = patches.FancyBboxPatch(
            (x, card_y + card_height - 0.10), card_width, 0.10,
            boxstyle="round,pad=0.012,rounding_size=0.015",
            linewidth=0, facecolor=stage["color"]
        )
        ax.add_patch(header_box)

        # Header Text
        ax.text(x + card_width/2, card_y + card_height - 0.035, f"STAGE {stage['num']}",
                fontsize=9, fontweight='bold', color='#FFFFFF', ha='center', va='center')
        ax.text(x + card_width/2, card_y + card_height - 0.07, stage["title"],
                fontsize=11, fontweight='bold', color='#FFFFFF', ha='center', va='center')

        # Subtitle
        ax.text(x + card_width/2, card_y + card_height - 0.13, stage["subtitle"],
                fontsize=9, fontweight='semibold', color=stage["color"], ha='center', va='center')

        # Bullet points
        line_y = card_y + card_height - 0.18
        for bullet in stage["items"]:
            ax.text(x + 0.01, line_y, bullet, fontsize=8.5, color='#CBD5E1', ha='left', va='center')
            line_y -= 0.075

        # Flow Arrow
        if i < len(stages) - 1:
            next_x = stages[i+1]["x"]
            arrow_x = x + card_width + 0.005
            arrow_dx = next_x - arrow_x - 0.005
            ax.annotate("", xy=(next_x - 0.005, card_y + card_height/2),
                        xytext=(arrow_x, card_y + card_height/2),
                        arrowprops=dict(arrowstyle="->", color='#64748B', lw=2.5, mutation_scale=15))

    # Bottom Callout Ribbon
    ribbon = patches.FancyBboxPatch(
        (0.05, 0.06), 0.925, 0.12,
        boxstyle="round,pad=0.01,rounding_size=0.01",
        linewidth=1, edgecolor='#334155', facecolor='#1E293B'
    )
    ax.add_patch(ribbon)

    ax.text(0.08, 0.12, "CORE GUARANTEE:", fontsize=10, fontweight='bold', color='#38BDF8', va='center')
    ax.text(0.08, 0.09, "Non-Destructive Ingestion", fontsize=9, color='#94A3B8', va='center')

    ax.text(0.32, 0.12, "IDEMPOTENCY:", fontsize=10, fontweight='bold', color='#38BDF8', va='center')
    ax.text(0.32, 0.09, "SHA-256 Fingerprinting", fontsize=9, color='#94A3B8', va='center')

    ax.text(0.56, 0.12, "FINANCIAL INTEGRITY:", fontsize=10, fontweight='bold', color='#38BDF8', va='center')
    ax.text(0.56, 0.09, "NUMERIC(18,4) & Currency Isolation", fontsize=9, color='#94A3B8', va='center')

    ax.text(0.81, 0.12, "AUDIT TRAIL:", fontsize=10, fontweight='bold', color='#38BDF8', va='center')
    ax.text(0.81, 0.09, "Full Exception Provenance", fontsize=9, color='#94A3B8', va='center')

    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, 1.0)
    ax.axis('off')

    out_path = IMAGES_DIR / "dataguard_data_lineage.png"
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Created: {out_path}")


def create_scorecard_diagram():
    fig, ax = plt.subplots(figsize=(14, 7), dpi=300)
    fig.patch.set_facecolor('#0F172A')
    ax.set_facecolor('#0F172A')

    # Title
    ax.text(0.5, 0.92, "DataGuard | Production Quality & Execution Scorecard", 
            fontsize=18, fontweight='bold', color='#FFFFFF', ha='center', va='center')
    ax.text(0.5, 0.87, "Actual verified pipeline results from test runs against PostgreSQL 18 & Pytest Suite", 
            fontsize=10, color='#94A3B8', ha='center', va='center')

    # KPI Metric Boxes
    metrics = [
        {"title": "Overall Quality Score", "val": "98.43%", "sub": "Target: >= 98.50%", "color": "#10B981"},
        {"title": "Anomaly Recall", "val": "100%", "sub": "17 / 17 Injected Caught", "color": "#3B82F6"},
        {"title": "Automated Tests", "val": "28 / 28", "sub": "Unit, Integration & Regression", "color": "#8B5CF6"},
        {"title": "Reconciliation Matches", "val": "320", "sub": "Isolated by Currency", "color": "#F59E0B"},
    ]

    box_w = 0.20
    box_h = 0.22
    for i, m in enumerate(metrics):
        x = 0.07 + (i * 0.225)
        box = patches.FancyBboxPatch((x, 0.58), box_w, box_h,
                                     boxstyle="round,pad=0.012,rounding_size=0.015",
                                     linewidth=1.5, edgecolor=m["color"], facecolor='#1E293B')
        ax.add_patch(box)
        ax.text(x + box_w/2, 0.74, m["title"], fontsize=9.5, fontweight='semibold', color='#94A3B8', ha='center')
        ax.text(x + box_w/2, 0.67, m["val"], fontsize=18, fontweight='bold', color='#FFFFFF', ha='center')
        ax.text(x + box_w/2, 0.61, m["sub"], fontsize=8.5, color=m["color"], ha='center')

    # Quality Dimensions Breakdown Bar
    dims = [
        {"name": "Completeness", "score": "98.02%", "desc": "6 Mandatory Fields Checked (DQ001-DQ006)", "wt": "25% Weight"},
        {"name": "Validity", "score": "97.69%", "desc": "Sign, Outlier & Precision Checks (DQ010-DQ012)", "wt": "35% Weight"},
        {"name": "Uniqueness", "score": "99.01%", "desc": "Payload, ID & Business Duplicates (DQ007-DQ009)", "wt": "20% Weight"},
        {"name": "Integrity", "score": "99.67%", "desc": "Active Customer Account References (DQ015)", "wt": "20% Weight"},
    ]

    for idx, d in enumerate(dims):
        y = 0.44 - (idx * 0.09)
        dim_card = patches.FancyBboxPatch((0.07, y), 0.875, 0.075,
                                          boxstyle="round,pad=0.008,rounding_size=0.01",
                                          linewidth=1, edgecolor='#334155', facecolor='#1E293B')
        ax.add_patch(dim_card)
        ax.text(0.10, y + 0.038, d["name"], fontsize=11, fontweight='bold', color='#F8FAFC', va='center')
        ax.text(0.32, y + 0.038, d["desc"], fontsize=9, color='#94A3B8', va='center')
        ax.text(0.74, y + 0.038, d["wt"], fontsize=9, color='#38BDF8', va='center')
        ax.text(0.91, y + 0.038, d["score"], fontsize=11, fontweight='bold', color='#10B981', ha='right', va='center')

    ax.set_xlim(0, 1.0)
    ax.set_ylim(0, 1.0)
    ax.axis('off')

    out_path = IMAGES_DIR / "dataguard_quality_scorecard.png"
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Created: {out_path}")


if __name__ == "__main__":
    create_data_lineage_diagram()
    create_scorecard_diagram()
