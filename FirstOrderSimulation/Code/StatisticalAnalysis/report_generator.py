"""
Report generation utilities for transportation analysis.
"""

import pandas as pd
from datetime import datetime
from .constants import DIRECT_MODES, TRANSIT_MODES, METRIC_CATEGORIES


class ReportGenerator:
    """Generates reports in various formats."""
    
    def __init__(self, total_attendees):
        """
        Initialize report generator.
        
        Args:
            total_attendees: Total number of attendees
        """
        self.total_attendees = total_attendees
    
    def save_to_csv(self, metrics, file_path):
        """Save metrics to a CSV file."""
        flattened_metrics = self._flatten_metrics(metrics)
        metrics_df = pd.DataFrame(flattened_metrics)
        metrics_df.to_csv(file_path, index=False)
        print(f"Metrics saved to CSV: {file_path}")
    
    def save_to_markdown(self, metrics, file_path):
        """Save metrics to a Markdown file with formatted tables."""
        with open(file_path, 'w') as md_file:
            self._write_markdown_header(md_file)
            
            for category in METRIC_CATEGORIES:
                self._write_category_section(md_file, category, metrics[category])
            
            self._write_markdown_footer(md_file)
            
        print(f"Metrics saved to Markdown: {file_path}")
    
    def print_summary(self, metrics):
        """Print a summary of analysis results."""
        print("===== TRANSPORTATION ANALYSIS SUMMARY =====")
        print(f"Total number of attendees: {self.total_attendees}")
        
        for category in METRIC_CATEGORIES:
            self._print_category_summary(category, metrics[category])
    
    def _flatten_metrics(self, metrics):
        """Flatten the metrics dictionary into a list of dictionaries."""
        flattened_metrics = []
        for category, category_metrics in metrics.items():
            for metric_name, value in category_metrics.items():
                flattened_metrics.append({
                    "Category": category,
                    "Metric": metric_name,
                    "Value": value
                })
        return flattened_metrics
    
    def _write_markdown_header(self, md_file):
        """Write the markdown file header."""
        md_file.write("# Transportation Analysis Results\n\n")
        md_file.write(f"Total number of attendees: {self.total_attendees}\n\n")
    
    def _write_category_section(self, md_file, category, cat_metrics):
        """Write a category section to the markdown file."""
        md_file.write(f"## {category.capitalize()} Trip Metrics\n\n")
        
        self._write_carbon_section(md_file, cat_metrics)
        self._write_cost_section(md_file, cat_metrics)
        self._write_time_section(md_file, cat_metrics)
        self._write_legs_section(md_file, cat_metrics)
        self._write_direct_modes_section(md_file, cat_metrics)
        self._write_transit_modes_section(md_file, cat_metrics)
    
    def _write_carbon_section(self, md_file, cat_metrics):
        """Write carbon footprint section."""
        md_file.write("### Carbon Footprint\n\n")
        md_file.write("| Metric | Value |\n|--------|-------|\n")
        
        carbon_metrics = [
            ('total_carbon_footprint', 'Total carbon footprint', 'units'),
            ('avg_carbon_footprint', 'Average carbon footprint', 'units'),
            ('avg_carbon_per_attendee', 'Average carbon per attendee', 'units')
        ]
        
        for key, label, unit in carbon_metrics:
            if key in cat_metrics:
                md_file.write(f"| {label} | {cat_metrics[key]:.2f} {unit} |\n")
        md_file.write("\n")
    
    def _write_cost_section(self, md_file, cat_metrics):
        """Write cost section."""
        md_file.write("### Cost\n\n")
        md_file.write("| Metric | Value |\n|--------|-------|\n")
        
        cost_metrics = [
            ('total_cost', 'Total cost'),
            ('avg_cost', 'Average cost'),
            ('avg_cost_per_attendee', 'Average cost per attendee')
        ]
        
        for key, label in cost_metrics:
            if key in cat_metrics:
                md_file.write(f"| {label} | {cat_metrics[key]:.2f} |\n")
        md_file.write("\n")
    
    def _write_time_section(self, md_file, cat_metrics):
        """Write travel time section."""
        md_file.write("### Travel Time\n\n")
        md_file.write("| Metric | Value |\n|--------|-------|\n")
        
        time_metrics = [
            ('total_travel_time', 'Total travel time'),
            ('avg_travel_time', 'Average travel time'),
            ('avg_travel_time_per_attendee', 'Average travel time per attendee')
        ]
        
        for key, label in time_metrics:
            if key in cat_metrics:
                md_file.write(f"| {label} | {cat_metrics[key]:.2f} minutes |\n")
        md_file.write("\n")
    
    def _write_legs_section(self, md_file, cat_metrics):
        """Write journey complexity section."""
        md_file.write("### Journey Complexity\n\n")
        md_file.write("| Metric | Value |\n|--------|-------|\n")
        
        if 'total_legs' in cat_metrics:
            md_file.write(f"| Total journey legs | {cat_metrics['total_legs']} |\n")
        if 'avg_legs_per_attendee' in cat_metrics:
            md_file.write(f"| Average legs per attendee | {cat_metrics['avg_legs_per_attendee']:.2f} |\n")
        md_file.write("\n")
    
    def _write_direct_modes_section(self, md_file, cat_metrics):
        """Write direct mode distribution section."""
        md_file.write("### Direct Mode Distribution\n\n")
        md_file.write("| Mode | Count | Percentage |\n|------|-------|------------|\n")
        
        for mode in DIRECT_MODES:
            self._write_mode_row(md_file, cat_metrics, mode, 'direct_mode')
        md_file.write("\n")
    
    def _write_transit_modes_section(self, md_file, cat_metrics):
        """Write transit mode usage section."""
        md_file.write("### Transit Mode Usage\n\n")
        md_file.write("| Mode | Count | Percentage |\n|------|-------|------------|\n")
        
        for mode in TRANSIT_MODES:
            self._write_mode_row(md_file, cat_metrics, mode, 'transit_mode')
        md_file.write("\n")
    
    def _write_mode_row(self, md_file, cat_metrics, mode, mode_type):
        """Write a single mode row to the markdown table."""
        count_key = f'{mode_type}_{mode}_count'
        prop_key = f'{mode_type}_{mode}_proportion'
        
        if count_key in cat_metrics and prop_key in cat_metrics:
            count = cat_metrics[count_key]
            proportion = cat_metrics[prop_key] * 100
            md_file.write(f"| {mode} | {count} | {proportion:.1f}% |\n")
    
    def _write_markdown_footer(self, md_file):
        """Write the markdown file footer."""
        md_file.write("## Summary and Recommendations\n\n")
        md_file.write("This analysis provides insights into attendee transportation patterns for the festival. ")
        md_file.write("Based on the data, recommendations can be made for improving sustainability, cost-efficiency, and overall transportation experience in future events.\n\n")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        md_file.write(f"*Report generated on: {timestamp}*\n")
    
    def _print_category_summary(self, category, cat_metrics):
        """Print summary for a single category."""
        print(f"\n==== {category.upper()} TRIP METRICS ====")
        
        self._print_carbon_summary(cat_metrics)
        self._print_cost_summary(cat_metrics)
        self._print_time_summary(cat_metrics)
        self._print_legs_summary(cat_metrics)
        self._print_direct_modes_summary(cat_metrics)
        self._print_transit_modes_summary(cat_metrics)
    
    def _print_carbon_summary(self, cat_metrics):
        """Print carbon footprint summary."""
        print("\n----- CARBON FOOTPRINT -----")
        carbon_keys = ['total_carbon_footprint', 'avg_carbon_footprint', 'avg_carbon_per_attendee']
        carbon_labels = ['Total carbon footprint', 'Average carbon footprint', 'Average carbon per attendee']
        
        for key, label in zip(carbon_keys, carbon_labels):
            if key in cat_metrics:
                print(f"{label}: {cat_metrics[key]:.2f} units")
    
    def _print_cost_summary(self, cat_metrics):
        """Print cost summary."""
        print("\n----- COST -----")
        cost_keys = ['total_cost', 'avg_cost', 'avg_cost_per_attendee']
        cost_labels = ['Total cost', 'Average cost', 'Average cost per attendee']
        
        for key, label in zip(cost_keys, cost_labels):
            if key in cat_metrics:
                print(f"{label}: {cat_metrics[key]:.2f}")
    
    def _print_time_summary(self, cat_metrics):
        """Print travel time summary."""
        print("\n----- TRAVEL TIME -----")
        time_keys = ['total_travel_time', 'avg_travel_time', 'avg_travel_time_per_attendee']
        time_labels = ['Total travel time', 'Average travel time', 'Average travel time per attendee']
        
        for key, label in zip(time_keys, time_labels):
            if key in cat_metrics:
                print(f"{label}: {cat_metrics[key]:.2f} minutes")
    
    def _print_legs_summary(self, cat_metrics):
        """Print journey complexity summary."""
        print("\n----- JOURNEY COMPLEXITY -----")
        if 'total_legs' in cat_metrics:
            print(f"Total legs: {cat_metrics['total_legs']}")
        if 'avg_legs_per_attendee' in cat_metrics:
            print(f"Average legs per attendee: {cat_metrics['avg_legs_per_attendee']:.2f}")
    
    def _print_direct_modes_summary(self, cat_metrics):
        """Print direct mode distribution summary."""
        print("\n----- DIRECT MODE DISTRIBUTION -----")
        for mode in DIRECT_MODES:
            self._print_mode_summary(cat_metrics, mode, 'direct_mode')
    
    def _print_transit_modes_summary(self, cat_metrics):
        """Print transit mode usage summary."""
        print("\n----- TRANSIT MODE USAGE -----")
        for mode in TRANSIT_MODES:
            self._print_mode_summary(cat_metrics, mode, 'transit_mode')
    
    def _print_mode_summary(self, cat_metrics, mode, mode_type):
        """Print summary for a single transportation mode."""
        count_key = f'{mode_type}_{mode}_count'
        prop_key = f'{mode_type}_{mode}_proportion'
        
        if count_key in cat_metrics:
            count = cat_metrics[count_key]
            if prop_key in cat_metrics:
                proportion = cat_metrics[prop_key] * 100
                print(f"{mode}: {count} attendees ({proportion:.1f}%)")
            else:
                print(f"{mode}: {count} attendees")
