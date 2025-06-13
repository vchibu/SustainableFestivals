"""
Metrics calculation utilities for comparative analysis.
"""

import numpy as np
from typing import Dict, List, Any
import pandas as pd


class MetricsCalculator:
    """
    Handles calculation of comparative metrics across multiple datasets.
    """
    
    def __init__(self, data_frames: Dict[str, pd.DataFrame], metrics: List[str], categories: List[str]):
        """
        Initialize the MetricsCalculator with data and metric information.
        
        Args:
            data_frames: Dictionary mapping file names to DataFrames
            metrics: List of metric names to analyze
            categories: List of category names to analyze
        """
        self.data_frames = data_frames
        self.metrics = metrics
        self.categories = categories
        self.comparative_results = {}
    
    def analyze_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze metrics across all CSV files to find min, max, avg, etc.
        
        Returns:
            Dictionary containing analysis results for each metric
        """
        results = {}
        
        # For each metric
        for metric in self.metrics:
            metric_data = {}
            values_by_file = {}
            
            # Extract values for this metric from each file
            for file_name, df in self.data_frames.items():
                metric_rows = df[df['Metric'] == metric]
                
                for _, row in metric_rows.iterrows():
                    category = row['Category']
                    value = row['Value']
                    
                    key = f"{category}_{metric}"
                    if key not in metric_data:
                        metric_data[key] = []
                    
                    metric_data[key].append((file_name, value))
                    
                    # Also store by file for easier access
                    if file_name not in values_by_file:
                        values_by_file[file_name] = {}
                    values_by_file[file_name][category] = value
            
            # Analyze each category for this metric
            metric_results = {}
            for category in self.categories:
                key = f"{category}_{metric}"
                if key in metric_data:
                    data = metric_data[key]
                    values = [item[1] for item in data]
                    
                    if values:
                        min_value = min(values)
                        max_value = max(values)
                        avg_value = sum(values) / len(values)
                        std_dev = np.std(values) if len(values) > 1 else 0
                        
                        min_file = next(item[0] for item in data if item[1] == min_value)
                        max_file = next(item[0] for item in data if item[1] == max_value)
                        
                        metric_results[category] = {
                            'min': min_value,
                            'min_file': min_file,
                            'max': max_value,
                            'max_file': max_file,
                            'avg': avg_value,
                            'std_dev': std_dev,
                            'values_by_file': {file: values_by_file.get(file, {}).get(category, None) 
                                              for file in self.data_frames.keys()}
                        }
            
            results[metric] = metric_results
            
        self.comparative_results = results
        return results
    
    def get_comparative_results(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the comparative analysis results.
        
        Returns:
            Dictionary containing analysis results for each metric
        """
        return self.comparative_results
    
    def group_related_metrics(self, category: str, metric_groups: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Group related metrics together for better organization.
        
        Args:
            category: The category to group metrics for
            metric_groups: Dictionary defining metric groups and their keywords
            
        Returns:
            Dictionary mapping group names to lists of metrics
        """
        # Filter metrics that appear in this category
        relevant_metrics = []
        for metric in self.metrics:
            if metric in self.comparative_results and category in self.comparative_results[metric]:
                relevant_metrics.append(metric)
        
        # Initialize groups
        groups = {group_name: [] for group_name in metric_groups.keys()}
        
        for metric in relevant_metrics:
            assigned = False
            
            # Check each group (except "Other Metrics")
            for group_name, keywords in metric_groups.items():
                if group_name == "Other Metrics":
                    continue
                    
                # Check if any keyword appears in the metric name
                if any(keyword.lower() in metric.lower() for keyword in keywords):
                    groups[group_name].append(metric)
                    assigned = True
                    break
            
            # If not assigned to any specific group, put in "Other Metrics"
            if not assigned and "Other Metrics" in groups:
                groups["Other Metrics"].append(metric)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}