import pytest
from src.core.coverage.analyzer import CoverageAnalyzer

def test_analyzer_init():
    analyzer = CoverageAnalyzer('config/instruction_specs/x86_64.yaml')
    assert analyzer is not None
    assert len(analyzer.spec) > 0
