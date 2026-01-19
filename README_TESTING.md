# Testing Summary

This document provides a quick overview of testing resources. See detailed guides for more information.

## Quick Start Testing

1. **Run Unit Tests** (no IB connection needed):
   ```bash
   pytest tests/ -v -m "not integration"
   ```

2. **Run Safety Tests**:
   ```bash
   pytest tests/test_safety.py -v
   ```

3. **Verify Setup**:
   ```bash
   uv run bot doctor
   ```

4. **Test Scanning** (no orders):
   ```bash
   uv run bot scan
   ```

5. **Test Short Session** (trading disabled):
   ```bash
   uv run bot run --session 5
   ```

## Test Files

- `tests/test_risk.py` - Risk management calculations
- `tests/test_selector.py` - Option selection logic
- `tests/test_manager_math.py` - TP/SL calculations
- `tests/test_safety.py` - Safety features and kill switches
- `tests/test_integration.py` - Integration tests (require IB Gateway)
- `tests/conftest.py` - Test configuration and fixtures

## Testing Documents

- **TESTING_GUIDE.md** - Comprehensive testing procedures
- **TESTING_CHECKLIST.md** - Quick checklist before enabling trading

## Testing Phases

1. **Unit Tests** - Core logic (no IB connection)
2. **Safety Verification** - Kill switches and limits
3. **IB Integration** - Connection and market data
4. **Paper Trading (Disabled)** - 1-2 weeks
5. **Paper Trading (Enabled)** - 2-4 weeks minimum
6. **Extended Validation** - Ongoing monitoring

## Critical Tests Before Enabling

- [ ] All unit tests pass
- [ ] `bot doctor` shows all checks passing
- [ ] No orders placed when `TRADING_DISABLED=true`
- [ ] Paper trading validated for 2+ weeks
- [ ] All safety features verified
- [ ] Small account size configured
- [ ] Conservative risk settings (1-2%)

## Running Tests

```bash
# All unit tests (excluding integration)
pytest tests/ -v -m "not integration"

# Only safety tests
pytest tests/test_safety.py -v

# Only integration tests (requires IB Gateway)
pytest tests/test_integration.py -v -m integration

# All tests including integration
pytest tests/ -v

# With coverage (if pytest-cov installed)
pytest tests/ --cov=src/options_bot --cov-report=html
```

## Integration Tests

Integration tests require:
- IB Gateway running
- Paper account configured
- Market data subscriptions

Mark tests with `@pytest.mark.integration` to run separately:
```bash
pytest tests/ -v -m integration
```

## Safety Test Scenarios

See `TESTING_GUIDE.md` for detailed scenarios:
- Trading disabled enforcement
- Daily loss kill switch
- Max trades per day
- Entry window enforcement
- Position sizing limits
- Duplicate prevention

## Paper Trading Validation

**Minimum 2-4 weeks** of paper trading before considering live:
- Week 1: Trading disabled, verify scanning
- Week 2-3: Trading enabled, small size
- Week 4+: Extended validation, gradual increase

## Red Flags

Stop and fix if you see:
- Orders when trading disabled
- Limits exceeded
- Crashes or errors
- Incorrect calculations
- Database issues

See `TESTING_CHECKLIST.md` for complete list.
