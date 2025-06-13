"""
Data processing utilities for transportation analysis.
"""

import pandas as pd
from .constants import ALL_TRANSIT_MODES

class DataProcessor:
    """Handles data preprocessing and preparation for analysis."""
    
    def __init__(self, departure_df, return_df):
        """
        Initialize with departure and return dataframes.
        
        Args:
            departure_df: DataFrame containing departure trip data
            return_df: DataFrame containing return trip data
        """
        self.departure_df = departure_df.copy()
        self.return_df = return_df.copy()
        self.transit_modes = ALL_TRANSIT_MODES
        
        # Process the data
        self._merge_attendee_data()
        self._calculate_total_attendees()
        self._process_journey_legs()
    
    def _merge_attendee_data(self):
        """Merge departure and return dataframes."""
        self.all_attendees = pd.merge(
            self.departure_df,
            self.return_df,
            on='attendee_id',
            suffixes=('_dep', '_ret')
        )
    
    def _calculate_total_attendees(self):
        """Calculate the total number of unique attendees."""
        self.total_attendees = len(pd.concat([
            self.departure_df['attendee_id'],
            self.return_df['attendee_id']
        ]).unique())
    
    def _process_journey_legs(self):
        """Count journey legs and prepare data for analysis."""
        self.departure_df['leg_count'] = self.departure_df.apply(self._count_legs, axis=1)
        self.return_df['leg_count'] = self.return_df.apply(self._count_legs, axis=1)
    
    def _count_legs(self, row):
        """Count non-empty legs in a trip."""
        leg_columns = [col for col in row.index if 'leg' in col and 'mode' in col]
        return sum(1 for col in leg_columns if pd.notna(row[col]) and row[col] != '')
    
    def count_attendees_using_mode(self, df, mode):
        """
        Count attendees who use a specific mode in any leg of their journey.
        
        Args:
            df: DataFrame containing trip data
            mode: Transportation mode to count
            
        Returns:
            Set of attendee IDs using the specified mode
        """
        leg_columns = [col for col in df.columns if 'leg' in col and 'mode' in col]
        
        attendees_using_mode = set()
        for col in leg_columns:
            mode_users = df[df[col] == mode]['attendee_id']
            attendees_using_mode.update(mode_users)
            
        return attendees_using_mode