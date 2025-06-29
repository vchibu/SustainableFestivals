from typing import List, Optional

class GraphQLQueryBuilder:
    """Handles building GraphQL queries for the OTP API."""
    
    @staticmethod
    def build_modes_block(direct_mode: Optional[str], transit_modes: Optional[List[str]]) -> str:
        """Build the modes block for GraphQL queries."""
        parts = []

        if isinstance(direct_mode, str) and direct_mode.strip():
            parts.append(f"direct: [{direct_mode.strip()}]")

        if isinstance(transit_modes, list):
            transit_modes_list = [
                mode.strip() for mode in transit_modes 
                if isinstance(mode, str) and mode.strip()
            ]
            if transit_modes_list:
                transit_modes_formatted = ", ".join([
                    f"{{ mode: {mode} }}" for mode in transit_modes_list
                ])
                parts.append(f"transit: {{ transit: [{transit_modes_formatted}] }}")

        return " ".join(parts)

    @staticmethod
    def build_trip_query(origin_lat: float, origin_lng: float, 
                        destination_lat: float, destination_lng: float, time: str,
                        modes_block: str, is_arrival_time: bool = False, first: int = 1) -> str:
        """Build a complete trip planning query."""
        time_field = "latestArrival" if is_arrival_time else "earliestDeparture"
        
        return f"""
        {{
        planConnection(
            origin: {{ location: {{ coordinate: {{ latitude: {origin_lat}, longitude: {origin_lng} }} }} }}
            destination: {{ location: {{ coordinate: {{ latitude: {destination_lat}, longitude: {destination_lng} }} }} }}
            dateTime: {{ {time_field}: \"{time}\" }}
            modes: {{ {modes_block} }}
            first: {first}
        ) {{
            edges {{
            node {{
                legs {{
                mode
                distance
                from {{
                    name
                    departure {{ scheduledTime }}
                    lat
                    lon
                }}
                to {{
                    name
                    arrival {{ scheduledTime }}
                    lat
                    lon
                }}
                route {{
                    shortName
                    longName
                }}
                steps {{
                    streetName
                }}
                }}
            }}
            }}
        }}
        }}
        """

    @staticmethod
    def build_snapping_query(lat: float, lng: float, mode: str = "CAR") -> str:
        """Build a query for snapping a point to the road network."""
        offset = 0.0001
        to_lat = lat + offset
        to_lng = lng + offset

        return f"""
        {{
        planConnection(
            origin: {{ location: {{ coordinate: {{ latitude: {lat}, longitude: {lng} }} }} }}
            destination: {{ location: {{ coordinate: {{ latitude: {to_lat}, longitude: {to_lng} }} }} }}
            dateTime: {{ earliestDeparture: "2025-05-17T12:00:00+0200" }}
            modes: {{ direct: [{mode}] }}
            first: 1
        ) {{
            edges {{
            node {{
                legs {{
                from {{ lat lon }}
                }}
            }}
            }}
        }}
        }}
        """
