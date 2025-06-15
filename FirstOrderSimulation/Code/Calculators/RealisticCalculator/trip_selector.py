from Code.Calculators.RealisticCalculator.trade_off_analyzer import TradeOffAnalyzer
import pandas as pd

class TripSelector:
    """Selects optimal trips for attendees based on their priorities."""
    
    def __init__(self):
        self.trade_off_analyzer = TradeOffAnalyzer()
    
    def select_optimal_trips_per_attendee(self, df):
        """Selects the most optimal trip for each attendee."""
        best_trips = []
        
        for attendee_id in df['attendee_id'].unique():
            attendee_trips = df[df['attendee_id'] == attendee_id].copy()
            
            if len(attendee_trips) == 0:
                continue
            
            primary_priority = attendee_trips['priority'].iloc[0]
            second_priority = attendee_trips['second_priority'].iloc[0]
            
            best_trip = self.trade_off_analyzer.apply_trade_off_logic(
                attendee_trips, primary_priority, second_priority
            )
            
            best_trips.append(best_trip)
        
        if best_trips:
            result = pd.concat(best_trips, ignore_index=True)
        else:
            result = df.iloc[0:0].copy()
            
        return result

