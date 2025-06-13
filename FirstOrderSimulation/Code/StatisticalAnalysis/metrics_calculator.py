"""
Metrics calculation engine for transportation analysis.
"""

from .constants import DIRECT_MODES, TRANSIT_MODES

class MetricsCalculator:
    """Calculates various transportation metrics."""
    
    def __init__(self, data_processor):
        """
        Initialize with processed data.
        
        Args:
            data_processor: DataProcessor instance with processed data
        """
        self.data_processor = data_processor
        self.departure_df = data_processor.departure_df
        self.return_df = data_processor.return_df
        self.total_attendees = data_processor.total_attendees
    
    def compute_all_metrics(self):
        """
        Compute all transportation metrics categorized by trip type.
        
        Returns:
            Dictionary with metrics in three categories: 
            'departure', 'return', and 'combined'
        """
        metrics = {'departure': {}, 'return': {}, 'combined': {}}
        
        self._compute_carbon_metrics(metrics)
        self._compute_cost_metrics(metrics)
        self._compute_time_metrics(metrics)
        self._compute_leg_metrics(metrics)
        self._compute_direct_mode_metrics(metrics)
        self._compute_transit_mode_metrics(metrics)
        
        return metrics
    
    def _compute_carbon_metrics(self, metrics):
        """Calculate carbon footprint metrics."""
        # Departure metrics
        dep_carbon_total = self.departure_df['calculated_total_carbon_footprint'].sum()
        dep_carbon_avg = dep_carbon_total / len(self.departure_df)
        
        # Return metrics
        ret_carbon_total = self.return_df['calculated_total_carbon_footprint'].sum()
        ret_carbon_avg = ret_carbon_total / len(self.return_df)
        
        # Combined metrics
        total_carbon = dep_carbon_total + ret_carbon_total
        avg_carbon_per_attendee = total_carbon / max(len(self.departure_df), len(self.return_df))
        
        # Store metrics
        metrics['departure'].update({
            'total_carbon_footprint': dep_carbon_total,
            'avg_carbon_footprint': dep_carbon_avg
        })
        metrics['return'].update({
            'total_carbon_footprint': ret_carbon_total,
            'avg_carbon_footprint': ret_carbon_avg
        })
        metrics['combined'].update({
            'total_carbon_footprint': total_carbon,
            'avg_carbon_per_attendee': avg_carbon_per_attendee
        })
    
    def _compute_cost_metrics(self, metrics):
        """Calculate trip cost metrics."""
        # Departure metrics
        dep_cost_total = self.departure_df['calculated_total_cost'].sum()
        dep_cost_avg = dep_cost_total / len(self.departure_df)
        
        # Return metrics
        ret_cost_total = self.return_df['calculated_total_cost'].sum()
        ret_cost_avg = ret_cost_total / len(self.return_df)
        
        # Combined metrics
        total_cost = dep_cost_total + ret_cost_total
        avg_cost_per_attendee = total_cost / max(len(self.departure_df), len(self.return_df))
        
        # Store metrics
        metrics['departure'].update({
            'total_cost': dep_cost_total,
            'avg_cost': dep_cost_avg
        })
        metrics['return'].update({
            'total_cost': ret_cost_total,
            'avg_cost': ret_cost_avg
        })
        metrics['combined'].update({
            'total_cost': total_cost,
            'avg_cost_per_attendee': avg_cost_per_attendee
        })
    
    def _compute_time_metrics(self, metrics):
        """Calculate travel time metrics."""
        # Departure metrics
        dep_duration_total = self.departure_df['total_duration'].sum()
        dep_duration_avg = dep_duration_total / len(self.departure_df)
        
        # Return metrics
        ret_duration_total = self.return_df['total_duration'].sum()
        ret_duration_avg = ret_duration_total / len(self.return_df)
        
        # Combined metrics
        total_duration = dep_duration_total + ret_duration_total
        avg_duration_attendee = total_duration / max(len(self.departure_df), len(self.return_df))
        
        # Store metrics
        metrics['departure'].update({
            'total_travel_time': dep_duration_total,
            'avg_travel_time': dep_duration_avg
        })
        metrics['return'].update({
            'total_travel_time': ret_duration_total,
            'avg_travel_time': ret_duration_avg
        })
        metrics['combined'].update({
            'total_travel_time': total_duration,
            'avg_travel_time_per_attendee': avg_duration_attendee
        })
    
    def _compute_leg_metrics(self, metrics):
        """Calculate journey leg metrics."""
        # Departure metrics
        total_legs_departure = self.departure_df['leg_count'].sum()
        avg_legs_per_attendee_departure = total_legs_departure / len(self.departure_df)
        
        # Return metrics
        total_legs_return = self.return_df['leg_count'].sum()
        avg_legs_per_attendee_return = total_legs_return / len(self.return_df)
        
        # Combined metrics
        total_legs = total_legs_departure + total_legs_return
        avg_legs_per_attendee = total_legs / max(len(self.departure_df), len(self.return_df))
        
        # Store metrics
        metrics['departure'].update({
            'total_legs': total_legs_departure,
            'avg_legs_per_attendee': avg_legs_per_attendee_departure
        })
        metrics['return'].update({
            'total_legs': total_legs_return,
            'avg_legs_per_attendee': avg_legs_per_attendee_return
        })
        metrics['combined'].update({
            'total_legs': total_legs,
            'avg_legs_per_attendee': avg_legs_per_attendee
        })
    
    def _compute_direct_mode_metrics(self, metrics):
        """Calculate direct mode metrics (any leg, not just the first)."""
        for mode in DIRECT_MODES:
            # Count for departure trips
            dep_users = self.data_processor.count_attendees_using_mode(self.departure_df, mode)
            dep_count = len(dep_users)
            
            # Count for return trips
            ret_users = self.data_processor.count_attendees_using_mode(self.return_df, mode)
            ret_count = len(ret_users)
            
            # Combined unique users
            combined_users = dep_users | ret_users
            combined_count = len(combined_users)
            
            # Store metrics
            metrics['departure'].update({
                f'direct_mode_{mode}_count': dep_count,
                f'direct_mode_{mode}_proportion': dep_count / len(self.departure_df)
            })
            metrics['return'].update({
                f'direct_mode_{mode}_count': ret_count,
                f'direct_mode_{mode}_proportion': ret_count / len(self.return_df)
            })
            metrics['combined'].update({
                f'direct_mode_{mode}_count': combined_count,
                f'direct_mode_{mode}_proportion': combined_count / self.total_attendees
            })
    
    def _compute_transit_mode_metrics(self, metrics):
        """Calculate transit mode metrics (any leg)."""
        for mode in TRANSIT_MODES:
            # Count attendees using this mode in departure trips
            dep_users = self.data_processor.count_attendees_using_mode(self.departure_df, mode)
            dep_count = len(dep_users)
            
            # Count attendees using this mode in return trips
            ret_users = self.data_processor.count_attendees_using_mode(self.return_df, mode)
            ret_count = len(ret_users)
            
            # Combined users across both directions
            combined_users = dep_users | ret_users
            combined_count = len(combined_users)
            
            # Store metrics
            metrics['departure'].update({
                f'transit_mode_{mode}_count': dep_count,
                f'transit_mode_{mode}_proportion': dep_count / len(self.departure_df)
            })
            metrics['return'].update({
                f'transit_mode_{mode}_count': ret_count,
                f'transit_mode_{mode}_proportion': ret_count / len(self.return_df)
            })
            metrics['combined'].update({
                f'transit_mode_{mode}_count': combined_count,
                f'transit_mode_{mode}_proportion': combined_count / self.total_attendees
            })
