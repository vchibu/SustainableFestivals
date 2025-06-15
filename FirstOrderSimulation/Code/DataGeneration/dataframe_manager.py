from typing import List, Dict, Any, Tuple
import pandas as pd

class DataFrameManager:
    """Handles creation and management of pandas DataFrames for trip results."""
    
    @staticmethod
    def create_results_dataframe(results: List[Dict[str, Any]]) -> pd.DataFrame:
        """Create a DataFrame from trip results."""
        if not results:
            print("⚠️ No trip results available.")
            return pd.DataFrame()
        return pd.DataFrame(results)

    @staticmethod
    def split_by_direction(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Split DataFrame into departure and return trips."""
        dep_df = df[df["direction"] == "dep"].reset_index(drop=True)
        ret_df = df[df["direction"] == "ret"].reset_index(drop=True)
        return dep_df, ret_df

    @staticmethod
    def prepare_for_export(results: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepare DataFrames for CSV export with consistent column ordering."""
        if not results:
            return pd.DataFrame(), pd.DataFrame()
            
        df = pd.DataFrame(results)
        
        # Determine max legs for consistent ordering
        max_legs = max([
            max([int(col[3:].split("_")[0]) for col in row.keys() if col.startswith("leg")], default=0)
            for row in results
        ])

        # Define column order
        base_cols = ["attendee_id", "direction", "trip_option"]
        leg_cols = [
            f"leg{i}_{field}"
            for i in range(1, max_legs + 1)
            for field in ["mode", "length", "duration"]
        ]
        summary_cols = ["total_duration", "total_length"]
        all_columns = base_cols + leg_cols + summary_cols

        # Split and reindex
        dep_df = df[df["direction"] == "dep"].reindex(columns=all_columns).reset_index(drop=True)
        ret_df = df[df["direction"] == "ret"].reindex(columns=all_columns).reset_index(drop=True)
        
        return dep_df, ret_df

