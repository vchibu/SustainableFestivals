import requests
from datetime import datetime
import pandas as pd


class OTPTripPlannerClient:
    def __init__(self, base_url="http://localhost:8080/otp/gtfs/v1", headers=None):
        self.url = base_url
        self.headers = headers or {"Content-Type": "application/json"}
        self.results = []

    def build_modes_block(self, direct_mode, transit_modes):
        parts = []

        if isinstance(direct_mode, str) and direct_mode.strip():
            parts.append(f"direct: [{direct_mode.strip()}]")

        if isinstance(transit_modes, list):
            transit_modes_list = [mode.strip() for mode in transit_modes if isinstance(mode, str) and mode.strip()]
            if transit_modes_list:
                transit_modes_formatted = ", ".join([f"{{ mode: {mode} }}" for mode in transit_modes_list])
                parts.append(f"transit: {{ transit: [{transit_modes_formatted}] }}")

        return " ".join(parts)

    def build_query(self, origin_lat, origin_lng, destination_lat, destination_lng, time, modes_block, dep_or_ret):
        if dep_or_ret:
            return f"""
            {{
            planConnection(
                origin: {{ location: {{ coordinate: {{ latitude: {origin_lat}, longitude: {origin_lng} }} }} }}
                destination: {{ location: {{ coordinate: {{ latitude: {destination_lat}, longitude: {destination_lng} }} }} }}
                dateTime: {{ latestArrival: \"{time}\" }}
                modes: {{ {modes_block} }}
                first: 5
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
                    }}
                }}
                }}
            }}
            }}
            """
        else:
            return f"""
            {{
            planConnection(
                origin: {{ location: {{ coordinate: {{ latitude: {origin_lat}, longitude: {origin_lng} }} }} }}
                destination: {{ location: {{ coordinate: {{ latitude: {destination_lat}, longitude: {destination_lng} }} }} }}
                dateTime: {{ earliestDeparture: \"{time}\" }}
                modes: {{ {modes_block} }}
                first: 5
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
                    }}
                }}
                }}
            }}
            }}
            """

    def process_walk_trip(self, trip_data):
        # Store original trip data for comparison
        original_trip_data = trip_data.copy() 

        modified_trip_data = trip_data.copy()
        
        new_total_duration = 0.0
        new_total_length = 0.0
        conversion_failed = False # Flag to track if any conversion failed

        # RESET THE PRINTED LEGS SETS AT THE BEGINNING OF EACH CALL
        # This ensures correct printing for every trip option
        self._printed_legs_original = set() 
        self._printed_legs_modified = set()

        # Determine the maximum leg number dynamically
        max_legs_in_trip = 0
        for key in trip_data.keys():
            if key.startswith("leg") and "_mode" in key:
                try:
                    leg_num = int(key[3:].split('_')[0])
                    if leg_num > max_legs_in_trip:
                        max_legs_in_trip = leg_num
                except ValueError:
                    continue 

        # Iterate through all legs found in the trip data
        for i in range(1, max_legs_in_trip + 1): 
            mode_key = f"leg{i}_mode"
            
            if mode_key not in trip_data:
                continue 

            current_mode = trip_data.get(mode_key)

            if current_mode == "WALK":
                from_lat = trip_data.get(f"leg{i}_from_lat")
                from_lng = trip_data.get(f"leg{i}_from_lng")
                to_lat = trip_data.get(f"leg{i}_to_lat")
                to_lng = trip_data.get(f"leg{i}_to_lng")
                leg_departure_time_str = trip_data.get(f"leg{i}_from_scheduledTime")

                if None in [from_lat, from_lng, to_lat, to_lng, leg_departure_time_str]:
                    print(f"❌ Missing critical data for BICYCLE conversion of leg {i}. Cannot convert this trip.")
                    conversion_failed = True
                    break 
                
                bicycle_modes_block = self.build_modes_block(direct_mode="BICYCLE", transit_modes=[])
                bicycle_query = self.build_query(
                    origin_lat=from_lat,
                    origin_lng=from_lng,
                    destination_lat=to_lat,
                    destination_lng=to_lng,
                    time=leg_departure_time_str, 
                    modes_block=bicycle_modes_block,
                    dep_or_ret=False 
                )

                try:
                    response = requests.post(self.url, json={"query": bicycle_query}, headers=self.headers)
                    bicycle_data = response.json()

                    if "errors" in bicycle_data:
                        print(f"❌ OTP error during BICYCLE sub-query for leg {i}: {bicycle_data['errors']}. Cannot convert this trip.")
                        conversion_failed = True
                        break 
                    else:
                        bicycle_edges = bicycle_data["data"]["planConnection"]["edges"]
                        if bicycle_edges:
                            best_bicycle_leg = bicycle_edges[0]["node"]["legs"][0] 

                            fmt = "%Y-%m-%dT%H:%M:%S%z"
                            try:
                                t1 = datetime.strptime(best_bicycle_leg['from']['departure']['scheduledTime'], fmt)
                                t2 = datetime.strptime(best_bicycle_leg['to']['arrival']['scheduledTime'], fmt)
                                bicycle_duration = (t2 - t1).total_seconds() / 60
                            except Exception:
                                bicycle_duration = 0.0 

                            bicycle_distance = best_bicycle_leg.get("distance", 0.0) / 1000.0

                            # Update the trip data with the new BICYCLE leg details
                            modified_trip_data[f"leg{i}_mode"] = "BICYCLE"
                            modified_trip_data[f"leg{i}_length"] = bicycle_distance
                            modified_trip_data[f"leg{i}_duration"] = bicycle_duration
                            modified_trip_data[f"leg{i}_from_scheduledTime"] = best_bicycle_leg['from']['departure']['scheduledTime']
                            modified_trip_data[f"leg{i}_to_scheduledTime"] = best_bicycle_leg['to']['arrival']['scheduledTime']
                            
                            # Add the new duration/length for this leg
                            new_total_duration += bicycle_duration
                            new_total_length += bicycle_distance
                            print(f"✅ Converted WALK leg {i} to BICYCLE with duration {bicycle_duration:.2f} min and length {bicycle_distance:.2f} km.")
                        else:
                            print(f"❌ No BICYCLE trip found for leg {i} from {from_lat},{from_lng} to {to_lat},{to_lng}. Cannot convert this trip.")
                            conversion_failed = True
                            break 
                except requests.exceptions.RequestException as req_e:
                    print(f"❌ Network error contacting OTP for BICYCLE leg {i}: {req_e}. Cannot convert this trip.")
                    conversion_failed = True
                    break 
                except Exception as e:
                    print(f"❌ Unexpected error during BICYCLE sub-query for leg {i}: {e}. Cannot convert this trip.")
                    conversion_failed = True
                    break 
            else:
                # For non-WALK legs, just add their original duration and length to the new totals
                new_total_duration += trip_data.get(f"leg{i}_duration", 0.0)
                new_total_length += trip_data.get(f"leg{i}_length", 0.0)
        
        modified_trip_data["total_duration"] = new_total_duration
        modified_trip_data["total_length"] = new_total_length

        if conversion_failed:
            print("⚠️ Trip conversion failed. Returning None for this trip option.")
            return None 
        else:
            # The totals are already updated in modified_trip_data, so just return it
            return modified_trip_data
   
    def send_and_process_query(self, query, trip_label=None, identifier=None):
        response = requests.post(self.url, json={"query": query}, headers=self.headers)
        try:
            data = response.json()
            if "errors" in data:
                raise Exception(data["errors"])

            fmt = "%Y-%m-%dT%H:%M:%S%z"

            for edge_index, edge in enumerate(data["data"]["planConnection"]["edges"], 1):
                attendee_id, direction = "unknown", "unknown"
                if identifier and "_" in identifier:
                    parts = identifier.split("_")
                    if len(parts) >= 2:
                        attendee_id = parts[0]
                        direction = parts[1]

                total_duration_minutes = 0.0
                total_distance_km = 0.0
                leg_data = {}
                leg_count = 0

                for i, leg in enumerate(edge["node"]["legs"], 1):
                    mode = leg["mode"]
                    distance_km = leg.get("distance", 0.0) / 1000.0

                    try:
                        t1 = datetime.strptime(leg['from']['departure']['scheduledTime'], fmt)
                        t2 = datetime.strptime(leg['to']['arrival']['scheduledTime'], fmt)
                        duration_minutes = (t2 - t1).total_seconds() / 60
                    except Exception:
                        duration_minutes = 0.0

                    total_duration_minutes += duration_minutes
                    total_distance_km += distance_km

                    leg_data[f"leg{i}_mode"] = mode
                    leg_data[f"leg{i}_length"] = distance_km
                    leg_data[f"leg{i}_duration"] = duration_minutes

                    # Retrieve and store leg coordinates
                    leg_data[f"leg{i}_from_lat"] = leg['from']['lat']
                    leg_data[f"leg{i}_from_lng"] = leg['from']['lon']
                    leg_data[f"leg{i}_to_lat"] = leg['to']['lat']
                    leg_data[f"leg{i}_to_lng"] = leg['to']['lon']

                    # Store scheduled departure/arrival times for each leg
                    leg_data[f"leg{i}_from_scheduledTime"] = leg['from']['departure']['scheduledTime']
                    leg_data[f"leg{i}_to_scheduledTime"] = leg['to']['arrival']['scheduledTime']

                    leg_count = i

                # Assemble final result with edge index (trip_option)
                ordered_trip_data = {
                    "attendee_id": attendee_id,
                    "direction": direction,
                    "trip_option": edge_index
                }

                for i in range(1, leg_count + 1):
                    ordered_trip_data[f"leg{i}_mode"] = leg_data.get(f"leg{i}_mode", "")
                    ordered_trip_data[f"leg{i}_length"] = leg_data.get(f"leg{i}_length", "")
                    ordered_trip_data[f"leg{i}_duration"] = leg_data.get(f"leg{i}_duration", "")
                    ordered_trip_data[f"leg{i}_from_lat"] = leg_data.get(f"leg{i}_from_lat", "") 
                    ordered_trip_data[f"leg{i}_from_lng"] = leg_data.get(f"leg{i}_from_lng", "") 
                    ordered_trip_data[f"leg{i}_to_lat"] = leg_data.get(f"leg{i}_to_lat", "") 
                    ordered_trip_data[f"leg{i}_to_lng"] = leg_data.get(f"leg{i}_to_lng", "") 
                    ordered_trip_data[f"leg{i}_from_scheduledTime"] = leg_data.get(f"leg{i}_from_scheduledTime", "")
                    ordered_trip_data[f"leg{i}_to_scheduledTime"] = leg_data.get(f"leg{i}_to_scheduledTime", "")

                ordered_trip_data["total_duration"] = total_duration_minutes
                ordered_trip_data["total_length"] = total_distance_km

                should_append = True
                walk_trip = False
                if identifier and "BICYCLE" in identifier:
                    for i in range(1, leg_count + 1):
                        if ordered_trip_data.get(f"leg{i}_mode") == "WALK":
                            walk_trip = True    
                            should_append = False 
                            break
                    if walk_trip:
                        print("ℹ️ Trip contains WALK legs, attempting to convert to BICYCLE if possible.")
                        for i in range(1, leg_count + 1):
                            mode = ordered_trip_data.get(f"leg{i}_mode")
                            if mode == "RAIL" or mode == "SUBWAY":
                                should_append = True # Found a RAIL or SUBWAY leg, so we should append
                                break # No need to check further legs for this condition
                        if not should_append:
                            print("❌ Trip contains WALK legs but no RAIL or SUBWAY legs found. Skipping this trip option.")
                    
                if walk_trip and should_append:
                    ordered_trip_data = self.process_walk_trip(ordered_trip_data)
                    if ordered_trip_data == None:
                        should_append = False

                if should_append:
                    self.results.append(ordered_trip_data)         
                
        except Exception as e:
            print(f"❌ Error during {trip_label or 'trip'}: {e}")
            print("Text:", response.text[:500])

    def snap_point_to_road(self, lat, lng, mode="CAR"):
        # Tiny offset to avoid from == to
        offset = 0.0001
        to_lat = lat + offset
        to_lng = lng + offset

        query = f"""
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

    def get_results_dataframe(self):
        if not self.results:
            print("⚠️ No trip results available.")
            return pd.DataFrame()
        return pd.DataFrame(self.results)

    def get_departure_and_return_dataframes(self):
        df = self.get_results_dataframe()
        dep_df = df[df["direction"] == "dep"].reset_index(drop=True)
        ret_df = df[df["direction"] == "ret"].reset_index(drop=True)
        return dep_df, ret_df

    def save_results_split_by_direction(self, departure_file="Data/GeneratedInitialTrips/departure_trips.csv",
                                        return_file="Data/GeneratedInitialTrips/return_trips.csv"):
        if not self.results:
            print("⚠️ No trip results to save.")
            return

        df = pd.DataFrame(self.results)

        # Determine max legs for consistent ordering
        max_legs = max([
            max([int(col[3:].split("_")[0]) for col in row.keys() if col.startswith("leg")], default=0)
            for row in self.results
        ])

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
