"""
Update Portfolio Prices from Yahoo Finance

Fetches current stock prices, analyst targets, and USD/EUR exchange rate,
then updates the YAML config. Reads ticker mappings directly from the YAML.

Usage:
    python update_prices.py              # Update prices and analyst targets
    python update_prices.py --dry-run    # Show what would change without writing
    python update_prices.py --no-targets # Skip fetching analyst targets

Requirements:
    pip install yfinance pyyaml
"""

import argparse
import re
from datetime import datetime
from pathlib import Path

import yaml
import yfinance as yf


def load_positions_from_yaml(yaml_path: Path) -> list[dict]:
    """Load positions from YAML config file."""
    content = yaml_path.read_text()
    config = yaml.safe_load(content)
    return config.get("positions", [])


def fetch_usd_eur_rate() -> float:
    """Fetch current USD/EUR exchange rate from Yahoo Finance."""
    ticker = yf.Ticker("EURUSD=X")
    data = ticker.history(period="1d")
    if data.empty:
        raise ValueError("Could not fetch USD/EUR rate")
    eur_per_usd = data["Close"].iloc[-1]
    usd_to_eur = 1 / eur_per_usd
    return usd_to_eur


def fetch_stock_prices(yahoo_tickers: list[str]) -> dict[str, float]:
    """Fetch current stock prices from Yahoo Finance."""
    prices = {}
    unique_tickers = list(set(yahoo_tickers))

    print(f"Fetching prices for: {', '.join(unique_tickers)}")

    for yahoo_ticker in unique_tickers:
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


def fetch_analyst_targets(yahoo_tickers: list[str]) -> dict[str, dict]:
    """Fetch analyst price targets from Yahoo Finance."""
    targets = {}
    unique_tickers = list(set(yahoo_tickers))

    print(f"Fetching analyst targets for: {', '.join(unique_tickers)}")

    for yahoo_ticker in unique_tickers:
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
                print(
                    f"  {yahoo_ticker}: Low ${target_data.get('low', 'N/A')}, "
                    f"Mean ${target_data.get('mean', 'N/A')}, High ${target_data.get('high', 'N/A')} "
                    f"({target_data.get('analysts', '?')} analysts)"
                )
            else:
                print(f"  {yahoo_ticker}: No analyst data available")
        except Exception as e:
            print(f"  Error fetching {yahoo_ticker}: {e}")

    return targets


def update_yaml_file(
    yaml_path: Path,
    positions: list[dict],
    prices: dict,
    usd_to_eur: float,
    targets: dict = None,
    dry_run: bool = False,
):
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
            content = re.sub(
                r"(usd_to_eur:\s*)[\d.]+", f"\\g<1>{usd_to_eur:.4f}", content
            )
            changes.append(f"USD/EUR: {old_rate:.4f} -> {usd_to_eur:.4f}")

    # Update last_update date
    today = datetime.now().strftime("%Y-%m-%d")
    content = re.sub(
        r'(last_update:\s*")[^"]*(")', f"\\g<1>{today}\\2", content
    )

    # Update each position
    for pos in positions:
        ticker = pos.get("ticker", "")
        yahoo_ticker = pos.get("yahoo_ticker", "")
        currency = pos.get("currency", "EUR")
        is_open = pos.get("is_open", True)

        if not yahoo_ticker or not is_open:
            continue

        needs_conversion = currency == "USD"

        # Update current price if available
        if yahoo_ticker in prices:
            price_raw = prices[yahoo_ticker]
            price_eur = price_raw * usd_to_eur if needs_conversion else price_raw

            # Find and update this ticker's current_price_eur in the YAML
            pattern = rf"(- ticker: {ticker}\s+.*?current_price_eur:\s*)([\d.]+)"
            match = re.search(pattern, content, re.DOTALL)

            if match:
                old_price = float(match.group(2))
                if abs(old_price - price_eur) > 0.01:
                    content = re.sub(
                        pattern,
                        f"\\g<1>{price_eur:.5f}",
                        content,
                        flags=re.DOTALL,
                    )
                    pct_change = ((price_eur - old_price) / old_price) * 100 if old_price > 0 else 0
                    changes.append(
                        f"{ticker}: €{old_price:.2f} -> €{price_eur:.2f} ({pct_change:+.1f}%)"
                    )

        # Update analyst targets if available
        if targets and yahoo_ticker in targets:
            target_data = targets[yahoo_ticker]

            high_raw = target_data.get("high")
            low_raw = target_data.get("low")

            # Update target_high_eur (analyst high)
            if high_raw:
                high_eur = high_raw * usd_to_eur if needs_conversion else high_raw
                pattern = rf"(- ticker: {ticker}\s+.*?target_high_eur:\s*)([\d.]+)"
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    old_high = float(match.group(2))
                    if abs(old_high - high_eur) > 0.01:
                        content = re.sub(
                            pattern,
                            f"\\g<1>{high_eur:.5f}",
                            content,
                            flags=re.DOTALL,
                        )
                        target_changes.append(
                            f"{ticker} high: €{old_high:.2f} -> €{high_eur:.2f}"
                        )

            # Update target_low_eur (analyst low)
            if low_raw:
                low_eur = low_raw * usd_to_eur if needs_conversion else low_raw
                pattern = rf"(- ticker: {ticker}\s+.*?target_low_eur:\s*)([\d.]+)"
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    old_low = float(match.group(2))
                    if abs(old_low - low_eur) > 0.01:
                        content = re.sub(
                            pattern,
                            f"\\g<1>{low_eur:.5f}",
                            content,
                            flags=re.DOTALL,
                        )
                        target_changes.append(
                            f"{ticker} low: €{old_low:.2f} -> €{low_eur:.2f}"
                        )

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
    parser = argparse.ArgumentParser(
        description="Update portfolio prices from Yahoo Finance"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without writing"
    )
    parser.add_argument(
        "--no-targets",
        action="store_true",
        help="Skip fetching analyst targets",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    yaml_path = script_dir / "conf" / "{{ cookiecutter.config_name }}.yaml"

    if not yaml_path.exists():
        print(f"Error: {yaml_path} not found")
        return 1

    print("=" * 60)
    print("PORTFOLIO PRICE UPDATE")
    print("=" * 60)

    # Load positions from YAML
    print("\nLoading positions from YAML...")
    positions = load_positions_from_yaml(yaml_path)
    open_positions = [p for p in positions if p.get("is_open", True) and p.get("yahoo_ticker")]
    print(f"  Found {len(open_positions)} open positions with Yahoo tickers")

    if not open_positions:
        print("Error: No open positions with yahoo_ticker found")
        return 1

    # Get list of Yahoo tickers
    yahoo_tickers = [p["yahoo_ticker"] for p in open_positions]

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
    prices = fetch_stock_prices(yahoo_tickers)

    if not prices:
        print("Error: Could not fetch any prices")
        return 1

    # Fetch analyst targets
    targets = None
    if not args.no_targets:
        print("\nFetching analyst targets...")
        targets = fetch_analyst_targets(yahoo_tickers)

    # Update YAML
    update_yaml_file(
        yaml_path, positions, prices, usd_to_eur, targets=targets, dry_run=args.dry_run
    )

    print("\n" + "=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
