"""
Professional Instruction Coverage Analyzer - Final Working Version
"""

import re
import logging
import yaml
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import csv

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

class CoverageAnalyzer:
    """Intel Architecture Instruction Coverage Analysis Engine"""
    
    def __init__(self, spec_path: str, xed_path: str = "./bin/xed"):
        self.spec: Dict[str, Any] = self._load_validated_spec(Path(spec_path))
        self.xed_path = xed_path
        if not Path(xed_path).is_file():
            logger.error(f"xed binary not found at {xed_path}")
            raise FileNotFoundError(f"xed binary not found at {xed_path}")
        self.instruction_counts = defaultdict(int)
        self.iform_counts = defaultdict(int)
        self.unmatched_iforms = set()
        self.coverage_stats = self._init_coverage_stats()
        logger.info(f"Analyzer initialized with {len(self.spec)} instructions")

    def _init_coverage_stats(self) -> Dict[str, Any]:
        """Initialize coverage statistics with safe defaults"""
        return {
            'total_instructions': len(self.spec),
            'covered': 0,
            'coverage_percent': 0.0,
            'by_category': defaultdict(int),
            'by_isa_set': defaultdict(int),
            'uncovered': [],
            'top_instructions': [],
            'parsed_lines': 0,
            'matched_instructions': 0
        }

    def analyze(self, sde_file: Path) -> Dict[str, Any]:
        """Full analysis pipeline with error handling"""
        try:
            self._process_sde_file(sde_file)
            self._calculate_coverage()
            logger.info(f"Processed {self.coverage_stats['parsed_lines']} lines, matched {self.coverage_stats['matched_instructions']} instructions")
            return self.generate_report()
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}", exc_info=True)
            raise

    def _process_sde_file(self, sde_file: Path):
        """Process SDE output file including dynamic stats"""
        current_executions = 0
        in_dynamic_stats = False
        in_count_section = False
        
        with open(sde_file, 'r', encoding='utf-8') as f:
            for line_number, line in enumerate(f, 1):
                try:
                    line = line.strip()
                    self.coverage_stats['parsed_lines'] += 1

                    if not line or line.startswith('#'):
                        if "EMIT_DYNAMIC_STATS" in line:
                            in_dynamic_stats = True
                            in_count_section = False
                        continue

                    if in_dynamic_stats:
                        if line.startswith('TID') or line.startswith('0'):
                            in_count_section = True
                            continue
                            
                        if in_count_section and '*' not in line:
                            parts = line.rsplit(maxsplit=1)
                            if len(parts) == 2:
                                iform, count_str = parts
                                try:
                                    count = int(count_str)
                                    self._process_dynamic_stat(iform, count)
                                except ValueError:
                                    logger.warning(f"Invalid count in dynamic stats: {line}")
                        continue

                    if line.startswith('BLOCK'):
                        current_executions = self._parse_executions(line)
                    elif line.startswith('XDIS'):
                        self._process_instruction(line, current_executions)

                except Exception as e:
                    logger.warning(f"Error processing line {line_number}: {str(e)}")
                    continue

    def _process_dynamic_stat(self, iform: str, count: int):
        """Process dynamic statistics entry"""
        self.iform_counts[iform] += count
        if iform in self.spec:
            self._track_coverage(iform)
        else:
            self.unmatched_iforms.add(iform)
            logger.debug(f"IFORM {iform} not found in spec")

    def _parse_executions(self, line: str) -> int:
        """Robust execution count extraction"""
        try:
            match = re.search(r'EXECUTIONS:\s*(\d+)', line)
            return int(match.group(1)) if match else 0
        except (AttributeError, ValueError) as e:
            logger.warning(f"Execution count error: {str(e)}")
            return 0

    def _process_instruction(self, line: str, count: int):
        """Process XDIS instruction line"""
        try:
            _, remainder = line.split(':', 1)
            parts = remainder.strip().split()
            
            if len(parts) < 3:
                raise ValueError("Insufficient instruction data")
            
            hex_str = parts[1].upper()
            mnemonic = parts[2].split()[0].upper()
            
            iform = self._decode_instruction(hex_str)
            
            logger.debug(f"Processing instruction: hex={hex_str}, mnemonic={mnemonic}, iform={iform}")
            self.instruction_counts[hex_str] += count
            
            if iform:
                self.iform_counts[iform] += count
                if iform in self.spec:
                    self._track_coverage(iform)
                else:
                    self.unmatched_iforms.add(iform)
                    logger.debug(f"IFORM {iform} not found in spec")

        except (ValueError, IndexError) as e:
            logger.warning(f"Invalid instruction line: {line.strip()}")
        except KeyError as e:
            logger.warning(f"Unknown instruction format: {iform}")

    def _decode_instruction(self, hex_str: str) -> str:
        """Decode hex instruction using xed to get IFORM"""
        try:
            result = subprocess.run(
                [self.xed_path, '-64', '-d', hex_str],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout.strip().split('\n')
            for line in output:
                if line.startswith('IFORM:'):
                    return line.split(':')[1].strip().split()[0]
            return "UNKNOWN"
        except subprocess.CalledProcessError as e:
            logger.error(f"xed decode failed for '{hex_str}': {e.stderr}")
            return "UNKNOWN"
        except Exception as e:
            logger.error(f"Decoding error: {str(e)}")
            return "UNKNOWN"

    def _track_coverage(self, iform: str):
        """Update coverage statistics safely"""
        try:
            spec_entry = self.spec[iform]
            self.coverage_stats['by_category'][spec_entry['category']] += 1
            self.coverage_stats['by_isa_set'][spec_entry['isa_set']] += 1
            self.coverage_stats['matched_instructions'] += 1
        except KeyError as e:
            logger.error(f"Missing spec entry for {iform}: {str(e)}")

    def _calculate_coverage(self):
        """Calculate final coverage metrics"""
        try:
            total = self.coverage_stats['total_instructions']
            covered = len({iform for iform in self.spec if self.iform_counts.get(iform, 0) > 0})
            
            self.coverage_stats['coverage_percent'] = round(
                (covered / total * 100) if total > 0 else 0, 2
            )
            self.coverage_stats['covered'] = covered
            self.coverage_stats['uncovered'] = [
                iform for iform in self.spec
                if self.iform_counts.get(iform, 0) == 0
            ]
            self.coverage_stats['top_instructions'] = sorted(
                self.instruction_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
        except ZeroDivisionError:
            logger.error("Empty instruction spec - cannot calculate coverage")
            self.coverage_stats['coverage_percent'] = 0.0

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive coverage report"""
        try:
            top_category = max(
                self.coverage_stats['by_category'].items(),
                key=lambda x: x[1]
            )[0] if self.coverage_stats['by_category'] else 'N/A'
        except ValueError:
            top_category = 'N/A'

        return {
            'summary': {
                'total_instructions': self.coverage_stats['total_instructions'],
                'covered_instructions': self.coverage_stats['covered'],
                'coverage_percent': self.coverage_stats['coverage_percent'],
                'top_category': top_category,
                'categories': dict(self.coverage_stats['by_category']),
                'isa_sets': dict(self.coverage_stats['by_isa_set']),
                'parsed_lines': self.coverage_stats['parsed_lines'],
                'matched_instructions': self.coverage_stats['matched_instructions']
            },
            'details': {
                'uncovered_instructions': self.coverage_stats['uncovered'],
                'top_used_instructions': [
                    {'hex': k, 'count': v} 
                    for k, v in self.coverage_stats['top_instructions']
                ],
                'spec_validation': self._validate_spec_coverage()
            }
        }

    def _validate_spec_coverage(self) -> Dict[str, Any]:
        """Validate spec against observed instructions"""
        spec_iforms = set(self.spec.keys())
        observed_iforms = set(
            iform for iform, count in self.iform_counts.items()
            if count > 0
        )
        
        return {
            'missing_spec_entries': list(observed_iforms - spec_iforms),
            'unused_spec_entries': list(spec_iforms - observed_iforms),
            'coverage_match_percent': round(
                len(observed_iforms & spec_iforms) / len(spec_iforms) * 100,
                2
            ) if spec_iforms else 0
        }

    def _load_validated_spec(self, path: Path) -> Dict[str, Any]:
        """Load and validate instruction spec file"""
        if not path.exists():
            logger.error(f"Spec file missing: {path}")
            raise FileNotFoundError(f"Spec file not found: {path}")

        try:
            with open(path) as f:
                spec = yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in spec: {str(e)}")
            raise

        if not isinstance(spec, dict):
            logger.error("Invalid spec format: Root must be a dictionary")
            raise ValueError("Spec file must contain a dictionary")

        required_fields = {'iclass', 'category', 'isa_set', 'attributes'}
        validation_errors = False
        
        for iform, data in spec.items():
            missing = required_fields - data.keys()
            if missing:
                logger.error(f"Missing fields in {iform}: {missing}")
                validation_errors = True
                
        if validation_errors:
            raise ValueError("Invalid spec entries detected")

        return spec
    
    def export_csv_report(self, output_path: str):
        """Export coverage report to CSV format"""
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write summary section
                writer.writerow(["Metric", "Value"])
                writer.writerow(["Total Instructions", self.coverage_stats['total_instructions']])
                writer.writerow(["Covered Instructions (Unique)", self.coverage_stats['covered']])
                writer.writerow(["Coverage Percentage", f"{self.coverage_stats['coverage_percent']}%"])
                writer.writerow(["Top Category", self.generate_report()['summary']['top_category']])
                writer.writerow(["Parsed Lines", self.coverage_stats['parsed_lines']])
                writer.writerow(["Matched Executions", self.coverage_stats['matched_instructions']])
                writer.writerow([])  # Empty row separator
                
                # Write detailed instruction data
                writer.writerow([
                    "iclass", "extension", "category", "iform",
                    "isa_set", "attributes", "count", "covered"
                ])
                
                for iform in sorted(self.spec.keys()):
                    spec_entry = self.spec[iform]
                    count = self.iform_counts.get(iform, 0)
                    
                    writer.writerow([
                        spec_entry['iclass'],
                        spec_entry['extension'],
                        spec_entry['category'],
                        iform,
                        spec_entry['isa_set'],
                        ';'.join(spec_entry['attributes']),
                        count,
                        "Yes" if count > 0 else "No"
                    ])
                    
            logger.info(f"CSV report saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate CSV report: {str(e)}")
            raise

if __name__ == '__main__':
    """Command-line execution with argument parsing"""
    parser = argparse.ArgumentParser(description='Instruction Coverage Analyzer')
    parser.add_argument('--spec-file', default='config/instruction_specs/x86_64.yaml',
                        help='Path to instruction spec YAML file')
    parser.add_argument('--sde-file', required=True,
                        help='Path to SDE mix output file')
    parser.add_argument('--xed-path', default='./bin/xed',
                        help='Path to xed binary')
    parser.add_argument('--output-csv', default='tests/integration/data/coverage_report.csv',
                        help='Output path for CSV report')
    
    
    args = parser.parse_args()
    
    try:
        analyzer = CoverageAnalyzer(args.spec_file, args.xed_path)
        report = analyzer.analyze(Path(args.sde_file))
        analyzer.export_csv_report(args.output_csv)
        
        print("\n=== Coverage Analysis Report ===")
        print(f"Total Instructions: {report['summary']['total_instructions']}")
        print(f"Unique Covered: {report['summary']['covered_instructions']}")
        print(f"Coverage Percentage: {report['summary']['coverage_percent']}%")
        print(f"Top Category: {report['summary']['top_category']}")
        print(f"Total Executions: {report['summary']['matched_instructions']}")
        print(f"Uncovered Instructions: {len(report['details']['uncovered_instructions'])}")
        print(f"CSV Report: {args.output_csv}")
        
    except Exception as e:
        logger.critical(f"Critical failure: {str(e)}")
        exit(1)