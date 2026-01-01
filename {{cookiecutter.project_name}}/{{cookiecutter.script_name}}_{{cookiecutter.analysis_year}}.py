"""
Portfolio Analysis Script - {{ cookiecutter.analysis_year }} Projections

Hydra-based portfolio tracker with:
- Best/worst case scenario projections based on analyst targets
- Monthly monitoring with P&L tracking
- Position open/closed status with realized P&L
- Results organized by month/year

Usage:
    python {{ cookiecutter.script_name }}.py                    # Run analysis
    python {{ cookiecutter.script_name }}.py mode=update        # Update prices
    python {{ cookiecutter.script_name }}.py mode=report        # Generate report
"""

import os
from datetime import datetime

import hydra
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from conf.{{ cookiecutter.config_name }} import {{ cookiecutter.config_name }}
from hydra.core.config_store import ConfigStore

matplotlib.use("Agg")

# Register dataclass with ConfigStore
configstore = ConfigStore.instance()
configstore.store(name="portfolio_base", node={{ cookiecutter.config_name }})

# Colors
REALIZED_COLOR = "royalblue"
PROFIT_COLOR = "green"
LOSS_COLOR = "red"


def calculate_portfolio_values(positions):
    """Calculate current, best case, and worst case portfolio values.

    Returns tuple of (open_positions_df, closed_positions_df)
    """
    open_results = []
    closed_results = []

    for pos in positions:
        buy_value = pos.shares * pos.buy_price_eur

        if pos.is_open:
            # Open position - unrealized P&L
            current_value = pos.shares * pos.current_price_eur
            best_value = pos.shares * pos.target_high_eur
            worst_value = pos.shares * pos.target_low_eur

            unrealized_pnl = current_value - buy_value
            unrealized_pnl_pct = (
                (unrealized_pnl / buy_value) * 100 if buy_value > 0 else 0
            )

            best_pnl = best_value - buy_value
            best_pnl_pct = (best_pnl / buy_value) * 100 if buy_value > 0 else 0

            worst_pnl = worst_value - buy_value
            worst_pnl_pct = (worst_pnl / buy_value) * 100 if buy_value > 0 else 0

            open_results.append(
                {
                    "ticker": pos.ticker,
                    "shares": pos.shares,
                    "buy_price": pos.buy_price_eur,
                    "current_price": pos.current_price_eur,
                    "target_low": pos.target_low_eur,
                    "target_high": pos.target_high_eur,
                    "buy_value": buy_value,
                    "current_value": current_value,
                    "best_value": best_value,
                    "worst_value": worst_value,
                    "unrealized_pnl": unrealized_pnl,
                    "unrealized_pnl_pct": unrealized_pnl_pct,
                    "best_pnl": best_pnl,
                    "best_pnl_pct": best_pnl_pct,
                    "worst_pnl": worst_pnl,
                    "worst_pnl_pct": worst_pnl_pct,
                    "notes": pos.notes,
                }
            )
        else:
            # Closed position - use sell_price_eur for realized P&L
            if pos.sell_price_eur is None:
                continue  # Skip if no sell price set
            sell_value = pos.shares * pos.sell_price_eur
            realized_pnl = sell_value - buy_value
            realized_pnl_pct = (
                (realized_pnl / buy_value) * 100 if buy_value > 0 else 0
            )

            closed_results.append(
                {
                    "ticker": pos.ticker,
                    "shares": pos.shares,
                    "buy_price": pos.buy_price_eur,
                    "sell_price": pos.sell_price_eur,
                    "buy_value": buy_value,
                    "sell_value": sell_value,
                    "realized_pnl": realized_pnl,
                    "realized_pnl_pct": realized_pnl_pct,
                    "notes": pos.notes,
                }
            )

    df_open = pd.DataFrame(open_results) if open_results else pd.DataFrame()
    df_closed = pd.DataFrame(closed_results) if closed_results else pd.DataFrame()

    return df_open, df_closed


def plot_portfolio_scenarios(df_open, df_closed, output_dir, year):
    """Plot best/worst case scenarios for portfolio."""
    if df_open.empty:
        print("No open positions to plot")
        return

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Sort by current value for better visualization
    df_sorted = df_open.sort_values("current_value", ascending=True)

    # Plot 1: Current vs Buy Value (Unrealized P&L)
    ax = axes[0, 0]
    y_pos = np.arange(len(df_sorted))
    width = 0.35

    ax.barh(
        y_pos - width / 2,
        df_sorted["buy_value"],
        width,
        label="Buy Value",
        color="gray",
        alpha=0.7,
    )
    ax.barh(
        y_pos + width / 2,
        df_sorted["current_value"],
        width,
        label="Current Value",
        color=[
            PROFIT_COLOR if x > 0 else LOSS_COLOR
            for x in df_sorted["unrealized_pnl"]
        ],
        alpha=0.7,
    )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_sorted["ticker"])
    ax.set_xlabel("Value (EUR)")
    ax.set_title("Current Holdings vs Buy Value")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="x")

    # Plot 2: Best vs Worst Case per Stock
    ax = axes[0, 1]
    x_pos = np.arange(len(df_sorted))

    ax.bar(x_pos - 0.2, df_sorted["worst_value"], 0.2, label="Worst Case", color=LOSS_COLOR, alpha=0.7)
    ax.bar(x_pos, df_sorted["current_value"], 0.2, label="Current", color="blue", alpha=0.7)
    ax.bar(x_pos + 0.2, df_sorted["best_value"], 0.2, label="Best Case", color=PROFIT_COLOR, alpha=0.7)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(df_sorted["ticker"], rotation=45, ha="right")
    ax.set_ylabel("Value (EUR)")
    ax.set_title("Scenario Comparison by Stock")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    # Plot 3: Portfolio Summary Pie Charts
    ax = axes[1, 0]
    total_current = df_open["current_value"].sum()
    sizes = df_sorted["current_value"]
    wedges, texts = ax.pie(sizes, labels=[""] * len(sizes), startangle=90)
    ax.legend(wedges, df_sorted["ticker"], title="Ticker", loc="center left", bbox_to_anchor=(1, 0.5), fontsize=8)
    ax.set_title(f"Current Portfolio Allocation\nTotal: €{total_current:,.0f}")

    # Plot 4: P&L Summary
    ax = axes[1, 1]
    total_buy = df_open["buy_value"].sum()
    total_current = df_open["current_value"].sum()
    total_best = df_open["best_value"].sum()
    total_worst = df_open["worst_value"].sum()

    total_realized = df_closed["realized_pnl"].sum() if not df_closed.empty else 0

    scenarios = ["Buy Value", "Current", "Worst Case", "Best Case"]
    values = [total_buy, total_current, total_worst, total_best]
    colors = ["gray", "blue", LOSS_COLOR, PROFIT_COLOR]

    bars = ax.bar(scenarios, values, color=colors, alpha=0.7, edgecolor="black")
    ax.set_ylabel("Portfolio Value (EUR)")
    ax.set_title(f"Portfolio Scenarios - {year}")

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1000, f"€{val:,.0f}", ha="center", va="bottom", fontsize=10)

    worst_pct = ((total_worst - total_buy) / total_buy) * 100
    best_pct = ((total_best - total_buy) / total_buy) * 100

    ax.axhline(total_buy, color="gray", linestyle="--", alpha=0.5)
    ax.text(3.5, total_best, f"+{best_pct:.1f}%", fontsize=12, color=PROFIT_COLOR, fontweight="bold")
    ax.text(2.5, total_worst, f"{worst_pct:.1f}%", fontsize=12, color=LOSS_COLOR, fontweight="bold")

    if total_realized != 0:
        ax.text(0.02, 0.98, f"Realized P&L: €{total_realized:+,.0f}", transform=ax.transAxes, fontsize=11, fontweight="bold", color=REALIZED_COLOR, ha="left", va="top", bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

    ax.grid(True, alpha=0.3, axis="y")

    plt.suptitle(f"Portfolio Analysis - {year} Projections", fontsize=14, fontweight="bold")
    plt.tight_layout()

    output_path = os.path.join(output_dir, "portfolio_scenarios.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_individual_positions(df_open, output_dir):
    """Plot individual position analysis."""
    if df_open.empty:
        print("No open positions to plot")
        return

    n_positions = len(df_open)
    n_cols = 4
    n_rows = (n_positions + n_cols - 1) // n_cols
    n_rows = max(n_rows, 1)

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 5 * n_rows))
    if n_rows == 1 and n_cols == 1:
        axes = np.array([[axes]])
    elif n_rows == 1:
        axes = axes.reshape(1, -1)
    axes = axes.flatten()

    for idx, (_, row) in enumerate(df_open.iterrows()):
        if idx >= len(axes):
            break

        ax = axes[idx]
        scenarios = ["Worst", "Current", "Best"]
        values = [row["worst_value"], row["current_value"], row["best_value"]]
        colors = [LOSS_COLOR, "blue", PROFIT_COLOR]

        bars = ax.bar(scenarios, values, color=colors, alpha=0.7, edgecolor="black")
        ax.axhline(row["buy_value"], color="orange", linestyle="--", linewidth=2, label="Buy Value")
        ax.set_title(f"{row['ticker']}\n{row['shares']} shares")
        ax.set_ylabel("Value (EUR)")

        for bar, val, scenario in zip(bars, values, scenarios):
            pnl = val - row["buy_value"]
            pnl_pct = (pnl / row["buy_value"]) * 100
            color = PROFIT_COLOR if pnl > 0 else LOSS_COLOR
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{pnl_pct:+.0f}%", ha="center", va="bottom", fontsize=9, color=color)

        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis="y")

    for idx in range(len(df_open), len(axes)):
        axes[idx].set_visible(False)

    plt.suptitle("Individual Position Analysis", fontsize=14, fontweight="bold")
    plt.tight_layout()

    output_path = os.path.join(output_dir, "position_analysis.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_pnl_waterfall(df_open, df_closed, output_dir):
    """Plot P&L waterfall chart with realized P&L in royal blue."""
    has_open = not df_open.empty
    has_closed = not df_closed.empty

    if not has_open and not has_closed:
        print("No positions to plot")
        return

    fig, ax = plt.subplots(figsize=(14, 6))

    tickers = []
    pnl_values = []
    colors = []

    if has_closed:
        df_closed_sorted = df_closed.sort_values("realized_pnl", ascending=False)
        for _, row in df_closed_sorted.iterrows():
            tickers.append(f"{row['ticker']} (closed)")
            pnl_values.append(row["realized_pnl"])
            colors.append(REALIZED_COLOR)

    if has_open:
        df_open_sorted = df_open.sort_values("unrealized_pnl", ascending=False)
        for _, row in df_open_sorted.iterrows():
            tickers.append(row["ticker"])
            pnl_values.append(row["unrealized_pnl"])
            colors.append(PROFIT_COLOR if row["unrealized_pnl"] > 0 else LOSS_COLOR)

    ax.bar(tickers, pnl_values, color=colors, alpha=0.7, edgecolor="black")
    ax.axhline(0, color="black", linewidth=1)
    ax.set_xlabel("Stock")
    ax.set_ylabel("P&L (EUR)")
    ax.set_title("P&L by Position (Royal Blue = Realized, Green/Red = Unrealized)")
    ax.grid(True, alpha=0.3, axis="y")

    plt.xticks(rotation=45, ha="right")

    total_unrealized = df_open["unrealized_pnl"].sum() if has_open else 0
    total_realized = df_closed["realized_pnl"].sum() if has_closed else 0
    total_pnl = total_unrealized + total_realized

    total_color = PROFIT_COLOR if total_pnl > 0 else LOSS_COLOR

    info_text = f"Total P&L: €{total_pnl:+,.0f}"
    if has_closed and has_open:
        info_text += f"\n(Realized: €{total_realized:+,.0f}, Unrealized: €{total_unrealized:+,.0f})"

    ax.text(0.98, 0.98, info_text, transform=ax.transAxes, fontsize=11, fontweight="bold", color=total_color, ha="right", va="top", bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

    plt.tight_layout()

    output_path = os.path.join(output_dir, "pnl_waterfall.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def save_history(df_open, df_closed, cfg, output_dir):
    """Save current portfolio state to history file."""
    history_path = os.path.join(output_dir, cfg.monitoring.history_file)

    total_unrealized = df_open["unrealized_pnl"].sum() if not df_open.empty else 0
    total_realized = df_closed["realized_pnl"].sum() if not df_closed.empty else 0

    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_buy_value": df_open["buy_value"].sum() if not df_open.empty else 0,
        "total_current_value": df_open["current_value"].sum() if not df_open.empty else 0,
        "total_unrealized_pnl": total_unrealized,
        "total_realized_pnl": total_realized,
        "total_pnl": total_unrealized + total_realized,
        "total_best_value": df_open["best_value"].sum() if not df_open.empty else 0,
        "total_worst_value": df_open["worst_value"].sum() if not df_open.empty else 0,
        "open_positions": len(df_open),
        "closed_positions": len(df_closed),
    }

    if not df_open.empty:
        for _, row in df_open.iterrows():
            summary[f"{row['ticker']}_price"] = row["current_price"]
            summary[f"{row['ticker']}_value"] = row["current_value"]

    summary_df = pd.DataFrame([summary])

    if os.path.exists(history_path):
        existing = pd.read_csv(history_path)
        if summary["date"] in existing["date"].values:
            existing = existing[existing["date"] != summary["date"]]
        combined = pd.concat([existing, summary_df], ignore_index=True)
    else:
        combined = summary_df

    combined.to_csv(history_path, index=False)
    print(f"Saved history: {history_path}")


def print_summary(df_open, df_closed, year):
    """Print portfolio summary to console."""
    has_open = not df_open.empty
    has_closed = not df_closed.empty

    print("\n" + "=" * 80)
    print(f"PORTFOLIO SUMMARY - {year}")
    print("=" * 80)

    if has_open:
        total_buy = df_open["buy_value"].sum()
        total_current = df_open["current_value"].sum()
        unrealized_pnl = total_current - total_buy
        unrealized_pnl_pct = (unrealized_pnl / total_buy) * 100 if total_buy > 0 else 0

        print(f"\nOPEN POSITIONS ({len(df_open)})")
        print(f"{'Position':<12} {'Shares':>8} {'Buy':>10} {'Current':>10} {'P&L':>12} {'P&L%':>8}")
        print("-" * 80)

        for _, row in df_open.iterrows():
            pnl_str = f"€{row['unrealized_pnl']:+,.0f}"
            pnl_pct_str = f"{row['unrealized_pnl_pct']:+.1f}%"
            print(f"{row['ticker']:<12} {row['shares']:>8} €{row['buy_price']:>9,.2f} €{row['current_price']:>9,.2f} {pnl_str:>12} {pnl_pct_str:>8}")

        print("-" * 80)
        print(f"{'SUBTOTAL':<12} {'':>8} €{total_buy:>9,.0f} €{total_current:>9,.0f} €{unrealized_pnl:>+11,.0f} {unrealized_pnl_pct:>+7.1f}%")

    if has_closed:
        total_realized = df_closed["realized_pnl"].sum()

        print(f"\nCLOSED POSITIONS ({len(df_closed)}) - Realized P&L")
        print(f"{'Position':<12} {'Shares':>8} {'Buy':>10} {'Sell':>10} {'P&L':>12} {'P&L%':>8}")
        print("-" * 80)

        for _, row in df_closed.iterrows():
            pnl_str = f"€{row['realized_pnl']:+,.0f}"
            pnl_pct_str = f"{row['realized_pnl_pct']:+.1f}%"
            print(f"{row['ticker']:<12} {row['shares']:>8} €{row['buy_price']:>9,.2f} €{row['sell_price']:>9,.2f} {pnl_str:>12} {pnl_pct_str:>8}")

        print("-" * 80)
        print(f"{'REALIZED':<12} {'':>8} {'':>10} {'':>10} €{total_realized:>+11,.0f}")

    total_unrealized = df_open["unrealized_pnl"].sum() if has_open else 0
    total_realized = df_closed["realized_pnl"].sum() if has_closed else 0
    grand_total = total_unrealized + total_realized

    print("\n" + "=" * 80)
    print(f"TOTAL P&L: €{grand_total:+,.0f}")
    if has_open and has_closed:
        print(f"  Unrealized: €{total_unrealized:+,.0f}")
        print(f"  Realized:   €{total_realized:+,.0f}")
    print("=" * 80)

    if has_open:
        total_buy = df_open["buy_value"].sum()
        total_current = df_open["current_value"].sum()
        total_best = df_open["best_value"].sum()
        total_worst = df_open["worst_value"].sum()

        unrealized_pnl_pct = ((total_current - total_buy) / total_buy) * 100
        best_pnl_pct = ((total_best - total_buy) / total_buy) * 100
        worst_pnl_pct = ((total_worst - total_buy) / total_buy) * 100

        print("\nSCENARIO PROJECTIONS (Open Positions)")
        print("-" * 80)
        print(f"  Current Value:    €{total_current:>12,.0f}  ({unrealized_pnl_pct:+.1f}% from buy)")
        print(f"  Best Case {year}:   €{total_best:>12,.0f}  ({best_pnl_pct:+.1f}% from buy)")
        print(f"  Worst Case {year}:  €{total_worst:>12,.0f}  ({worst_pnl_pct:+.1f}% from buy)")


@hydra.main(version_base="1.3", config_path="conf", config_name="{{ cookiecutter.config_name }}")
def main(cfg: {{ cookiecutter.config_name }}):
    """Main entry point with Hydra configuration."""
    print("=" * 80)
    print("PORTFOLIO ANALYSIS")
    print("=" * 80)

    current_month = datetime.now().strftime("%Y-%m")

    if cfg.output.verbose:
        print("\nConfiguration:")
        print(f"  Analysis Year: {cfg.settings.analysis_year}")
        print(f"  Analysis Month: {current_month}")
        print(f"  USD/EUR Rate: {cfg.settings.usd_to_eur}")
        print(f"  Positions: {len(cfg.positions)}")
        print(f"  Last Update: {cfg.monitoring.last_update}")

    base_output_dir = cfg.output.output_dir
    output_dir = os.path.join(base_output_dir, current_month)
    os.makedirs(output_dir, exist_ok=True)

    df_open, df_closed = calculate_portfolio_values(cfg.positions)

    print_summary(df_open, df_closed, cfg.settings.analysis_year)

    if not df_open.empty:
        csv_path = os.path.join(output_dir, "open_positions.csv")
        df_open.to_csv(csv_path, index=False)
        print(f"\nSaved: {csv_path}")

    if not df_closed.empty:
        csv_path = os.path.join(output_dir, "closed_positions.csv")
        df_closed.to_csv(csv_path, index=False)
        print(f"Saved: {csv_path}")

    if cfg.output.save_plots:
        print("\nGenerating plots...")
        plot_portfolio_scenarios(df_open, df_closed, output_dir, cfg.settings.analysis_year)
        plot_individual_positions(df_open, output_dir)
        plot_pnl_waterfall(df_open, df_closed, output_dir)

    if cfg.monitoring.save_history:
        save_history(df_open, df_closed, cfg, output_dir)

    print("\n" + "=" * 80)
    print(f"ANALYSIS COMPLETE - Results saved to: {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
