from Code.Calculators.RealisticCalculator.constants import PriorityConstants, TradeOffThresholds
import pandas as pd

class TradeOffAnalyzer:
    """Analyzes and applies trade-off logic for different priority combinations."""
    
    def __init__(self):
        self.thresholds = TradeOffThresholds()
        self.constants = PriorityConstants()
    
    def apply_trade_off_logic(self, trips, primary_priority, second_priority):
        """Apply appropriate trade-off logic based on priority combination."""
        priority_combo = f"{primary_priority}_{second_priority}"
        
        if priority_combo in self.thresholds.THRESHOLDS:
            return self._apply_survey_trade_offs(trips, primary_priority, second_priority, priority_combo)
        else:
            return self._standard_priority_selection(trips, primary_priority, second_priority)
    
    def _apply_survey_trade_offs(self, trips, primary_priority, second_priority, priority_combo):
        """Apply survey-based trade-off logic."""
        primary_col = self.constants.PRIORITY_COLUMNS[primary_priority]
        second_col = self.constants.PRIORITY_COLUMNS[second_priority]
        
        best_primary_trip = trips.loc[trips[primary_col].idxmin()]
        
        trade_off_methods = {
            'DURATION_COST': self._duration_cost_trade_off,
            'COST_DURATION': self._cost_duration_trade_off,
            'COST_CONVENIENCE': self._cost_convenience_trade_off,
            'CONVENIENCE_COST': self._convenience_cost_trade_off,
            'CONVENIENCE_DURATION': self._convenience_duration_trade_off
        }
        
        method = trade_off_methods.get(priority_combo)
        if method:
            return method(trips, best_primary_trip, primary_col, second_col)
        else:
            return self._standard_priority_selection(trips, primary_priority, second_priority)
    
    def _duration_cost_trade_off(self, trips, best_duration_trip, duration_col, cost_col):
        """Duration priority with cost secondary: Accept extra time for cost savings."""
        best_duration = best_duration_trip[duration_col]
        best_cost = best_duration_trip[cost_col]
        
        cheaper_trips = trips[trips[cost_col] < best_cost - 5]
        if len(cheaper_trips) == 0:
            return best_duration_trip.to_frame().T
        
        acceptable_trips = self._find_acceptable_duration_cost_trips(
            cheaper_trips, best_cost, best_duration, duration_col, cost_col
        )
        
        if acceptable_trips:
            acceptable_df = pd.DataFrame(acceptable_trips)
            return acceptable_df.loc[acceptable_df[cost_col].idxmin()].to_frame().T
        else:
            return best_duration_trip.to_frame().T
    
    def _cost_duration_trade_off(self, trips, best_cost_trip, cost_col, duration_col):
        """Cost priority with duration secondary: Pay extra for time savings."""
        best_cost = best_cost_trip[cost_col]
        best_duration = best_cost_trip[duration_col]
        
        faster_trips = trips[trips[duration_col] < best_duration - 5]
        if len(faster_trips) == 0:
            return best_cost_trip.to_frame().T
        
        acceptable_trips = self._find_acceptable_cost_duration_trips(
            faster_trips, best_cost, best_duration, cost_col, duration_col
        )
        
        if acceptable_trips:
            acceptable_df = pd.DataFrame(acceptable_trips)
            return acceptable_df.loc[acceptable_df[duration_col].idxmin()].to_frame().T
        else:
            return best_cost_trip.to_frame().T
    
    def _cost_convenience_trade_off(self, trips, best_cost_trip, cost_col, convenience_col):
        """Cost priority with convenience secondary: Pay extra for convenience."""
        best_cost = best_cost_trip[cost_col]
        best_convenience = best_cost_trip[convenience_col]
        
        more_convenient_trips = trips[trips[convenience_col] < best_convenience]
        if len(more_convenient_trips) == 0:
            return best_cost_trip.to_frame().T
        
        acceptable_trips = self._find_acceptable_cost_convenience_trips(
            more_convenient_trips, best_cost, best_convenience, cost_col, convenience_col
        )
        
        if acceptable_trips:
            acceptable_df = pd.DataFrame(acceptable_trips)
            return acceptable_df.loc[acceptable_df[convenience_col].idxmin()].to_frame().T
        else:
            return best_cost_trip.to_frame().T
    
    def _convenience_cost_trade_off(self, trips, best_convenience_trip, convenience_col, cost_col):
        """Convenience priority with cost secondary: Need significant savings to give up convenience."""
        best_convenience = best_convenience_trip[convenience_col]
        best_cost = best_convenience_trip[cost_col]
        
        cheaper_trips = trips[(trips[cost_col] < best_cost - 10) & 
                             (trips[convenience_col] > best_convenience)]
        if len(cheaper_trips) == 0:
            return best_convenience_trip.to_frame().T
        
        acceptable_trips = self._find_acceptable_convenience_cost_trips(
            cheaper_trips, best_cost, best_convenience, cost_col, convenience_col
        )
        
        if acceptable_trips:
            acceptable_df = pd.DataFrame(acceptable_trips)
            return acceptable_df.loc[acceptable_df[cost_col].idxmin()].to_frame().T
        else:
            return best_convenience_trip.to_frame().T
    
    def _convenience_duration_trade_off(self, trips, best_convenience_trip, convenience_col, duration_col):
        """Convenience priority with duration secondary: Need significant time savings to give up convenience."""
        best_convenience = best_convenience_trip[convenience_col]
        best_duration = best_convenience_trip[duration_col]
        
        faster_trips = trips[(trips[duration_col] < best_duration - 15) & 
                            (trips[convenience_col] > best_convenience)]
        if len(faster_trips) == 0:
            return best_convenience_trip.to_frame().T
        
        acceptable_trips = self._find_acceptable_convenience_duration_trips(
            faster_trips, best_duration, best_convenience, duration_col, convenience_col
        )
        
        if acceptable_trips:
            acceptable_df = pd.DataFrame(acceptable_trips)
            return acceptable_df.loc[acceptable_df[duration_col].idxmin()].to_frame().T
        else:
            return best_convenience_trip.to_frame().T
    
    def _find_acceptable_duration_cost_trips(self, trips, best_cost, best_duration, duration_col, cost_col):
        """Find trips with acceptable duration-cost trade-offs."""
        acceptable_trips = []
        thresholds = self.thresholds.THRESHOLDS['DURATION_COST']['time_tolerance']
        
        for _, trip in trips.iterrows():
            cost_savings = best_cost - trip[cost_col]
            extra_time = trip[duration_col] - best_duration
            
            max_acceptable_time = self._get_max_threshold(cost_savings, thresholds)
            
            if extra_time <= max_acceptable_time:
                acceptable_trips.append(trip)
        
        return acceptable_trips
    
    def _find_acceptable_cost_duration_trips(self, trips, best_cost, best_duration, cost_col, duration_col):
        """Find trips with acceptable cost-duration trade-offs."""
        acceptable_trips = []
        thresholds = self.thresholds.THRESHOLDS['COST_DURATION']['cost_tolerance']
        
        for _, trip in trips.iterrows():
            time_savings = best_duration - trip[duration_col]
            extra_cost = trip[cost_col] - best_cost
            
            max_acceptable_cost = self._get_max_threshold(time_savings, thresholds)
            
            if extra_cost <= max_acceptable_cost:
                acceptable_trips.append(trip)
        
        return acceptable_trips
    
    def _find_acceptable_cost_convenience_trips(self, trips, best_cost, best_convenience, cost_col, convenience_col):
        """Find trips with acceptable cost-convenience trade-offs."""
        acceptable_trips = []
        thresholds = self.thresholds.THRESHOLDS['COST_CONVENIENCE']['cost_tolerance']
        
        for _, trip in trips.iterrows():
            convenience_gain = best_convenience - trip[convenience_col]
            extra_cost = trip[cost_col] - best_cost
            
            max_acceptable_cost = self._get_max_threshold(convenience_gain, thresholds)
            
            if extra_cost <= max_acceptable_cost:
                acceptable_trips.append(trip)
        
        return acceptable_trips
    
    def _find_acceptable_convenience_cost_trips(self, trips, best_cost, best_convenience, cost_col, convenience_col):
        """Find trips with acceptable convenience-cost trade-offs."""
        acceptable_trips = []
        thresholds = self.thresholds.THRESHOLDS['CONVENIENCE_COST']['convenience_tolerance']
        
        for _, trip in trips.iterrows():
            cost_savings = best_cost - trip[cost_col]
            convenience_loss = trip[convenience_col] - best_convenience
            
            max_acceptable_loss = self._get_max_threshold(cost_savings, thresholds)
            
            if convenience_loss <= max_acceptable_loss:
                acceptable_trips.append(trip)
        
        return acceptable_trips
    
    def _find_acceptable_convenience_duration_trips(self, trips, best_duration, best_convenience, duration_col, convenience_col):
        """Find trips with acceptable convenience-duration trade-offs."""
        acceptable_trips = []
        thresholds = self.thresholds.THRESHOLDS['CONVENIENCE_DURATION']['convenience_tolerance']
        
        for _, trip in trips.iterrows():
            time_savings = best_duration - trip[duration_col]
            convenience_loss = trip[convenience_col] - best_convenience
            
            max_acceptable_loss = self._get_max_threshold(time_savings, thresholds)
            
            if convenience_loss <= max_acceptable_loss:
                acceptable_trips.append(trip)
        
        return acceptable_trips
    
    def _get_max_threshold(self, value, thresholds):
        """Get maximum acceptable threshold based on value."""
        max_threshold = 0
        for threshold_value in sorted(thresholds.keys()):
            if value >= threshold_value:
                max_threshold = thresholds[threshold_value]
        return max_threshold
    
    def _standard_priority_selection(self, trips, primary_priority, second_priority):
        """Standard priority selection for combinations not covered by survey trade-offs."""
        primary_col = self.constants.PRIORITY_COLUMNS[primary_priority]
        second_col = self.constants.PRIORITY_COLUMNS[second_priority]
        
        sorted_trips = trips.sort_values(
            by=[primary_col, second_col], 
            ascending=[True, True]
        )
        
        return sorted_trips.iloc[0:1]
