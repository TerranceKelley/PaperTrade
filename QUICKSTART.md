# Quick Start Guide

## 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Key settings:
#   - TRADING_DISABLED=true (default - safe!)
#   - IB_HOST, IB_PORT (default: 127.0.0.1:4002)
#   - ACCOUNT_SIZE (your paper account size)
```

## 2. Start IB Gateway

```bash
docker compose up -d
```

## 3. Complete IB Gateway Login

1. Check logs: `docker compose logs -f ib-gateway`
2. Complete login in gateway interface
3. Complete 2FA if prompted
4. Verify "Connected" status

## 4. Verify Setup

```bash
uv run bot doctor
```

This should show:
- ✓ Connection OK
- ✓ Paper account detected
- ✓ Market data OK
- ✓ Options chain OK
- ✓ Greeks available (or warning if not)

## 5. Scan for Candidates

```bash
uv run bot scan
```

## 6. Run Trading Session

```bash
# Run for 120 minutes (default)
uv run bot run --session 120

# Or shorter test
uv run bot run --session 5
```

**Remember**: Trading is disabled by default. Set `TRADING_DISABLED=false` in `.env` to enable order placement (after thorough testing!).

## 7. View Reports

```bash
# Daily report
uv run bot report

# Export to CSV
uv run bot export --csv trades.csv
```

## Troubleshooting

- **Connection failed**: Check `docker compose ps` and logs
- **No market data**: Verify market is open and subscriptions active
- **Greeks unavailable**: Set `REQUIRE_GREEKS=false` to use OTM fallback
- **Trading disabled**: Check `TRADING_DISABLED` in `.env`
