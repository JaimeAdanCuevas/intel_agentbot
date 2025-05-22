#!/bin/bash
# Runs stress-ng under Intel SDE and saves mix output

set -euo pipefail

# Default values
SDE_BIN="./bin/sde"
STRESS_BIN="./bin/stress-ng"
OUTPUT_DIR="tests/integration/data"
OUTPUT_FILE="${OUTPUT_DIR}/stress-ng-cpu-mix-out.txt"
DEFAULT_SDE_FLAGS="-cmt -mix -iform"
DEFAULT_STRESS_ARGS="--cpu 1 --timeout 10s --metrics-brief"

# Usage info
usage() {
    echo "Usage: $0 [sde_tarball_path] [sde_flags] [stress_args]"
    echo "Example: $0 ~/sde-external-<version>.tar.xz \"-cmt -mix -iform\" \"--cpu 2 --timeout 20s\""
    exit 1
}

# Extract SDE tarball if provided
extract_sde_if_needed() {
    local tarball="$1"
    if [[ -f "$tarball" ]]; then
        echo "[INFO] Extracting $tarball..."
        TMP_DIR=$(mktemp -d)
        tar -xf "$tarball" -C "$TMP_DIR"
        SDE_DIR=$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n1)
        echo "[INFO] Moving extracted SDE to ./bin..."
        mkdir -p ./bin
        mv "$SDE_DIR"/* ./bin/
    else
        echo "[ERROR] SDE tarball '$tarball' not found."
        exit 1
    fi
}

# Main logic
main() {
    local sde_tarball=""
    local sde_flags="${2:-$DEFAULT_SDE_FLAGS}"
    local stress_args="${3:-$DEFAULT_STRESS_ARGS}"

    # If user passed a tarball path, extract it
    if [[ $# -ge 1 && "$1" == *.tar.* ]]; then
        sde_tarball="$1"
        extract_sde_if_needed "$sde_tarball"
    fi

    # Check binaries
    if [[ ! -x "$SDE_BIN" ]]; then
        echo "[ERROR] SDE binary not found at $SDE_BIN"
        exit 1
    fi
    if [[ ! -x "$STRESS_BIN" ]]; then
        echo "[ERROR] stress-ng binary not found at $STRESS_BIN"
        exit 1
    fi

    # Run stress-ng under SDE
    echo "[INFO] Running stress-ng under SDE..."
    mkdir -p "$OUTPUT_DIR"
    set +e
    "$SDE_BIN" $sde_flags -- "$STRESS_BIN" $stress_args > sde-mix-out.txt 2>&1
    result=$?
    set -e

    if [[ $result -ne 0 ]]; then
        echo "[ERROR] stress-ng under SDE failed. See sde-mix-out.txt for details."
        exit $result
    fi

    mv sde-mix-out.txt "$OUTPUT_FILE"
    echo "[INFO] Output saved to $OUTPUT_FILE"
}

main "$@"
