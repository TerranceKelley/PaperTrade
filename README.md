# Options Paper Trading Bot

A production-quality options paper trading bot for Interactive Brokers, designed to run on a headless Ubuntu server with IB Gateway in Docker.

## Features

- **Put Credit Spread Strategy**: Automated scanning and execution of SPY/QQQ put credit spreads
- **Safety First**: Multiple kill switches and risk controls (trading disabled by default)
- **Comprehensive Logging**: SQLite database + rotating log files
- **Full Diagnostics**: `bot doctor` command verifies connectivity and market data
- **Risk Management**: Position sizing, daily loss limits, trade count limits

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11 or higher
- `uv` recommended (or use `pip`/`venv`)
- Interactive Brokers account (paper trading account recommended)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repo-url>
cd PaperTrade
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings (see Configuration section)
```

### 3. Start IB Gateway

```bash
docker compose up -d
```

### 4. Complete IB Gateway Login

**First-time setup:**

1. Check gateway logs: `docker compose logs -f ib-gateway`
2. Access the gateway web interface (if available) or use VNC
3. Complete login with your IB credentials
4. Complete 2FA if prompted
5. Ensure gateway shows "Connected" status

**Note**: The gateway container persists login state in the `ib-gateway-data` volume.

### 5. Verify Setup

```bash
# Using uv (recommended)
uv run bot doctor

# Or using Python directly
python -m options_bot.cli doctor
```

The `doctor` command will verify:
- ✓ IB Gateway connection
- ✓ Paper account detection
- ✓ Market data (SPY quote)
- ✓ Options chain access
- ✓ Greeks availability

### 6. Scan for Candidates

```bash
uv run bot scan
```

This prints candidate put credit spreads per ticker.

### 7. Run Trading Session

```bash
# Run for 120 minutes (default)
uv run bot run --session 120

# Or specify duration
uv run bot run --session 60
```

**Important**: Trading is **disabled by default** (`TRADING_DISABLED=true`). The bot will scan and manage positions but will NOT place orders until you explicitly enable trading.

## Configuration

Key environment variables in `.env`:

### Safety Settings (CRITICAL)

- `TRADING_DISABLED=true` - **Default: trading disabled**. Set to `false` to enable order placement.
- `ACCOUNT_SIZE=1000` - Account size for position sizing
- `RISK_PER_TRADE_PCT=0.02` - Max risk per trade (2% of account)
- `MAX_DAILY_LOSS_PCT=0.03` - Max daily loss kill switch (3% of account)
- `MAX_TRADES_PER_DAY=2` - Maximum trades per day

### Strategy Parameters

- `UNDERLYINGS=SPY,QQQ` - Comma-separated list of symbols
- `DTE_MIN=7` / `DTE_MAX=21` - Days to expiration range
- `DELTA_MIN=0.15` / `DELTA_MAX=0.25` - Delta range for short put
- `SPREAD_WIDTH=1.0` - Strike width between short and long puts (1.0 or 2.0)
- `REQUIRE_GREEKS=true` - Reject candidates without Greeks (default: true)
- `OTM_TARGET_PCT=0.04` - Fallback: select strike 4% OTM when Greeks unavailable

### Exit Management

- `TP_CAPTURE_PCT=0.50` - Take profit at 50% of credit captured
- `SL_MULTIPLE=2.0` - Stop loss at 2.0x initial credit
- `TIME_EXIT_DTE=3` - Close when DTE <= 3

### Execution

- `ENTRY_WINDOW_START=10:00` / `ENTRY_WINDOW_END=11:00` - Entry window (ET)
- `MANAGE_INTERVAL_SECONDS=300` - Management loop interval (5 minutes)
- `ENTRY_MAX_SLIPPAGE=0.05` - Max slippage tolerance
- `ENTRY_RETRY_SECONDS=60` - Retry timeout for orders

## CLI Commands

### `bot doctor`

Verifies connectivity, paper account, market data, and options chain. **Run this first** to ensure everything is configured correctly.

```bash
uv run bot doctor
```

### `bot scan`

Scans for candidate put credit spreads and prints them (no orders placed).

```bash
uv run bot scan
```

### `bot run --session <minutes>`

Runs a trading session:
- Scans for candidates during entry window
- Places orders (if `TRADING_DISABLED=false`)
- Manages open positions (TP/SL/time exits)
- Logs everything to database and files

```bash
uv run bot run --session 120
```

### `bot manage`

Manages existing positions only (no new entries).

```bash
uv run bot manage
```

### `bot report`

Prints today's trades, P/L, win rate, and open risk.

```bash
uv run bot report
```

### `bot export --csv <file>`

Exports trades/orders/fills to CSV.

```bash
uv run bot export --csv trades.csv
```

## Safety Features

1. **Trading Disabled by Default**: `TRADING_DISABLED=true` - bot will never place orders until explicitly enabled
2. **Max Daily Loss Kill Switch**: Stops opening new trades if daily loss exceeds `MAX_DAILY_LOSS_PCT`
3. **Max Risk Per Trade**: Position sizing enforces `RISK_PER_TRADE_PCT` limit
4. **Max Trades Per Day**: Prevents exceeding `MAX_TRADES_PER_DAY`
5. **Entry Window**: Only opens trades during configured hours
6. **Duplicate Prevention**: One open trade per ticker maximum

## Market Data Subscriptions

**Important**: The bot requires real-time or delayed market data for:
- Underlying stock quotes (bid/ask)
- Option quotes (bid/ask)
- Greeks (delta) from market data

### Delayed Data

If you see warnings about missing bid/ask or Greeks:
- Delayed data may be available (15-20 minute delay)
- The bot will still function but may miss opportunities
- Consider subscribing to real-time data for production use

### Greeks Availability

The bot requires Greeks (delta) for selection when `REQUIRE_GREEKS=true`:
- Greeks come from `ib_insync` ticker `modelGreeks` or `optionGreeks`
- If unavailable, set `REQUIRE_GREEKS=false` to use OTM fallback
- `bot doctor` explicitly reports Greeks availability

## Database

All trades, orders, fills, and market snapshots are stored in SQLite:
- Location: `./data/bot.db` (configurable via `DB_PATH`)
- Tables: `bot_runs`, `trades`, `orders`, `fills`, `market_snapshots`, `daily_stats`

## Logging

Logs are written to:
- Console: Structured output
- File: `./logs/bot.log` (rotating, max 10MB, 5 backups)

## Switching from Paper to Live

**WARNING**: The bot is designed for paper trading. To use with a live account:

1. **Change IB Gateway mode**: Set `TRADING_MODE=live` in docker-compose.yml (or use live TWS)
2. **Update account**: Set `IB_ACCOUNT_ID` in `.env` to your live account
3. **Verify**: `bot doctor` should show a non-DU account (with warning)
4. **Enable trading**: Set `TRADING_DISABLED=false` **only after thorough testing**
5. **Start small**: Use small `ACCOUNT_SIZE` and `RISK_PER_TRADE_PCT` initially

**The bot does NOT distinguish between paper and live accounts in its logic** - it relies on you to configure it correctly.

## Project Structure

```
PaperTrade/
├── README.md
├── .env.example
├── docker-compose.yml
├── pyproject.toml
├── src/
│   └── options_bot/
│       ├── config.py          # Configuration from env
│       ├── logging_setup.py    # Logging configuration
│       ├── cli.py              # CLI entrypoint
│       ├── time_utils.py       # ET timezone handling
│       ├── db/                 # Database models and repo
│       ├── ibkr/               # IBKR integration
│       ├── strategy/            # Strategy logic
│       └── services/            # High-level services
└── tests/                       # Unit tests
```

## Development

### Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### Run Tests

```bash
pytest tests/
```

## Troubleshooting

### IB Gateway Connection Failed

- Check gateway is running: `docker compose ps`
- Check gateway logs: `docker compose logs ib-gateway`
- Verify port matches `IB_PORT` in `.env`
- Ensure gateway is logged in (check logs for "Connected")

### No Market Data

- Verify market data subscriptions in IB account
- Check if market is open (bot works during market hours)
- Run `bot doctor` to diagnose

### Greeks Not Available

- Check market data subscription includes options data
- Try setting `REQUIRE_GREEKS=false` to use OTM fallback
- Verify with `bot doctor` - it reports Greeks availability

### Trading Disabled

- Check `TRADING_DISABLED` in `.env` (default: `true`)
- Bot will scan and manage but not place orders when disabled

## License

[Add your license here]

## Disclaimer

This software is for educational and paper trading purposes only. Trading options involves substantial risk. Use at your own risk. The authors are not responsible for any losses.
