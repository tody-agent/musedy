#!/usr/bin/env bash
# Build script for Meta Muse UI Board (Bread S3 OLED + INMP441 + MAX98357A + Pet Touch)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== [1/3] Checking ESP-IDF Environment ==="
if ! command -v idf.py >/dev/null 2>&1; then
    for d in "$HOME/.espressif/esp-idf-v6.0.1" "${IDF_PATH:-}" "$HOME/esp/esp-idf-v6.0.1" "$HOME/esp/esp-idf-v6" "$HOME/esp/esp-idf" "/Volumes/Builder/esp/esp-idf"; do
        if [ -n "$d" ] && [ -f "$d/export.sh" ]; then
            echo "Activating ESP-IDF from: $d"
            # shellcheck disable=SC1090
            . "$d/export.sh" >/dev/null 2>&1
            break
        fi
    done
fi

command -v idf.py >/dev/null 2>&1 || {
    echo "ERROR: idf.py not found. Please activate ESP-IDF v6.0.1 or set IDF_PATH." >&2
    exit 1
}

B="build-muse-bread-s3"
DEFAULTS="sdkconfig.defaults;devices/sdkconfig.muse;devices/sdkconfig.muse-bread-s3"
ARGS="-B $B -DIDF_TARGET=esp32s3 -DSDKCONFIG=$B/sdkconfig -DSDKCONFIG_DEFAULTS=$DEFAULTS"

echo "=== [2/3] Configuring Bread S3 UI Firmware ==="
idf.py $ARGS reconfigure

echo "=== [3/3] Building Bread S3 UI Firmware ==="
idf.py $ARGS build

echo "=== Build Complete! ==="
echo "Firmware binary: $B/muse-gadget.bin"
echo "Flash command: idf.py $ARGS -p /dev/ttyACM0 flash monitor"
