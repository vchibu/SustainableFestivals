"""
Report generation utilities for creating CSV and Markdown outputs.
"""

import os
import pandas as pd
from typing import Dict, List, Any
from .constants import CATEGORY_ORDER, METRIC_GROUPS

class ReportGenerator:
    """
    Handles generation of CSV and Markdown reports from comparative analysis results.
    """
    
    def __init__(self, comparative_results: Dict[str, Dict[str, Any]], 
                 data_frames: Dict[str, pd.DataFrame], 
                 metrics: List[str], 
                 categories: List[str]):
        """
        Initialize the ReportGenerator with analysis results and data.
        
        Args:
            comparative_results: Dictionary containing analysis results for each metric
            data_frames: Dictionary mapping file names to DataFrames
            metrics: List of metric names
            categories: List of category names
        """
        self.comparative_results = comparative_results
        self.data_frames = data_frames
        self.metrics = metrics
        self.categories = categories
    
    def generate_csv_report(self, output_path: str) -> None:
        """
        Generate a CSV report with the comparative analysis results.
        The CSV is organized by category (departure, return, combined).
        
        Args:
            output_path: Path where the CSV report will be saved
        """
        # Create separate DataFrames for each category
        category_dfs = {}
        
        # Ensure we process categories in a specific order
        ordered_categories = self._get_ordered_categories()
        
        for category in ordered_categories:
            rows = []
            
            for metric in self.metrics:
                if metric in self.comparative_results and category in self.comparative_results[metric]:
                    results = self.comparative_results[metric][category]
                    
                    row = {
                        'Metric': metric,
                        'Min_Value': results['min'],
                        'Min_File': results['min_file'],
                        'Max_Value': results['max'],
                        'Max_File': results['max_file'],
                        'Average': results['avg'],
                        'Std_Dev': results['std_dev']
                    }
                    
                    # Add values for each file
                    for file_name, value in results['values_by_file'].items():
                        row[f"{file_name}"] = value if value is not None else "N/A"
                        
                    rows.append(row)
            
            if rows:
                category_dfs[category] = pd.DataFrame(rows)
        
        # Write each category to a separate sheet in the Excel file or separate CSVs
        if output_path.endswith('.xlsx'):
            with pd.ExcelWriter(output_path) as writer:
                for category, df in category_dfs.items():
                    df.to_excel(writer, sheet_name=category, index=False)
            print(f"Excel report with separate sheets saved to {output_path}")
        else:
            # Create a single CSV with category as a column
            all_rows = []
            for category in ordered_categories:
                if category in category_dfs:
                    df = category_dfs[category]
                    for _, row in df.iterrows():
                        csv_row = {'Category': category}
                        csv_row.update(row)
                        all_rows.append(csv_row)
            
            # Create combined DataFrame and save to CSV
            if all_rows:
                combined_df = pd.DataFrame(all_rows)
                # Reorder columns to put Category first
                cols = combined_df.columns.tolist()
                cols.remove('Category')
                cols = ['Category'] + cols
                combined_df = combined_df[cols]
                combined_df.to_csv(output_path, index=False)
                print(f"CSV report saved to {output_path}")
            else:
                print("No data to write to CSV")
        
        # Also generate individual CSVs per category if needed
        base_path = os.path.splitext(output_path)[0]
        for category, df in category_dfs.items():
            category_path = f"{base_path}_{category}.csv"
            df.to_csv(category_path, index=False)
            print(f"{category.capitalize()} CSV report saved to {category_path}")
    
    def generate_markdown_report(self, output_path: str) -> None:
        """
        Generate a Markdown report with the comparative analysis results,
        clearly organizing metrics by category (departure, return, combined).
        
        Args:
            output_path: Path where the Markdown report will be saved
        """
        with open(output_path, 'w') as f:
            f.write("# Comparative Analysis of Festival Sustainability Metrics\n\n")
            
            f.write("## Summary of Analyzed Files\n\n")
            f.write("The following files were analyzed:\n\n")
            
            for file_name in self.data_frames.keys():
                f.write(f"- {file_name}\n")
            
            f.write("\n## Metrics Comparison by Category\n\n")
            
            # Ensure we process categories in a specific order (departure, return, combined)
            ordered_categories = self._get_ordered_categories()
            
            # Organize by category first (departure, return, combined)
            for category in ordered_categories:
                f.write(f"## {category.upper()} CATEGORY\n\n")
                
                # Group metrics by type (carbon, cost, time, etc.)
                metric_groups = self._group_related_metrics(category)
                
                for group_name, metrics_in_group in metric_groups.items():
                    f.write(f"### {group_name}\n\n")
                    
                    for metric in metrics_in_group:
                        if metric in self.comparative_results and category in self.comparative_results[metric]:
                            results = self.comparative_results[metric][category]
                            
                            # Format metric name for better readability
                            display_metric = metric.replace('_', ' ')
                            
                            f.write(f"#### {display_metric}\n\n")
                            f.write(f"- **Minimum**: {results['min']:.2f} ({results['min_file']})\n")
                            f.write(f"- **Maximum**: {results['max']:.2f} ({results['max_file']})\n")
                            f.write(f"- **Average**: {results['avg']:.2f}\n")
                            f.write(f"- **Standard Deviation**: {results['std_dev']:.2f}\n\n")
                            
                            f.write("Values by file:\n\n")
                            f.write("| File | Value |\n")
                            f.write("|------|-------|\n")
                            
                            # Sort files by value for better comparison
                            sorted_files = sorted(
                                [(file, value) for file, value in results['values_by_file'].items() if value is not None],
                                key=lambda x: x[1]
                            )
                            
                            for file_name, value in sorted_files:
                                f.write(f"| {file_name} | {value:.2f} |\n")
                                
                            # Add missing files as N/A
                            for file_name, value in results['values_by_file'].items():
                                if value is None:
                                    f.write(f"| {file_name} | N/A |\n")
                                    
                            f.write("\n")
            
            print(f"Markdown report saved to {output_path}")
    
    def _get_ordered_categories(self) -> List[str]:
        """
        Get categories ordered according to the predefined order.
        
        Returns:
            List of categories in the correct order
        """
        return sorted(self.categories, 
                     key=lambda x: CATEGORY_ORDER.get(x, 999))
    
    def _group_related_metrics(self, category: str) -> Dict[str, List[str]]:
        """
        Group related metrics together for better organization in the report.
        
        Args:
            category: The category to group metrics for
            
        Returns:
            Dictionary mapping group names to lists of metrics
        """
        # Filter metrics that appear in this category
        relevant_metrics = []
        for metric in self.metrics:
            if metric in self.comparative_results and category in self.comparative_results[metric]:
                relevant_metrics.append(metric)
        
        # Initialize groups
        groups = {group_name: [] for group_name in METRIC_GROUPS.keys()}
        
        for metric in relevant_metrics:
            assigned = False
            
            # Check each group (except "Other Metrics")
            for group_name, keywords in METRIC_GROUPS.items():
                if group_name == "Other Metrics":
                    continue
                    
                # Check if any keyword appears in the metric name
                if any(keyword.lower() in metric.lower() for keyword in keywords):
                    groups[group_name].append(metric)
                    assigned = True
                    break
            
            # If not assigned to any specific group, put in "Other Metrics"
            if not assigned:
                groups["Other Metrics"].append(metric)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}