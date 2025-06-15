class LegCalculator:

    def _calculate_leg_count(self, df):
        """
        Calculate the number of valid legs for each row and add 'leg_count' column.
        A leg is valid if mode, length, and duration are all non-null.

        Parameters:
        df (DataFrame): DataFrame including leg columns.

        Returns:
        DataFrame: DataFrame with added 'leg_count' column.
        """
        # Detect all legs by their shared prefixes
        leg_prefixes = sorted(set(col.rsplit('_', 1)[0] for col in df.columns if col.startswith("leg") and col.endswith("_mode")))

        # For each leg, check if mode, length, and duration are all present
        leg_complete_flags = []
        for prefix in leg_prefixes:
            mode_col = f"{prefix}_mode"
            length_col = f"{prefix}_length"
            duration_col = f"{prefix}_duration"
            leg_is_valid = df[[mode_col, length_col, duration_col]].notna().all(axis=1)
            leg_complete_flags.append(leg_is_valid)

        # Sum up the number of valid legs per row and add to dataframe
        df['leg_count'] = sum(leg_complete_flags)
        return df

    def select_least_leg_options(self, df):
        """
        For each attendee, select the trip option with the least number of legs.
        A leg is only counted if mode, length, and duration are all non-null.
        If multiple options have the same number of legs, choose the one with the lowest carbon footprint.

        Parameters:
        df (DataFrame): DataFrame including leg columns and carbon footprint.

        Returns:
        DataFrame: Filtered DataFrame with one best option per attendee.
        """
        # Calculate the number of valid legs per row and add to dataframe
        df = self._calculate_leg_count(df)

        # Sort by attendee, leg_count, and carbon footprint
        df_sorted = df.sort_values(by=['attendee_id', 'leg_count', 'calculated_total_carbon_footprint'])

        # Select one row per attendee
        least_leg_options = df_sorted.drop_duplicates(subset='attendee_id', keep='first')

        return least_leg_options