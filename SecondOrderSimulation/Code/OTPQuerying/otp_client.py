import requests
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from .query_builder import GraphQLQueryBuilder
from .processors import TripDataProcessor, BicycleConverter
from .validators import TripValidator
from .dataframe_manager import DataFrameManager

class OTPTripPlannerClient:
    """Main client for OpenTripPlanner API interactions."""
    
    def __init__(self, base_url: str = "http://localhost:8080/otp/gtfs/v1", 
                 headers: Optional[Dict[str, str]] = None):
        self.url = base_url
        self.headers = headers or {"Content-Type": "application/json"}
        self.results = []
        
        # Initialize helper classes
        self.query_builder = GraphQLQueryBuilder()
        self.trip_processor = TripDataProcessor(self)
        self.bicycle_converter = BicycleConverter(self, self.query_builder)
        self.dataframe_manager = DataFrameManager()

    def build_modes_block(self, direct_mode: Optional[str], 
                         transit_modes: Optional[List[str]]) -> str:
        """Build modes block for GraphQL queries."""
        return self.query_builder.build_modes_block(direct_mode, transit_modes)

    def build_query(self, origin_lat: float, origin_lng: float, 
                    destination_lat: float, destination_lng: float,
                    time: str, modes_block: str, dep_or_ret: bool,
                    first: int = 1) -> str:
        """Build a trip planning query."""
        return self.query_builder.build_trip_query(
            origin_lat, origin_lng, destination_lat, destination_lng,
            time, modes_block, is_arrival_time=dep_or_ret, first=first
        )


    def process_walk_trip(self, trip_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert walking legs to bicycle legs in a trip."""
        return self.bicycle_converter.convert_walk_legs_to_bicycle(trip_data)

    def send_and_process_query(
        self,
        query: str,
        trip_label: Optional[str] = None,
        identifier: Optional[str] = None,
        target_trip_option: Optional[int] = None
        ) -> None:

        """Send a query to the OTP API and process the results."""
        try:
            response = requests.post(self.url, json={"query": query}, headers=self.headers)
            data = response.json()
            
            if "errors" in data:
                raise Exception(data["errors"])

            self._process_response_data(data, identifier, target_trip_option)
            
        except Exception as e:
            print(f"❌ Error during {trip_label or 'trip'}: {e}")
            print("Text:", response.text[:500])

    def _process_response_data(
        self,
        data: Dict[str, Any],
        identifier: Optional[str],
        target_trip_option: Optional[int] = None,
        ) -> None:

        """Process the response data from the OTP API."""
        edges = data["data"]["planConnection"]["edges"]

        for edge_index, edge in enumerate(edges, 1):
            if target_trip_option is not None and edge_index != target_trip_option:
                continue

            trip_data = self.trip_processor.process_trip_edge(edge, edge_index, identifier)
            should_append, needs_conversion = TripValidator.should_process_trip(trip_data, identifier)

            if needs_conversion:
                trip_data = self.process_walk_trip(trip_data)
                if trip_data is None:
                    should_append = False

            if should_append:
                self.results.append(trip_data)  


    def snap_point_to_road(self, lat: float, lng: float, mode: str = "CAR") -> Tuple[float, float, bool]:
        """Snap a point to the road network."""
        query = self.query_builder.build_snapping_query(lat, lng, mode)
        
        try:
            response = requests.post(self.url, json={"query": query}, headers=self.headers)
            data = response.json()
            edges = data.get("data", {}).get("planConnection", {}).get("edges", [])

            if edges and edges[0]["node"]["legs"]:
                snapped = edges[0]["node"]["legs"][0]["from"]
                print(f"✅ Snapped point ({lat}, {lng}) to ({snapped['lat']}, {snapped['lon']})")
                return snapped["lat"], snapped["lon"], True
            else:
                print(f"❌ Snapping failed for ({lat}, {lng})")
                return lat, lng, False

        except Exception as e:
            print(f"❌ Error during snapping: {e}")
            return lat, lng, False

    def get_results_dataframe(self) -> pd.DataFrame:
        """Get all results as a pandas DataFrame."""
        return self.dataframe_manager.create_results_dataframe(self.results)

    def get_departure_and_return_dataframes(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Get separate DataFrames for departure and return trips."""
        df = self.get_results_dataframe()
        return self.dataframe_manager.split_by_direction(df)

    def save_results_split_by_direction(self, 
                                      departure_file: str = "Data/GeneratedInitialTrips/departure_trips.csv",
                                      return_file: str = "Data/GeneratedInitialTrips/return_trips.csv") -> None:
        """Save results to separate CSV files for departure and return trips."""
        if not self.results:
            print("⚠️ No trip results to save.")
            return

        dep_df, ret_df = self.dataframe_manager.prepare_for_export(self.results)

        if not dep_df.empty:
            dep_df.to_csv(departure_file, index=False)
            print(f"📁 Saved departure trips to {departure_file}")
        else:
            print("⚠️ No departure trips found.")

        if not ret_df.empty:
            ret_df.to_csv(return_file, index=False)
            print(f"📁 Saved return trips to {return_file}")
        else:
            print("⚠️ No return trips found.")