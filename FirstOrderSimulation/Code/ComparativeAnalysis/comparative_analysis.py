"""
Main Comparative Analysis module for festival sustainability metrics.

This module provides the ComparativeAnalysis class which orchestrates the entire
analysis workflow, from data loading to report generation.
"""

import os
from typing import Dict, List, Any

from .constants import INPUT_DIRECTORY, OUTPUT_DIRECTORY
from .data_processor import DataProcessor
from .metrics_calculator import MetricsCalculator
from .report_generator import ReportGenerator


class ComparativeAnalysis:
    """
    A class for comparative analysis of CSV files containing festival sustainability metrics.
    
    This class reads all CSV files in a specified directory with a specific structure,
    compares the metrics across files, and generates summary reports in both CSV and Markdown
    formats.
    """
    
    def __init__(self, directory_path: str = None):
        """
        Initialize the ComparativeAnalysis with the path to the directory containing CSV files.
        
        Args:
            directory_path: Path to the directory containing the CSV files to analyze.
                          If None, uses the default INPUT_DIRECTORY.
        """
        if directory_path is None:
            directory_path = INPUT_DIRECTORY
            
        print(f"Looking for CSV files in: {directory_path}")
        
        # Initialize data processor and load files
        self.data_processor = DataProcessor(directory_path)
        self.data_processor.load_csv_files()
        
        # Initialize metrics calculator
        self.metrics_calculator = MetricsCalculator(
            self.data_processor.get_data_frames(),
            self.data_processor.get_metrics(),
            self.data_processor.get_categories()
        )
        
        # Initialize report generator (will be updated after analysis)
        self.report_generator = None
        
    def analyze_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze metrics across all CSV files to find min, max, avg, etc.
        
        Returns:
            Dictionary containing analysis results for each metric
        """
        results = self.metrics_calculator.analyze_metrics()
        
        # Initialize report generator with analysis results
        self.report_generator = ReportGenerator(
            self.metrics_calculator.get_comparative_results(),
            self.data_processor.get_data_frames(),
            self.data_processor.get_metrics(),
            self.data_processor.get_categories()
        )
        
        return results
        
    def generate_csv_report(self, output_path: str) -> None:
        """
        Generate a CSV report with the comparative analysis results.
        The CSV is organized by category (departure, return, combined).
        
        Args:
            output_path: Path where the CSV report will be saved
        """
        if self.report_generator is None:
            self.analyze_metrics()
        
        self.report_generator.generate_csv_report(output_path)
        
    def generate_markdown_report(self, output_path: str) -> None:
        """
        Generate a Markdown report with the comparative analysis results,
        clearly organizing metrics by category (departure, return, combined).
        
        Args:
            output_path: Path where the Markdown report will be saved
        """
        if self.report_generator is None:
            self.analyze_metrics()
        
        self.report_generator.generate_markdown_report(output_path)
    
    def run_analysis(self, csv_output_path: str, md_output_path: str) -> Dict[str, Dict[str, Any]]:
        """
        Run the complete analysis workflow and generate both CSV and Markdown reports.
        
        Args:
            csv_output_path: Path where the CSV report will be saved
            md_output_path: Path where the Markdown report will be saved
            
        Returns:
            Dictionary containing analysis results
        """
        csv_files = self.data_processor.get_csv_files()
        print(f"Starting analysis of {len(csv_files)} CSV files from {self.data_processor.directory_path}")
        
        results = self.analyze_metrics()
        self.generate_csv_report(csv_output_path)
        self.generate_markdown_report(md_output_path)
        
        print("Analysis complete!")
        return results
    
    # Convenience methods to access underlying data
    def get_data_frames(self) -> Dict[str, Any]:
        """Get the loaded data frames."""
        return self.data_processor.get_data_frames()
    
    def get_metrics(self) -> List[str]:
        """Get the list of metrics."""
        return self.data_processor.get_metrics()
    
    def get_categories(self) -> List[str]:
        """Get the list of categories."""
        return self.data_processor.get_categories()
    
    def get_comparative_results(self) -> Dict[str, Dict[str, Any]]:
        """Get the comparative analysis results."""
        if self.metrics_calculator:
            return self.metrics_calculator.get_comparative_results()
        return {}


# Example usage
if __name__ == "__main__":
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    
    # Initialize the analyzer with the default path
    analyzer = ComparativeAnalysis()
    
    # Run the complete analysis
    analyzer.run_analysis(
        csv_output_path=os.path.join(OUTPUT_DIRECTORY, "comparative_analysis.csv"),
        md_output_path=os.path.join(OUTPUT_DIRECTORY, "comparative_analysis.md")
    )