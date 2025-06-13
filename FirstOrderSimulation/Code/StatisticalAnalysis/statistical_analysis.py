"""
Main statistical analysis class that orchestrates the entire analysis process.
"""

from .data_processor import DataProcessor
from .metrics_calculator import MetricsCalculator
from .report_generator import ReportGenerator


class StatisticalAnalysis:
    """
    A class that analyzes transportation data for festival attendees,
    calculating carbon footprints, travel times, transportation modes, and costs.
    """
    
    def __init__(self, departure_df, return_df):
        """
        Initialize with the departure and return dataframes.
        
        Args:
            departure_df: DataFrame containing departure trip data
            return_df: DataFrame containing return trip data
        """
        # Initialize data processor
        self.data_processor = DataProcessor(departure_df, return_df)
        
        # Initialize metrics calculator
        self.metrics_calculator = MetricsCalculator(self.data_processor)
        
        # Initialize report generator
        self.report_generator = ReportGenerator(self.data_processor.total_attendees)
        
        # Expose commonly used attributes for backward compatibility
        self.departure_df = self.data_processor.departure_df
        self.return_df = self.data_processor.return_df
        self.total_attendees = self.data_processor.total_attendees
        self.transit_modes = self.data_processor.transit_modes
        self.all_attendees = self.data_processor.all_attendees
    
    def analyze(self, output_csv=None, output_md=None, print_summary=False):
        """
        Analyze transportation data and return metrics.
        
        Args:
            output_csv: Optional file path to save results as CSV
            output_md: Optional file path to save results as Markdown
            print_summary: Whether to print a summary of results to console
            
        Returns:
            Dictionary containing all computed metrics
        """
        # Compute all metrics
        metrics = self.metrics_calculator.compute_all_metrics()
        
        # Generate reports if requested
        if output_csv:
            self.report_generator.save_to_csv(metrics, output_csv)
        
        if output_md:
            self.report_generator.save_to_markdown(metrics, output_md)
        
        if print_summary:
            self.report_generator.print_summary(metrics)
        
        return metrics
    
    # Backward compatibility methods
    def _count_attendees_using_mode(self, df, mode):
        """Backward compatibility method."""
        return self.data_processor.count_attendees_using_mode(df, mode)
    
    def _process_journey_legs(self):
        """Backward compatibility method."""
        return self.data_processor._process_journey_legs()