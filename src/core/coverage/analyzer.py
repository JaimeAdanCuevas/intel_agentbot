"""
Professional Instruction Coverage Analyzer - Final Working Version
"""

import re
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class CoverageAnalyzer:
    """Intel Architecture Instruction Coverage Analysis Engine"""
    
    def __init__(self, spec_path: str):
        self.spec: Dict[str, Any] = self._load_validated_spec(Path(spec_path))
        self.instruction_counts = defaultdict(int)
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
            'top_instructions': []
        }

    def analyze(self, sde_file: Path) -> Dict[str, Any]:
        """Full analysis pipeline with error handling"""
        try:
            self._process_sde_file(sde_file)
            self._calculate_coverage()
            return self.generate_report()
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}", exc_info=True)
            raise

    def _process_sde_file(self, sde_file: Path):
        """Process SDE output file line by line"""
        current_executions = 0
        
        with open(sde_file, 'r', encoding='utf-8') as f:
            for line_number, line in enumerate(f, 1):
                try:
                    # Debug line processing
                    print(f"Processing line: {line.strip()}")  # Debug
                    
                    if line.startswith('BLOCK'):
                        current_executions = self._parse_executions(line)
                    elif line.startswith('XDIS'):
                        self._process_instruction(line, current_executions)
                except Exception as e:
                    logger.warning(f"Error processing line {line_number}: {str(e)}")
                    continue

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
            
            if len(parts) < 2:
                raise ValueError("Insufficient instruction data")
            
            hex_str = parts[0].upper()
            iform = parts[-1].split(',')[0]  # Handle operand variations
            
            self.instruction_counts[hex_str] += count
            
            if iform in self.spec:
                self._track_coverage(iform)

        except (ValueError, IndexError) as e:
            logger.warning(f"Invalid instruction line: {line.strip()}")
        except KeyError as e:
            logger.warning(f"Unknown instruction format: {iform}")

    def _track_coverage(self, iform: str):
        """Update coverage statistics safely"""
        try:
            spec_entry = self.spec[iform]
            self.coverage_stats['by_category'][spec_entry['category']] += 1
            self.coverage_stats['by_isa_set'][spec_entry['isa_set']] += 1
            self.coverage_stats['covered'] += 1
        except KeyError as e:
            logger.error(f"Missing spec entry for {iform}: {str(e)}")

    def _calculate_coverage(self):
        """Calculate final coverage metrics"""
        try:
            total = self.coverage_stats['total_instructions']
            covered = self.coverage_stats['covered']
            
            self.coverage_stats['coverage_percent'] = (
                (covered / total * 100) if total > 0 else 0
            )
            self.coverage_stats['uncovered'] = [
                iform for iform in self.spec
                if self.instruction_counts.get(iform, 0) == 0
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
            top_category = (
                max(self.coverage_stats['by_category'].items(), 
                    key=lambda x: x[1])[0]
                if self.coverage_stats['by_category']
                else 'N/A'
            )
        except ValueError:
            top_category = 'N/A'

        return {
            'summary': {
                'total_instructions': self.coverage_stats['total_instructions'],
                'covered_instructions': self.coverage_stats['covered'],
                'coverage_percent': round(self.coverage_stats['coverage_percent'], 2),
                'top_category': top_category,
                'categories': dict(self.coverage_stats['by_category']),
                'isa_sets': dict(self.coverage_stats['by_isa_set'])
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
            iform for iform, count in self.instruction_counts.items()
            if count > 0
        )
        
        return {
            'missing_spec_entries': list(observed_iforms - spec_iforms),
            'unused_spec_entries': list(spec_iforms - observed_iforms),
            'coverage_match_percent': (
                len(observed_iforms & spec_iforms) / 
                len(spec_iforms) * 100
                if spec_iforms
                else 0
            )
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

if __name__ == '__main__':
    """Command-line execution example"""
    try:
        analyzer = CoverageAnalyzer('config/instruction_specs/x86_64.yaml')
        report = analyzer.analyze(Path('tests/integration/data/cg.A.AVX2-mix-out.txt'))
        
        print("\n=== Coverage Analysis Report ===")
        print(f"Total Instructions: {report['summary']['total_instructions']}")
        print(f"Coverage Percentage: {report['summary']['coverage_percent']}%")
        print(f"Top Category: {report['summary']['top_category']}")
        print(f"Uncovered Instructions: {len(report['details']['uncovered_instructions'])}")
        
    except Exception as e:
        logger.critical(f"Critical failure: {str(e)}")
        exit(1)
