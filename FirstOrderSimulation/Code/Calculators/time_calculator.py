class TimeCalculator:
        
    def select_lowest_time_options(self, df):
        """
        For each attendee, select the trip option with the lowest total duration.
        If multiple options have the duration, select the one with the lowest carbon footprint.
        
        Parameters:
        df (DataFrame): DataFrame with calculated total durations and carbon footprints.
        
        Returns:
        DataFrame: A new DataFrame containing only the lowest total duration soption for each attendee
        """

        # Sort first by total trip duration footprint, then by carbon footprint
        df_sorted = df.sort_values(by=['attendee_id', 'total_duration', 'calculated_total_carbon_footprint'])

        # Drop duplicates, keeping the first (lowest carbon, then shortest duration)
        lowest_time_options = df_sorted.drop_duplicates(subset=['attendee_id'], keep='first')

        return lowest_time_options

        