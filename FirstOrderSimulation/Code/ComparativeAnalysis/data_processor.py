"""
Data processing utilities for loading and processing CSV files.
"""

import os
import pandas as pd
import glob
from typing import Dict, List


class DataProcessor:
    """
    Handles loading and initial processing of CSV files for comparative analysis.
    """
    
    def __init__(self, directory_path: str):
        """
        Initialize the DataProcessor with the path to the directory containing CSV files.
        
        Args:
            directory_path: Path to the directory containing the CSV files to process.
        """
        self.directory_path = os.path.abspath(directory_path)
        self.csv_files = []
        self.data_frames = {}
        self.metrics = []
        self.categories = []
    
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
    
    def get_data_frames(self) -> Dict[str, pd.DataFrame]:
        """
        Get the loaded DataFrames.
        
        Returns:
            Dictionary mapping file names to DataFrames
        """
        return self.data_frames
    
    def get_metrics(self) -> List[str]:
        """
        Get the list of unique metrics found in the data.
        
        Returns:
            List of metric names
        """
        return self.metrics
    
    def get_categories(self) -> List[str]:
        """
        Get the list of unique categories found in the data.
        
        Returns:
            List of category names
        """
        return self.categories
    
    def get_csv_files(self) -> List[str]:
        """
        Get the list of CSV file paths that were processed.
        
        Returns:
            List of CSV file paths
        """
        return self.csv_files