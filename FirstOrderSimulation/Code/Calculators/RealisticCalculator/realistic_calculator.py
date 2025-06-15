from Code.Calculators.RealisticCalculator.priority_assigner import PriorityAssigner
from Code.Calculators.RealisticCalculator.trip_selector import TripSelector

class RealisticCalculator:
    """Main calculator class that orchestrates the trip selection process."""
    
    def __init__(self):
        self.priority_assigner = PriorityAssigner()
        self.trip_selector = TripSelector()
    
    def select_best_trips(self, departure_df=None, return_df=None):
        """
        Main method that assigns priorities to attendees and selects the best trips for both departure and return.
        
        Args:
            departure_df: pandas DataFrame with departure trips and 'attendee_id' column (optional)
            return_df: pandas DataFrame with return trips and 'attendee_id' column (optional)
            
        Returns:
            tuple: (best_departure_trips, best_return_trips) - both as pandas DataFrames with 
                   'priority' and 'second_priority' columns. Returns None for any DataFrame that was None/empty.
        """
        # Handle empty/None inputs
        if (departure_df is None or len(departure_df) == 0) and (return_df is None or len(return_df) == 0):
            return None, None
        
        # Get all unique attendees from both DataFrames
        unique_attendees = self._get_unique_attendees(departure_df, return_df)
        
        # Assign priorities once for all attendees
        attendee_priority_map = self.priority_assigner.assign_priorities_to_attendees(unique_attendees)
        
        # Process departure trips
        best_departure_trips = None
        if departure_df is not None and len(departure_df) > 0:
            departure_with_priorities = self._apply_priorities_to_dataframe(
                departure_df.copy(), attendee_priority_map
            )
            best_departure_trips = self.trip_selector.select_optimal_trips_per_attendee(departure_with_priorities)
        
        # Process return trips
        best_return_trips = None
        if return_df is not None and len(return_df) > 0:
            return_with_priorities = self._apply_priorities_to_dataframe(
                return_df.copy(), attendee_priority_map
            )
            best_return_trips = self.trip_selector.select_optimal_trips_per_attendee(return_with_priorities)
        
        return best_departure_trips, best_return_trips
    
    def _get_unique_attendees(self, departure_df, return_df):
        """Get unique attendees from both DataFrames."""
        unique_attendees = set()
        
        if departure_df is not None and len(departure_df) > 0:
            unique_attendees.update(departure_df['attendee_id'].unique())
        
        if return_df is not None and len(return_df) > 0:
            unique_attendees.update(return_df['attendee_id'].unique())
        
        return list(unique_attendees)
    
    def _apply_priorities_to_dataframe(self, df, attendee_priority_map):
        """Apply priority assignments to all rows in the DataFrame."""
        df['priority'] = df['attendee_id'].map(
            lambda x: attendee_priority_map[x]['priority']
        )
        df['second_priority'] = df['attendee_id'].map(
            lambda x: attendee_priority_map[x]['second_priority']
        )
        return df
