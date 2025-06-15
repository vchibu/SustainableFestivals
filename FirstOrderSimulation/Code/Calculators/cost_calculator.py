import pandas as pd
import re

class CostCalculator:

    cost_factors = {
        "CAR": 0.23,      # euros/km (standard tax-free reimbursement rate)
        "BUS": 0.19,    # euros/km (OV-chipkaart usage, adult fare per km)
        "RAIL": 0.26,     # euros/km (NS base + per km, typical for mid-range trips)
        "WALK": 0.00,     # euros/km (no cost)
        "BICYCLE": 0,  # euros/km (maintenance, depreciation)
        "SUBWAY": 0.19,  # euros/km (GVB metro fare same as bus/tram)
        "TRAM": 0.19     # euros/km (same fare model as bus/subway)
    }


    def compute_trip_cost(self, mode: str, distance_km: float) -> float:
        """Compute costs in euros for a single trip."""
        factor = self.cost_factors.get(mode.upper(), 0.0)
        return distance_km * factor

    def compute_dataframe_costs(self, df, mode_column="mode", distance_column="distance_km") -> pd.Series:
        """Return a pandas Series with costs per row in euros."""
        return df.apply(
            lambda row: self.compute_trip_cost(row[mode_column], row[distance_column]),
            axis=1
        )

    def annotate_dataframe(self, df, mode_column="mode", distance_column="distance_km") -> pd.DataFrame:
        """Return a copy of the dataframe with a new cost column."""
        df = df.copy()
        df["Cost (€)"] = self.compute_dataframe_costs(df, mode_column, distance_column)
        return df
        
    def process_multi_leg_trips(self, df):
        """
        Process CSV data with multiple legs per trip.
        Adds costs for each leg and calculates total cost.
        """
        df = df.copy()
        
        # Find all leg columns (mode and length)
        leg_mode_cols = [col for col in df.columns if re.match(r'leg\d+_mode', col)]
        leg_length_cols = [col for col in df.columns if re.match(r'leg\d+_length', col)]
        
        # Add cost columns for each leg
        for i, (mode_col, length_col) in enumerate(zip(leg_mode_cols, leg_length_cols), 1):
            cost_col = f'leg{i}_cost'
            df[cost_col] = df.apply(
                lambda row: self.compute_trip_cost(
                    row[mode_col], 
                    row[length_col]
                ) if pd.notna(row[mode_col]) and pd.notna(row[length_col]) else 0.0,
                axis=1
            )
        
        # Calculate total carbon footprint
        cost_cols = [col for col in df.columns if re.match(r'leg\d+_cost', col)]
        df['calculated_total_cost'] = df[cost_cols].sum(axis=1)
        
        return df
        
    def select_lowest_cost_options(self, df):
        """
        For each attendee, select the trip option with the lowest cost.
        If multiple options have the same cost, select the one with the lowest carbon footprint.
        
        Parameters:
        df (DataFrame): DataFrame with calculated costs and carbon footprints.
        
        Returns:
        DataFrame: A new DataFrame containing only the lowest cost options for each attendee
        """
        if 'calculated_total_cost' not in df.columns:
            df = self.process_multi_leg_trips(df)

        # Sort first by total cost, then by carbon footprint
        df_sorted = df.sort_values(by=['attendee_id', 'calculated_total_cost', 'calculated_total_carbon_footprint'])

        # Drop duplicates, keeping the first (lowest carbon, then shortest duration)
        lowest_cost_options = df_sorted.drop_duplicates(subset=['attendee_id'], keep='first')

        return lowest_cost_options

        