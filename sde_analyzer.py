import re
import subprocess
import csv
import datetime
import os
import logging
import sys
import getopt
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - \
                    %(levelname)s - %(message)s')
logger = logging.getLogger()


def decode_instruction(instruction_hex):
    """Decode hexadecimal instruction using xed."""
    try:
        logger.debug(f"Decoding instruction: {instruction_hex}")
        result = subprocess.run(['./xed', '-64', '-d', instruction_hex],
                                capture_output=True, text=True, check=True)
        decoded = result.stdout.strip().split('\n')[-1]
        logger.debug(f"Decoded successfully: {decoded}")
        return decoded
    except subprocess.CalledProcessError as e:
        logger.error(f"xed decode failed for '{instruction_hex}': {e.stderr}")
        return "DECODE_ERROR"
    except Exception as e:
        logger.error(f"Decoding error: {str(e)}")
        return "DECODE_ERROR"


def extract_instruction_coverage(file_path):
    """Extract instruction coverage from SDE mix output."""
    logger.info(f"Processing instruction coverage from: {file_path}")
    counter = Counter()
    try:
        with open(file_path, 'r') as f:
            current_executions = 0
            block_re = re.compile(r'BLOCK:\s+\d+.*EXECUTIONS:\s+(\d+)')
            xdis_re = re.compile(r'^XDIS\s+\S+:\s+\S+\s+([0-9A-Fa-f]+)')

            for line in f:
                # Track current block executions
                if block_match := block_re.search(line):
                    current_executions = int(block_match.group(1))
                    logger.debug(f"New block with executions: \
                                 {current_executions}")
                    continue

                # Process XDIS lines
                if xdis_match := xdis_re.match(line):
                    hex_str = xdis_match.group(1).upper()
                    counter[hex_str] += current_executions
                    logger.debug(f"Found instruction: {hex_str} \
                                 x{current_executions}")

        logger.info(f"Found {len(counter)} unique instructions")
        return counter
    except Exception as e:
        logger.error(f"Instruction extraction failed: {str(e)}")
        return Counter()


def extract_branch_coverage(file_path):
    """Extract branch coverage from SDE mix output."""
    logger.info(f"Processing branch coverage from: {file_path}")
    counter = Counter()
    try:
        with open(file_path, 'r') as f:
            current_executions = 0
            block_re = re.compile(r'BLOCK:\s+\d+.*EXECUTIONS:\s+(\d+)')
            branch_re = re.compile(
                r'^XDIS\s+\S+:\s+\S+\s+([0-9A-Fa-f]+).\
                    *\s(j[a-z]+|call|ret|loop)\b',
                re.IGNORECASE
            )

            for line in f:
                if block_match := block_re.search(line):
                    current_executions = int(block_match.group(1))
                    continue

                if branch_match := branch_re.search(line):
                    hex_str = branch_match.group(1).upper()
                    counter[hex_str] += current_executions
                    logger.debug(f"Found branch: {hex_str} \
                                 x{current_executions}")

        logger.info(f"Found {len(counter)} branch instructions")
        return counter
    except Exception as e:
        logger.error(f"Branch extraction failed: {str(e)}")
        return Counter()


def generate_coverage_report(instructions, branches, report_file):
    """Generate CSV coverage report."""
    logger.info(f"Generating report: {report_file}")
    try:
        file_exists = os.path.exists(report_file)
        with open(report_file, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow([
                    'Timestamp', 'Type', 'Hex',
                    'Count', 'Decoded', 'Context'
                ])

            timestamp = datetime.datetime.now().isoformat()

            # Write instructions
            for hex_str, count in instructions.items():
                decoded = decode_instruction(hex_str)
                writer.writerow([
                    timestamp, 'INSTRUCTION', hex_str,
                    count, decoded, ''
                ])

            # Write branches
            for hex_str, count in branches.items():
                decoded = decode_instruction(hex_str)
                writer.writerow([
                    timestamp, 'BRANCH', hex_str,
                    count, decoded, ''
                ])

        logger.info(f"Report generated with \
                    {len(instructions) + len(branches)} entries")
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")


def main(spec_file, sde_output, report_file):
    """Main processing workflow."""
    if not os.path.exists(sde_output):
        logger.critical(f"SDE output file not found: {sde_output}")
        sys.exit(1)

    logger.info("Starting coverage analysis...")
    instructions = extract_instruction_coverage(sde_output)
    branches = extract_branch_coverage(sde_output)

    if not instructions and not branches:
        logger.warning("No coverage data found in input file")
        return

    # Print top findings to console
    if instructions:
        print("\nTop Instructions:")
        for hex_str, count in instructions.most_common(10):
            print(f"{hex_str:8} x{count:8} → {decode_instruction(hex_str)}")

    if branches:
        print("\nTop Branches:")
        for hex_str, count in branches.most_common(10):
            print(f"{hex_str:8} x{count:8} → {decode_instruction(hex_str)}")

    generate_coverage_report(instructions, branches, report_file)


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hs:o:r:",
            ["help", "spec=", "output=", "report="]
        )
    except getopt.GetoptError as err:
        logger.error(f"Invalid arguments: {err}")
        sys.exit(2)

    spec_file = ""
    sde_output = ""
    report_file = "coverage_report.csv"

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("Usage: python sde_analyzer.py -s <spec> -o <sde_output> \
                  [-r <report.csv>]")
            sys.exit()
        elif opt in ("-s", "--spec"):
            spec_file = arg
        elif opt in ("-o", "--output"):
            sde_output = arg
        elif opt in ("-r", "--report"):
            report_file = arg

    if not sde_output:
        logger.critical("Missing required SDE output file (-o)")
        sys.exit(2)

    main(spec_file, sde_output, report_file)
