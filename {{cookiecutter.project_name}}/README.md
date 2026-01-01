# {{ cookiecutter.project_name }}

{{ cookiecutter.short_description }}

## Features

- Best/worst case scenario projections based on analyst targets
- Monthly monitoring with P&L tracking
- Position open/closed status with realized P&L
- Results organized by month/year
- Automatic price updates from Yahoo Finance

## Installation

```bash
pip install hydra-core omegaconf pandas numpy matplotlib yfinance
```

## Usage

### Run Analysis

```bash
python {{ cookiecutter.script_name }}.py
```

### Update Prices

```bash
# Preview changes
python update_prices.py --dry-run

# Apply changes
python update_prices.py
```

## Configuration

Edit `conf/{{ cookiecutter.config_name }}.yaml` to add your positions:

```yaml
positions:
  - ticker: AAPL
    shares: 100
    buy_price_eur: 150.00
    current_price_eur: 175.00
    target_low_eur: 130.00
    target_high_eur: 200.00
    currency: USD
    is_open: true
    sell_price_eur: null
    notes: "Apple Inc"
```

### Closing a Position

When you sell a position, update the YAML:

```yaml
  - ticker: AAPL
    ...
    is_open: false
    sell_price_eur: 180.00  # Your actual sell price in EUR
```

## Output

Results are saved to `results/YYYY-MM/`:
- `open_positions.csv` - Current open positions
- `closed_positions.csv` - Closed positions with realized P&L
- `portfolio_scenarios.png` - Scenario visualization
- `position_analysis.png` - Individual position charts
- `pnl_waterfall.png` - P&L breakdown
- `portfolio_history.csv` - Historical tracking

## Author

{{ cookiecutter.full_name }} <{{ cookiecutter.email }}>
