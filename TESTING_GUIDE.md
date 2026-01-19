# Testing Guide - Pre-Production Checklist

This guide outlines comprehensive testing procedures to validate the bot before enabling live trading.

## Testing Phases

### Phase 1: Unit Tests (No IB Connection Required)

Run all unit tests to verify core logic:

```bash
pytest tests/ -v
```

**What to verify:**
- ✓ All tests pass
- ✓ Position sizing calculations correct
- ✓ TP/SL math correct
- ✓ Risk limits enforced

### Phase 2: Safety Feature Verification

**Test 1: Trading Disabled by Default**
```bash
# Ensure TRADING_DISABLED=true in .env
uv run bot run --session 5
# Verify: Check logs - should see "Trading is disabled" messages
# Verify: No orders should be placed
```

**Test 2: Daily Loss Kill Switch**
- Manually set daily loss in database to exceed limit
- Attempt to open trade
- Verify: Trade should be rejected with "Daily loss limit exceeded"

**Test 3: Max Trades Per Day**
- Set MAX_TRADES_PER_DAY=1
- Run bot, let it open one trade
- Verify: Second trade attempt should be rejected

**Test 4: Max Risk Per Trade**
- Set RISK_PER_TRADE_PCT=0.01 (1%)
- Verify: Position sizing respects the limit

**Test 5: Entry Window Enforcement**
- Set ENTRY_WINDOW_START=23:00 (outside market hours)
- Run bot
- Verify: No trades opened outside window

### Phase 3: IB Gateway Integration Tests

**Test 1: Connection & Diagnostics**
```bash
uv run bot doctor
```
**Verify:**
- ✓ Connection successful
- ✓ Paper account detected (DU prefix)
- ✓ Market data available
- ✓ Options chain accessible
- ✓ Greeks available (or fallback works)

**Test 2: Market Data Retrieval**
```bash
uv run bot scan
```
**Verify:**
- ✓ Can retrieve option chains
- ✓ Can get bid/ask for options
- ✓ Greeks retrieved (if available)
- ✓ Candidates found and ranked

**Test 3: Order Creation (Dry Run)**
- Keep TRADING_DISABLED=true
- Run `bot scan` to see candidates
- Manually verify combo order structure would be correct
- Check logs for order creation attempts (should be blocked)

### Phase 4: Paper Trading Validation

**Prerequisites:**
- IB Gateway running and connected
- Paper account funded
- Market hours (or use extended hours for testing)

**Test 1: Scan Only (No Orders)**
```bash
# TRADING_DISABLED=true
uv run bot scan
```
**Verify:**
- ✓ Candidates found
- ✓ All filters applied correctly
- ✓ Rankings make sense

**Test 2: Short Session (Trading Disabled)**
```bash
# TRADING_DISABLED=true
uv run bot run --session 5
```
**Verify:**
- ✓ Bot runs without errors
- ✓ Scans during entry window
- ✓ No orders placed
- ✓ Logs written correctly
- ✓ Database records created

**Test 3: Management Loop (No Open Trades)**
```bash
uv run bot manage
# Let it run for 5 minutes, then Ctrl+C
```
**Verify:**
- ✓ Management loop runs
- ✓ No errors with no open trades
- ✓ Logs show management attempts

**Test 4: Single Trade Test (Paper Account)**
```bash
# Set TRADING_DISABLED=false
# Set MAX_TRADES_PER_DAY=1
# Set ACCOUNT_SIZE to small amount (e.g., 1000)
# Set RISK_PER_TRADE_PCT=0.01 (1% = $10 max risk)
uv run bot run --session 30
```
**Verify:**
- ✓ Trade opened successfully
- ✓ Order placed in IB
- ✓ Trade recorded in database
- ✓ Daily stats updated
- ✓ Position tracked correctly

**Test 5: Trade Management (Paper Account)**
- Open a trade manually in IB (or let bot open one)
- Wait for management loop
- Verify: Bot detects open position
- Verify: TP/SL logic works
- Verify: Time exit works when DTE <= 3

**Test 6: Multiple Trades (Paper Account)**
```bash
# Set MAX_TRADES_PER_DAY=2
# Set small ACCOUNT_SIZE and RISK_PER_TRADE_PCT
uv run bot run --session 60
```
**Verify:**
- ✓ First trade opens
- ✓ Second trade opens (if within limits)
- ✓ Third trade blocked (max trades reached)
- ✓ No duplicate trades on same symbol

### Phase 5: Edge Cases & Error Handling

**Test 1: Connection Loss**
- Start bot
- Stop IB Gateway mid-session
- Verify: Bot handles disconnection gracefully
- Verify: Logs show reconnection attempts

**Test 2: Missing Market Data**
- Test during market closed hours
- Verify: Bot handles missing data gracefully
- Verify: No crashes on missing bid/ask

**Test 3: Invalid Configuration**
- Set invalid values (negative numbers, etc.)
- Verify: Bot validates config or fails safely

**Test 4: Database Issues**
- Make database read-only
- Verify: Bot handles DB errors gracefully

**Test 5: Greeks Unavailable**
- Set REQUIRE_GREEKS=false
- Verify: OTM fallback works
- Verify: Logs show fallback usage

### Phase 6: End-to-End Scenarios

**Scenario 1: Full Trading Day (Paper)**
```bash
# Full day simulation
# TRADING_DISABLED=false (after all other tests pass)
# Small account size and risk
uv run bot run --session 480  # 8 hours
```
**Monitor:**
- All trades opened/closed correctly
- Daily limits respected
- No errors or crashes
- Database integrity
- Log file rotation

**Scenario 2: Weekend/After Hours**
- Run bot outside market hours
- Verify: No errors, graceful handling

**Scenario 3: Multiple Days**
- Run bot for several days
- Verify: Daily stats reset correctly
- Verify: Trade limits reset daily

### Phase 7: Performance & Monitoring

**Test 1: Logging**
- Run bot for 1 hour
- Verify: Logs written correctly
- Verify: Log rotation works
- Verify: No log file bloat

**Test 2: Database Growth**
- Run bot for several days
- Verify: Database size reasonable
- Verify: Query performance acceptable

**Test 3: Resource Usage**
- Monitor CPU/memory during run
- Verify: No memory leaks
- Verify: Reasonable resource usage

## Pre-Enable Checklist

Before setting `TRADING_DISABLED=false`:

- [ ] All unit tests pass
- [ ] `bot doctor` shows all checks passing
- [ ] Paper trading tested for at least 1 week
- [ ] All safety features verified
- [ ] Edge cases tested
- [ ] Logging and monitoring working
- [ ] Database backups configured
- [ ] Small account size configured
- [ ] Low risk per trade (1-2%)
- [ ] Max trades per day set conservatively
- [ ] Entry window verified
- [ ] Exit logic verified (TP/SL/time)
- [ ] Manual review of all trades in paper account
- [ ] Performance acceptable
- [ ] Error handling verified

## Recommended Testing Timeline

1. **Week 1**: Unit tests + Safety verification
2. **Week 2**: IB Gateway integration + Scan tests
3. **Week 3**: Paper trading with TRADING_DISABLED=true
4. **Week 4**: Paper trading with TRADING_DISABLED=false (small size)
5. **Week 5+**: Extended paper trading, monitor and refine

## Red Flags - Stop and Fix

If you see any of these, **DO NOT** enable live trading:

- ✗ Orders placed when TRADING_DISABLED=true
- ✗ Daily loss limit exceeded but trades still open
- ✗ Max trades per day exceeded
- ✗ Duplicate trades on same symbol
- ✗ Trades outside entry window
- ✗ Position sizing exceeds risk limit
- ✗ Database corruption
- ✗ Crashes or unhandled exceptions
- ✗ Incorrect P/L calculations
- ✗ Orders not matching intended strategy

## Manual Verification Steps

After automated tests, manually verify:

1. **Review Database**
   ```bash
   sqlite3 data/bot.db "SELECT * FROM trades ORDER BY ts_open DESC LIMIT 10;"
   ```

2. **Review Logs**
   ```bash
   tail -100 logs/bot.log
   ```

3. **Review IB Account**
   - Log into IB web portal
   - Verify all trades match database
   - Verify P/L matches

4. **Review Reports**
   ```bash
   uv run bot report
   uv run bot export --csv review.csv
   ```

## Continuous Monitoring

Even after enabling, monitor:

- Daily P/L vs expectations
- Trade execution quality
- Error rates
- System resource usage
- Database growth
- Log file health
