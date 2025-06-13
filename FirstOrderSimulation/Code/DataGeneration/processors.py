from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from .query_builder import GraphQLQueryBuilder
import requests

class TripDataProcessor:
    """Handles processing and conversion of trip data."""
    
    def __init__(self, api_client):
        self.api_client = api_client
        self.time_format = "%Y-%m-%dT%H:%M:%S%z"

    def calculate_leg_duration(self, departure_time: str, arrival_time: str) -> float:
        """Calculate duration between two times in minutes."""
        try:
            t1 = datetime.strptime(departure_time, self.time_format)
            t2 = datetime.strptime(arrival_time, self.time_format)
            return (t2 - t1).total_seconds() / 60
        except Exception:
            return 0.0

    def extract_leg_data(self, leg: Dict[str, Any], leg_number: int) -> Dict[str, Any]:
        """Extract data from a single leg of a trip."""
        mode = leg["mode"]
        distance_km = leg.get("distance", 0.0) / 1000.0
        duration_minutes = self.calculate_leg_duration(
            leg['from']['departure']['scheduledTime'],
            leg['to']['arrival']['scheduledTime']
        )

        return {
            f"leg{leg_number}_mode": mode,
            f"leg{leg_number}_length": distance_km,
            f"leg{leg_number}_duration": duration_minutes,
            f"leg{leg_number}_from_lat": leg['from']['lat'],
            f"leg{leg_number}_from_lng": leg['from']['lon'],
            f"leg{leg_number}_to_lat": leg['to']['lat'],
            f"leg{leg_number}_to_lng": leg['to']['lon'],
            f"leg{leg_number}_from_scheduledTime": leg['from']['departure']['scheduledTime'],
            f"leg{leg_number}_to_scheduledTime": leg['to']['arrival']['scheduledTime'],
        }

    def process_trip_edge(self, edge: Dict[str, Any], edge_index: int, identifier: str) -> Dict[str, Any]:
        """Process a single trip edge into structured data."""
        attendee_id, direction = self._parse_identifier(identifier)
        
        total_duration_minutes = 0.0
        total_distance_km = 0.0
        trip_data = {
            "attendee_id": attendee_id,
            "direction": direction,
            "trip_option": edge_index
        }

        for i, leg in enumerate(edge["node"]["legs"], 1):
            leg_data = self.extract_leg_data(leg, i)
            trip_data.update(leg_data)
            
            total_duration_minutes += leg_data[f"leg{i}_duration"]
            total_distance_km += leg_data[f"leg{i}_length"]

        trip_data["total_duration"] = total_duration_minutes
        trip_data["total_length"] = total_distance_km
        
        return trip_data

    def _parse_identifier(self, identifier: str) -> Tuple[str, str]:
        """Parse attendee ID and direction from identifier."""
        if identifier and "_" in identifier:
            parts = identifier.split("_")
            if len(parts) >= 2:
                return parts[0], parts[1]
        return "unknown", "unknown"


class BicycleConverter:
    """Handles conversion of walking legs to bicycle legs."""
    
    def __init__(self, api_client, query_builder: GraphQLQueryBuilder):
        self.api_client = api_client
        self.query_builder = query_builder
        self.time_format = "%Y-%m-%dT%H:%M:%S%z"

    def convert_walk_legs_to_bicycle(self, trip_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert all walking legs in a trip to bicycle legs."""
        modified_trip_data = trip_data.copy()
        new_total_duration = 0.0
        new_total_length = 0.0
        
        max_legs = self._find_max_legs(trip_data)
        
        for leg_num in range(1, max_legs + 1):
            mode_key = f"leg{leg_num}_mode"
            
            if mode_key not in trip_data:
                continue
                
            current_mode = trip_data.get(mode_key)
            
            if current_mode == "WALK":
                bicycle_leg_data = self._convert_single_walk_leg(trip_data, leg_num)
                if bicycle_leg_data is None:
                    print(f"⚠️ Trip conversion failed at leg {leg_num}. Returning None.")
                    return None
                    
                # Update the trip data with bicycle leg
                self._update_leg_data(modified_trip_data, leg_num, bicycle_leg_data)
                new_total_duration += bicycle_leg_data['duration']
                new_total_length += bicycle_leg_data['distance']
                
                print(f"✅ Converted WALK leg {leg_num} to BICYCLE with duration "
                      f"{bicycle_leg_data['duration']:.2f} min and length "
                      f"{bicycle_leg_data['distance']:.2f} km.")
            else:
                # Keep original leg data
                new_total_duration += trip_data.get(f"leg{leg_num}_duration", 0.0)
                new_total_length += trip_data.get(f"leg{leg_num}_length", 0.0)
        
        modified_trip_data["total_duration"] = new_total_duration
        modified_trip_data["total_length"] = new_total_length
        
        return modified_trip_data

    def _find_max_legs(self, trip_data: Dict[str, Any]) -> int:
        """Find the maximum leg number in the trip data."""
        max_legs = 0
        for key in trip_data.keys():
            if key.startswith("leg") and "_mode" in key:
                try:
                    leg_num = int(key[3:].split('_')[0])
                    max_legs = max(max_legs, leg_num)
                except ValueError:
                    continue
        return max_legs

    def _convert_single_walk_leg(self, trip_data: Dict[str, Any], leg_num: int) -> Optional[Dict[str, Any]]:
        """Convert a single walking leg to bicycle."""
        required_keys = [
            f"leg{leg_num}_from_lat", f"leg{leg_num}_from_lng",
            f"leg{leg_num}_to_lat", f"leg{leg_num}_to_lng",
            f"leg{leg_num}_from_scheduledTime"
        ]
        
        # Check if all required data is available
        for key in required_keys:
            if trip_data.get(key) is None:
                print(f"❌ Missing critical data for BICYCLE conversion of leg {leg_num}. "
                      f"Missing: {key}")
                return None
        
        # Build bicycle query
        bicycle_modes_block = self.query_builder.build_modes_block(
            direct_mode="BICYCLE", transit_modes=[]
        )
        bicycle_query = self.query_builder.build_trip_query(
            origin_lat=trip_data[f"leg{leg_num}_from_lat"],
            origin_lng=trip_data[f"leg{leg_num}_from_lng"],
            destination_lat=trip_data[f"leg{leg_num}_to_lat"],
            destination_lng=trip_data[f"leg{leg_num}_to_lng"],
            time=trip_data[f"leg{leg_num}_from_scheduledTime"],
            modes_block=bicycle_modes_block,
            is_arrival_time=False
        )
        
        try:
            response = requests.post(
                self.api_client.url, 
                json={"query": bicycle_query}, 
                headers=self.api_client.headers
            )
            bicycle_data = response.json()
            
            if "errors" in bicycle_data:
                print(f"❌ OTP error during BICYCLE sub-query for leg {leg_num}: "
                      f"{bicycle_data['errors']}")
                return None
                
            bicycle_edges = bicycle_data["data"]["planConnection"]["edges"]
            if not bicycle_edges:
                print(f"❌ No BICYCLE trip found for leg {leg_num}")
                return None
                
            best_bicycle_leg = bicycle_edges[0]["node"]["legs"][0]
            
            # Calculate bicycle leg metrics
            duration = self._calculate_duration(
                best_bicycle_leg['from']['departure']['scheduledTime'],
                best_bicycle_leg['to']['arrival']['scheduledTime']
            )
            distance = best_bicycle_leg.get("distance", 0.0) / 1000.0
            
            return {
                'duration': duration,
                'distance': distance,
                'from_time': best_bicycle_leg['from']['departure']['scheduledTime'],
                'to_time': best_bicycle_leg['to']['arrival']['scheduledTime']
            }
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error contacting OTP for BICYCLE leg {leg_num}: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error during BICYCLE sub-query for leg {leg_num}: {e}")
            return None

    def _calculate_duration(self, departure_time: str, arrival_time: str) -> float:
        """Calculate duration between two times in minutes."""
        try:
            t1 = datetime.strptime(departure_time, self.time_format)
            t2 = datetime.strptime(arrival_time, self.time_format)
            return (t2 - t1).total_seconds() / 60
        except Exception:
            return 0.0

    def _update_leg_data(self, trip_data: Dict[str, Any], leg_num: int, 
                        bicycle_data: Dict[str, Any]) -> None:
        """Update trip data with bicycle leg information."""
        trip_data[f"leg{leg_num}_mode"] = "BICYCLE"
        trip_data[f"leg{leg_num}_length"] = bicycle_data['distance']
        trip_data[f"leg{leg_num}_duration"] = bicycle_data['duration']
        trip_data[f"leg{leg_num}_from_scheduledTime"] = bicycle_data['from_time']
        trip_data[f"leg{leg_num}_to_scheduledTime"] = bicycle_data['to_time']