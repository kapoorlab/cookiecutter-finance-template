"""
Update Portfolio Prices from Yahoo Finance

Fetches current stock prices and USD/EUR exchange rate, then updates the YAML config.

Usage:
    python update_prices.py              # Update prices and show changes
    python update_prices.py --dry-run    # Show what would change without writing

Requirements:
    pip install yfinance
"""

import argparse
import re
from datetime import datetime
from pathlib import Path

import yfinance as yf

# Mapping from portfolio ticker to Yahoo Finance ticker
# Add your tickers here: "YOUR_TICKER": "YAHOO_TICKER"
TICKER_MAP = {
    "EXAMPLE": "AAPL",  # Example mapping - replace with your own
}

# Which tickers are in USD (need conversion to EUR)
USD_TICKERS = {
    "EXAMPLE",  # Add tickers that trade in USD
}


def fetch_usd_eur_rate() -> float:
    """Fetch current USD/EUR exchange rate from Yahoo Finance."""
    ticker = yf.Ticker("EURUSD=X")
    data = ticker.history(period="1d")
    if data.empty:
        raise ValueError("Could not fetch USD/EUR rate")
    eur_per_usd = data["Close"].iloc[-1]
    usd_to_eur = 1 / eur_per_usd
    return usd_to_eur


def fetch_stock_prices(tickers: list[str]) -> dict[str, float]:
    """Fetch current stock prices from Yahoo Finance."""
    prices = {}
    yahoo_tickers = list({TICKER_MAP.get(t, t) for t in tickers})

    print(f"Fetching prices for: {', '.join(yahoo_tickers)}")

    for yahoo_ticker in yahoo_tickers:
        try:
            ticker = yf.Ticker(yahoo_ticker)
            data = ticker.history(period="1d")
            if not data.empty:
                prices[yahoo_ticker] = data["Close"].iloc[-1]
            else:
                print(f"  Warning: No data for {yahoo_ticker}")
        except Exception as e:
            print(f"  Error fetching {yahoo_ticker}: {e}")

    return prices


def fetch_analyst_targets(tickers: list[str]) -> dict[str, dict]:
    """Fetch analyst price targets from Yahoo Finance.

    Returns dict with: targetHighPrice, targetLowPrice, targetMeanPrice, numberOfAnalystOpinions
    """
    targets = {}
    yahoo_tickers = list({TICKER_MAP.get(t, t) for t in tickers})

    print(f"Fetching analyst targets for: {', '.join(yahoo_tickers)}")

    for yahoo_ticker in yahoo_tickers:
        try:
            ticker = yf.Ticker(yahoo_ticker)
            info = ticker.info
            target_data = {}

            if "targetHighPrice" in info and info["targetHighPrice"]:
                target_data["high"] = info["targetHighPrice"]
            if "targetLowPrice" in info and info["targetLowPrice"]:
                target_data["low"] = info["targetLowPrice"]
            if "targetMeanPrice" in info and info["targetMeanPrice"]:
                target_data["mean"] = info["targetMeanPrice"]
            if "numberOfAnalystOpinions" in info and info["numberOfAnalystOpinions"]:
                target_data["analysts"] = info["numberOfAnalystOpinions"]

            if target_data:
                targets[yahoo_ticker] = target_data
                print(f"  {yahoo_ticker}: Low ${target_data.get('low', 'N/A')}, "
                      f"Mean ${target_data.get('mean', 'N/A')}, High ${target_data.get('high', 'N/A')} "
                      f"({target_data.get('analysts', '?')} analysts)")
            else:
                print(f"  {yahoo_ticker}: No analyst data available")
        except Exception as e:
            print(f"  Error fetching {yahoo_ticker}: {e}")

    return targets


def update_yaml_file(yaml_path: Path, prices: dict, usd_to_eur: float,
                     targets: dict = None, dry_run: bool = False):
    """Update the YAML config file with new prices and analyst targets."""
    content = yaml_path.read_text()
    original_content = content

    changes = []
    target_changes = []

    # Update USD/EUR rate
    old_rate_match = re.search(r"usd_to_eur:\s*([\d.]+)", content)
    if old_rate_match:
        old_rate = float(old_rate_match.group(1))
        if abs(old_rate - usd_to_eur) > 0.001:
            content = re.sub(r"(usd_to_eur:\s*)[\d.]+", f"\\g<1>{usd_to_eur:.4f}", content)
            changes.append(f"USD/EUR: {old_rate:.4f} -> {usd_to_eur:.4f}")

    # Update last_update date
    today = datetime.now().strftime("%Y-%m-%d")
    content = re.sub(r'(last_update:\s*")[^"]*(")', f"\\g<1>{today}\\2", content)

    # Update each position's current_price_eur and analyst targets (only open positions)
    for portfolio_ticker, yahoo_ticker in TICKER_MAP.items():
        # Find this ticker's block and check if it's open
        block_pattern = rf"(- ticker: {portfolio_ticker}\s+.*?)(?=\n  - ticker:|\Z)"
        block_match = re.search(block_pattern, content, re.DOTALL)

        if not block_match:
            continue

        block = block_match.group(1)

        # Skip closed positions
        if "is_open: false" in block:
            continue

        # Update current price if available
        if yahoo_ticker in prices:
            price_usd = prices[yahoo_ticker]

            # Convert to EUR if needed
            if portfolio_ticker in USD_TICKERS:
                price_eur = price_usd * usd_to_eur
            else:
                price_eur = price_usd

            # Find and update this ticker's current_price_eur in the YAML
            pattern = rf"(- ticker: {portfolio_ticker}\s+.*?current_price_eur:\s*)([\d.]+)"
            match = re.search(pattern, content, re.DOTALL)

            if match:
                old_price = float(match.group(2))
                if abs(old_price - price_eur) > 0.01:
                    content = re.sub(pattern, f"\\g<1>{price_eur:.5f}", content, flags=re.DOTALL)
                    pct_change = ((price_eur - old_price) / old_price) * 100
                    changes.append(f"{portfolio_ticker}: €{old_price:.2f} -> €{price_eur:.2f} ({pct_change:+.1f}%)")

        # Update analyst targets if available
        if targets and yahoo_ticker in targets:
            target_data = targets[yahoo_ticker]

            # Convert to EUR if needed
            if portfolio_ticker in USD_TICKERS:
                high_eur = target_data.get("high", 0) * usd_to_eur if target_data.get("high") else None
                low_eur = target_data.get("low", 0) * usd_to_eur if target_data.get("low") else None
            else:
                high_eur = target_data.get("high")
                low_eur = target_data.get("low")

            # Update best_case_price (analyst high)
            if high_eur:
                pattern = rf"(- ticker: {portfolio_ticker}\s+.*?best_case_price:\s*)([\d.]+)"
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    old_best = float(match.group(2))
                    if abs(old_best - high_eur) > 0.01:
                        content = re.sub(pattern, f"\\g<1>{high_eur:.5f}", content, flags=re.DOTALL)
                        target_changes.append(f"{portfolio_ticker} best: €{old_best:.2f} -> €{high_eur:.2f}")

            # Update worst_case_price (analyst low)
            if low_eur:
                pattern = rf"(- ticker: {portfolio_ticker}\s+.*?worst_case_price:\s*)([\d.]+)"
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    old_worst = float(match.group(2))
                    if abs(old_worst - low_eur) > 0.01:
                        content = re.sub(pattern, f"\\g<1>{low_eur:.5f}", content, flags=re.DOTALL)
                        target_changes.append(f"{portfolio_ticker} worst: €{old_worst:.2f} -> €{low_eur:.2f}")

    # Print changes
    if changes:
        print("\nPrice changes:")
        for change in changes:
            print(f"  {change}")
    else:
        print("\nNo significant price changes")

    if target_changes:
        print("\nAnalyst target changes:")
        for change in target_changes:
            print(f"  {change}")

    # Write if not dry run
    if not dry_run and content != original_content:
        yaml_path.write_text(content)
        print(f"\nUpdated: {yaml_path}")
    elif dry_run:
        print("\n[Dry run - no changes written]")


def main():
    parser = argparse.ArgumentParser(description="Update portfolio prices from Yahoo Finance")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--no-targets", action="store_true", help="Skip fetching analyst targets")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    yaml_path = script_dir / "conf" / "{{ cookiecutter.config_name }}.yaml"

    if not yaml_path.exists():
        print(f"Error: {yaml_path} not found")
        return 1

    print("=" * 60)
    print("PORTFOLIO PRICE UPDATE")
    print("=" * 60)

    # Fetch exchange rate
    print("\nFetching USD/EUR rate...")
    try:
        usd_to_eur = fetch_usd_eur_rate()
        print(f"  USD/EUR: {usd_to_eur:.4f}")
    except Exception as e:
        print(f"  Error: {e}")
        return 1

    # Fetch stock prices
    print("\nFetching stock prices...")
    tickers = list(TICKER_MAP.keys())
    prices = fetch_stock_prices(tickers)

    if not prices:
        print("Error: Could not fetch any prices")
        return 1

    # Fetch analyst targets
    targets = None
    if not args.no_targets:
        print("\nFetching analyst targets...")
        targets = fetch_analyst_targets(tickers)

    # Update YAML
    update_yaml_file(yaml_path, prices, usd_to_eur, targets=targets, dry_run=args.dry_run)

    print("\n" + "=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
