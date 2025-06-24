from typing import Dict, Any, Tuple

class TripValidator:
    """Handles validation of trip data based on various criteria."""
    
    @staticmethod
    def should_process_trip(trip_data: Dict[str, Any], identifier: str) -> Tuple[bool, bool]:
        """
        Determine if a trip should be processed based on identifier and content.
        
        Returns:
            Tuple[bool, bool]: (should_append, needs_walk_conversion)
        """
        if not identifier or "BICYCLE" not in identifier:
            return True, False
            
        # Check for walk legs
        has_walk_legs = TripValidator._has_walk_legs(trip_data)
        if not has_walk_legs:
            return True, False
            
        print("ℹ️ Trip contains WALK legs, attempting to convert to BICYCLE if possible.")
        
        # Check for rail/subway legs
        has_rail_or_subway = TripValidator._has_rail_or_subway_legs(trip_data)
        if not has_rail_or_subway:
            print("❌ Trip contains WALK legs but no RAIL or SUBWAY legs found. "
                  "Skipping this trip option.")
            return False, False
            
        return True, True

    @staticmethod
    def _has_walk_legs(trip_data: Dict[str, Any]) -> bool:
        """Check if trip contains any walking legs."""
        for key, value in trip_data.items():
            if key.endswith("_mode") and value == "WALK":
                return True
        return False

    @staticmethod
    def _has_rail_or_subway_legs(trip_data: Dict[str, Any]) -> bool:
        """Check if trip contains rail or subway legs."""
        for key, value in trip_data.items():
            if key.endswith("_mode") and value in ["RAIL", "SUBWAY"]:
                return True
        return False
