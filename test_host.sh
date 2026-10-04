#!/usr/bin/env bash
# Host test runner for Meta Muse Gadget SDK & Bread S3 Port
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export DEVELOPER_DIR="/Library/Developer/CommandLineTools"

echo "=== Running Meta Muse Gadget SDK Host Tests (157 unit tests) ==="
python3 -m unittest discover -s tests -p 'test_*.py' -v
echo "=== All Tests Passed Successfully! ==="
