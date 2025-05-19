import os
import pandas as pd
import glob
import numpy as np
from typing import Dict, List, Tuple, Any, Optional


def find_project_root():
    """Find the project root directory by looking for characteristic files/directories."""
    current_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Look for project root indicators
    while current_dir != os.path.dirname(current_dir):  # Not at filesystem root
        # Check for typical project root indicators
        if (os.path.exists(os.path.join(current_dir, "Data")) and 
            os.path.exists(os.path.join(current_dir, "Code")) and
            os.path.exists(os.path.join(current_dir, "README.md"))):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    
    # If not found, try current working directory
    cwd = os.getcwd()
    if (os.path.exists(os.path.join(cwd, "Data")) and 
        os.path.exists(os.path.join(cwd, "Code"))):
        return cwd
    
    # Last resort: use the directory two levels up from this file
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Find project root and set paths
PROJECT_ROOT = find_project_root()
INPUT_DIRECTORY = os.path.join(PROJECT_ROOT, "Data", "FinalStatistics", "CSVs")
OUTPUT_DIRECTORY = os.path.join(PROJECT_ROOT, "Data", "ComparativeStatistics")


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
            
        self.directory_path = os.path.abspath(directory_path)
        self.csv_files = []
        self.data_frames = {}
        self.metrics = []
        self.categories = []  # Expected to contain ['departure', 'return', 'combined']
        self.comparative_results = {}
        
        print(f"Looking for CSV files in: {self.directory_path}")
        self.load_csv_files()
        
    def load_csv_files(self) -> None:
        """
        Load all CSV files from the specified directory and process them into DataFrames.
        """
        # Check if directory exists
        if not os.path.exists(self.directory_path):
            raise FileNotFoundError(f"Directory does not exist: {self.directory_path}")
        
        # Find all CSV files in the directory
        self.csv_files = glob.glob(os.path.join(self.directory_path, "*.csv"))
        
        if not self.csv_files:
            # List what files are actually in the directory
            files_in_dir = os.listdir(self.directory_path)
            raise FileNotFoundError(
                f"No CSV files found in {self.directory_path}\n"
                f"Files found in directory: {files_in_dir}"
            )
            
        print(f"Found {len(self.csv_files)} CSV files:")
        for file_path in self.csv_files:
            print(f"  - {os.path.basename(file_path)}")
            
        # Read each CSV file and store as DataFrame
        for file_path in self.csv_files:
            file_name = os.path.basename(file_path).replace('.csv', '')
            try:
                df = pd.read_csv(file_path)
                self.data_frames[file_name] = df
                print(f"  Loaded {file_name}: {len(df)} rows, {len(df.columns)} columns")
            except Exception as e:
                print(f"  Error loading {file_name}: {e}")
                continue
                
        # Extract unique metrics and categories from the first successfully loaded file
        if self.data_frames:
            sample_df = next(iter(self.data_frames.values()))
            self.metrics = sample_df['Metric'].unique().tolist()
            self.categories = sample_df['Category'].unique().tolist()
            print(f"Found metrics: {self.metrics}")
            print(f"Found categories: {self.categories}")
        else:
            raise RuntimeError("No CSV files could be loaded successfully")
        
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
    
    def generate_csv_report(self, output_path: str) -> None:
        """
        Generate a CSV report with the comparative analysis results.
        The CSV is organized by category (departure, return, combined).
        
        Args:
            output_path: Path where the CSV report will be saved
        """
        if not self.comparative_results:
            self.analyze_metrics()
            
        # Create separate DataFrames for each category
        category_dfs = {}
        
        # Ensure we process categories in a specific order
        ordered_categories = sorted(self.categories, 
                                   key=lambda x: (0 if x == 'departure' else 
                                                 1 if x == 'return' else 
                                                 2 if x == 'combined' else 3))
        
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
        if not self.comparative_results:
            self.analyze_metrics()
            
        with open(output_path, 'w') as f:
            f.write("# Comparative Analysis of Festival Sustainability Metrics\n\n")
            
            f.write("## Summary of Analyzed Files\n\n")
            f.write("The following files were analyzed:\n\n")
            
            for file_name in self.data_frames.keys():
                f.write(f"- {file_name}\n")
            
            f.write("\n## Metrics Comparison by Category\n\n")
            
            # Ensure we process categories in a specific order (departure, return, combined)
            ordered_categories = sorted(self.categories, 
                                       key=lambda x: (0 if x == 'departure' else 
                                                     1 if x == 'return' else 
                                                     2 if x == 'combined' else 3))
            
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
        
        # Define groups based on common prefixes or themes
        groups = {
            "Carbon Footprint Metrics": [],
            "Cost Metrics": [],
            "Travel Time Metrics": [],
            "Travel Legs Metrics": [],
            "Transport Mode Metrics": [],
            "Other Metrics": []
        }
        
        for metric in relevant_metrics:
            if "carbon" in metric:
                groups["Carbon Footprint Metrics"].append(metric)
            elif "cost" in metric:
                groups["Cost Metrics"].append(metric)
            elif "time" in metric:
                groups["Travel Time Metrics"].append(metric)
            elif "leg" in metric:
                groups["Travel Legs Metrics"].append(metric)
            elif "mode" in metric or any(mode in metric for mode in ["WALK", "BICYCLE", "CAR", "TRAM", "SUBWAY", "BUS", "RAIL"]):
                groups["Transport Mode Metrics"].append(metric)
            else:
                groups["Other Metrics"].append(metric)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
    def run_analysis(self, csv_output_path: str, md_output_path: str) -> Dict[str, Dict[str, Any]]:
        """
        Run the complete analysis workflow and generate both CSV and Markdown reports.
        
        Args:
            csv_output_path: Path where the CSV report will be saved
            md_output_path: Path where the Markdown report will be saved
            
        Returns:
            Dictionary containing analysis results
        """
        print(f"Starting analysis of {len(self.csv_files)} CSV files from {self.directory_path}")
        
        results = self.analyze_metrics()
        self.generate_csv_report(csv_output_path)
        self.generate_markdown_report(md_output_path)
        
        print("Analysis complete!")
        return results


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
