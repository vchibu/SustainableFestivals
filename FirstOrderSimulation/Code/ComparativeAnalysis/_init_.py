"""
ComparativeAnalysis package for analyzing festival sustainability metrics.

This package provides tools for comparative analysis of CSV files containing
festival sustainability metrics, including data loading, metric calculation,
and report generation capabilities.
"""

from .comparative_analysis import ComparativeAnalysis
from .data_processor import DataProcessor
from .metrics_calculator import MetricsCalculator
from .report_generator import ReportGenerator
from .constants import (
    PROJECT_ROOT,
    INPUT_DIRECTORY,
    OUTPUT_DIRECTORY,
    METRIC_GROUPS,
    CATEGORY_ORDER
)

__all__ = [
    'ComparativeAnalysis',
    'DataProcessor',
    'MetricsCalculator',
    'ReportGenerator',
    'PROJECT_ROOT',
    'INPUT_DIRECTORY',
    'OUTPUT_DIRECTORY',
    'METRIC_GROUPS',
    'CATEGORY_ORDER'
]