# Pre-Production Testing Checklist

Use this checklist before enabling live trading (`TRADING_DISABLED=false`).

## Quick Test Commands

```bash
# 1. Run all unit tests
pytest tests/ -v -m "not integration"

# 2. Run safety tests
pytest tests/test_safety.py -v

# 3. Verify configuration
uv run bot doctor

# 4. Test scanning (no orders)
uv run bot scan

# 5. Test short session (trading disabled)
uv run bot run --session 5
```

## Pre-Enable Checklist

### Phase 1: Code Quality
- [ ] All unit tests pass: `pytest tests/ -v -m "not integration"`
- [ ] No linter errors
- [ ] Code review completed
- [ ] All safety features implemented

### Phase 2: Configuration
- [ ] `.env` file configured correctly
- [ ] `TRADING_DISABLED=true` (keep disabled for now)
- [ ] Account size set appropriately
- [ ] Risk limits set conservatively (1-2% per trade)
- [ ] Max trades per day set (start with 1-2)
- [ ] Entry window configured

### Phase 3: IB Gateway
- [ ] IB Gateway running: `docker compose ps`
- [ ] Gateway connected: Check logs
- [ ] Paper account detected: `bot doctor`
- [ ] Market data working: `bot doctor`
- [ ] Options chain accessible: `bot doctor`
- [ ] Greeks available (or fallback works): `bot doctor`

### Phase 4: Functionality (Trading Disabled)
- [ ] Scan works: `bot scan` returns candidates
- [ ] Short session runs: `bot run --session 5` (no errors)
- [ ] Management loop works: `bot manage` (Ctrl+C after 5 min)
- [ ] Logs written: Check `logs/bot.log`
- [ ] Database created: Check `data/bot.db` exists
- [ ] Reports work: `bot report`
- [ ] Export works: `bot export --csv test.csv`

### Phase 5: Safety Features (Trading Disabled)
- [ ] No orders placed when `TRADING_DISABLED=true`
- [ ] Daily loss check works (test with manual DB edit)
- [ ] Max trades check works (test with limit=1)
- [ ] Entry window enforced (test outside window)
- [ ] Duplicate prevention works (test with existing trade)

### Phase 6: Paper Trading (Week 1)
- [ ] Run bot for 1 week with `TRADING_DISABLED=true`
- [ ] Monitor logs daily
- [ ] Verify no orders placed
- [ ] Check database growth
- [ ] Review scan results

### Phase 7: Paper Trading (Week 2-3)
- [ ] Set `TRADING_DISABLED=false` (small account)
- [ ] Set `ACCOUNT_SIZE=1000` (or smaller)
- [ ] Set `RISK_PER_TRADE_PCT=0.01` (1%)
- [ ] Set `MAX_TRADES_PER_DAY=1`
- [ ] Run bot for 1-2 weeks
- [ ] Monitor all trades in IB portal
- [ ] Verify P/L matches expectations
- [ ] Check exit logic (TP/SL/time)

### Phase 8: Paper Trading (Week 4+)
- [ ] Gradually increase account size
- [ ] Gradually increase risk per trade (max 2%)
- [ ] Test with multiple trades per day
- [ ] Test edge cases (connection loss, etc.)
- [ ] Monitor performance
- [ ] Review all trades manually

### Phase 9: Final Verification
- [ ] All safety features verified in paper trading
- [ ] No errors or crashes for 2+ weeks
- [ ] P/L calculations correct
- [ ] Order execution quality acceptable
- [ ] Exit logic working (TP/SL/time)
- [ ] Database integrity verified
- [ ] Log rotation working
- [ ] Performance acceptable

### Phase 10: Pre-Live Preparation
- [ ] Backup strategy documented
- [ ] Monitoring setup
- [ ] Alert system configured
- [ ] Rollback plan ready
- [ ] Support contacts ready
- [ ] Small initial account size
- [ ] Conservative risk settings

## Red Flags - DO NOT ENABLE

If you see any of these, **STOP** and fix:

- ✗ Orders placed when `TRADING_DISABLED=true`
- ✗ Daily loss exceeded but trades still open
- ✗ Max trades per day exceeded
- ✗ Duplicate trades on same symbol
- ✗ Trades outside entry window
- ✗ Position sizing exceeds risk limit
- ✗ Crashes or unhandled exceptions
- ✗ Incorrect P/L calculations
- ✗ Database corruption
- ✗ Orders not matching strategy

## Recommended Timeline

- **Week 1-2**: Code testing + Paper trading (disabled)
- **Week 3-4**: Paper trading (enabled, small size)
- **Week 5-6**: Paper trading (gradual increase)
- **Week 7+**: Extended paper trading validation
- **Only then**: Consider live trading (with small size)

## Quick Verification Commands

```bash
# Check trading is disabled
grep TRADING_DISABLED .env

# Verify no orders in database (when disabled)
sqlite3 data/bot.db "SELECT COUNT(*) FROM orders WHERE status='submitted';"

# Check recent logs
tail -50 logs/bot.log

# Verify paper account
uv run bot doctor | grep "Paper Account"

# Check daily stats
sqlite3 data/bot.db "SELECT * FROM daily_stats ORDER BY day DESC LIMIT 1;"
```
