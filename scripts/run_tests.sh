#!/bin/bash
# Test runner script

set -e

echo "=== Running Unit Tests ==="
pytest tests/ -v -m "not integration"

echo ""
echo "=== Running Safety Tests ==="
pytest tests/test_safety.py -v

echo ""
echo "=== Integration Tests (require IB Gateway) ==="
echo "Skipping integration tests. Run manually with:"
echo "  pytest tests/test_integration.py -v -m integration"
echo ""
echo "Or run all tests including integration:"
echo "  pytest tests/ -v"
