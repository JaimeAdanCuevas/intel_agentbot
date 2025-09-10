#!/bin/bash
# Script to monitor unmatched IFORMs and invoke AI proposals

set -e

# Configuration
LOG_FILE="tests/integration/data/stress-ng-cpu-mix-out.log"
SPEC_FILE="config/instruction_specs/x86_64.yaml"
OUTPUT_SUGGESTIONS="tests/integration/data/iform_suggestions.txt"

# Run stress-ng to generate fresh logs
echo "Running stress-ng workflow to generate logs..."
make stress-ng > "${LOG_FILE}" 2>&1

# Extract unmatched IFORMs from logs
echo "Extracting unmatched IFORMs..."
UNMATCHED_IFORMS=$(grep "IFORM .* not found in spec" "${LOG_FILE}" | awk '{print $5}' | sort -u)

if [[ -z "${UNMATCHED_IFORMS}" ]]; then
    echo "No unmatched IFORMs found."
    exit 0
fi

# Generate basic suggestions for x86_64.yaml
echo "Generating basic suggestions for ${SPEC_FILE}..."
echo "# Basic IFORM suggestions for ${SPEC_FILE}" > "${OUTPUT_SUGGESTIONS}"
for IFORM in ${UNMATCHED_IFORMS}; do
    echo "${IFORM}:" >> "${OUTPUT_SUGGESTIONS}"
    echo "  iclass: ${IFORM}" >> "${OUTPUT_SUGGESTIONS}"
    echo "  extension: BASE" >> "${OUTPUT_SUGGESTIONS}"
    echo "  category: UNKNOWN" >> "${OUTPUT_SUGGESTIONS}"
    echo "  isa_set: UNKNOWN" >> "${OUTPUT_SUGGESTIONS}"
    echo "  attributes: []" >> "${OUTPUT_SUGGESTIONS}"
done

# Invoke AI for advanced suggestions
echo "Invoking AI for coverage optimization proposals..."
python3 src/core/coverage/propose_coverage_changes.py

echo "AI suggestions saved to tests/integration/data/coverage_suggestions.txt"
cat tests/integration/data/coverage_suggestions.txt