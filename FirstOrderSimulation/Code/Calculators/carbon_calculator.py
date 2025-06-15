import pandas as pd
import re

class CarbonCalculator:

    emissions_factors = {
        "CAR": 191,  # gCO2/km
        "BUS": 92,  # gCO2/km
        "RAIL": 3,  # gCO2/km
        "WALK": 0, # gCO2/km
        "BICYCLE": 0, # gCO2/km
        "SUBWAY": 56, # gCO2/km
        "TRAM": 56 # gCO2/km
    }

    def compute_trip_emission(self, mode: str, distance_km: float) -> float:
        """Compute CO2 emission for a single trip."""
        factor = self.emissions_factors.get(mode.upper(), 0.0)
        return distance_km * factor

    def compute_dataframe_emissions(self, df, mode_column="mode", distance_column="distance_km") -> pd.Series:
        """Return a pandas Series with emissions per row in gCO2."""
        return df.apply(
            lambda row: self.compute_trip_emission(row[mode_column], row[distance_column]),
            axis=1
        )

    def annotate_dataframe(self, df, mode_column="mode", distance_column="distance_km") -> pd.DataFrame:
        """Return a copy of the dataframe with a new carbon_gCO2 column."""
        df = df.copy()
        df["carbon_gCO2"] = self.compute_dataframe_emissions(df, mode_column, distance_column)
        return df
        
    def process_multi_leg_trips(self, df):
        """
        Process CSV data with multiple legs per trip.
        Adds carbon emissions for each leg and calculates total_carbon_footprint.
        """
        df = df.copy()
        
        # Find all leg columns (mode and length)
        leg_mode_cols = [col for col in df.columns if re.match(r'leg\d+_mode', col)]
        leg_length_cols = [col for col in df.columns if re.match(r'leg\d+_length', col)]
        
        # Add carbon footprint columns for each leg
        for i, (mode_col, length_col) in enumerate(zip(leg_mode_cols, leg_length_cols), 1):
            carbon_col = f'leg{i}_carbon'
            df[carbon_col] = df.apply(
                lambda row: self.compute_trip_emission(
                    row[mode_col], 
                    row[length_col]
                ) if pd.notna(row[mode_col]) and pd.notna(row[length_col]) else 0.0,
                axis=1
            )
        
        # Calculate total carbon footprint
        carbon_cols = [col for col in df.columns if re.match(r'leg\d+_carbon', col)]
        df['calculated_total_carbon_footprint'] = df[carbon_cols].sum(axis=1)
        
        return df
        
    def select_lowest_carbon_options(self, df):
        """
        For each attendee, select the trip option with the lowest carbon footprint.
        If multiple options have the same footprint, select the one with the shortest total duration.
        
        Parameters:
        df (DataFrame): DataFrame with calculated carbon footprints
        
        Returns:
        DataFrame: A new DataFrame containing only the lowest carbon option for each attendee
        """
        if 'calculated_total_carbon_footprint' not in df.columns:
            df = self.process_multi_leg_trips(df)

        # Sort first by carbon footprint, then by total duration
        df_sorted = df.sort_values(by=['attendee_id', 'calculated_total_carbon_footprint', 'total_duration'])

        # Drop duplicates, keeping the first (lowest carbon, then shortest duration)
        lowest_carbon_options = df_sorted.drop_duplicates(subset=['attendee_id'], keep='first')

        return lowest_carbon_options

        