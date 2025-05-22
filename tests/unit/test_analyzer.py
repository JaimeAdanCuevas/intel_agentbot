import pytest
from src.core.coverage.analyzer import CoverageAnalyzer
from pathlib import Path

def test_analyzer_init():
    analyzer = CoverageAnalyzer('config/instruction_specs/x86_64.yaml')
    assert analyzer is not None
    assert len(analyzer.spec) > 0

def test_analyzer_stress_ng():
    analyzer = CoverageAnalyzer('config/instruction_specs/x86_64.yaml')
    report = analyzer.analyze(Path('tests/integration/data/stress-ng-cpu-mix-out.txt'))
    assert report is not None
    assert 'summary' in report
    assert 'details' in report
    assert report['summary']['total_instructions'] > 0
    assert isinstance(report['summary']['coverage_percent'], float)