"""
Constants and configuration values for the Comparative Analysis module.
"""

import os

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


# Project structure constants
PROJECT_ROOT = find_project_root()
INPUT_DIRECTORY = os.path.join(PROJECT_ROOT, "Data", "FinalStatistics", "CSVs")
OUTPUT_DIRECTORY = os.path.join(PROJECT_ROOT, "Data", "ComparativeStatistics")

# Metric grouping constants
METRIC_GROUPS = {
    "Carbon Footprint Metrics": ["carbon"],
    "Cost Metrics": ["cost"],
    "Travel Time Metrics": ["time"],
    "Travel Legs Metrics": ["leg"],
    "Transport Mode Metrics": ["mode", "WALK", "BICYCLE", "CAR", "TRAM", "SUBWAY", "BUS", "RAIL"],
    "Other Metrics": []
}

# Category ordering
CATEGORY_ORDER = {
    'departure': 0,
    'return': 1,
    'combined': 2
}