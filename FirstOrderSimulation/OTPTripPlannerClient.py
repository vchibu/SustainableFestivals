import requests
from datetime import datetime
import csv
import pandas as pd
import random


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

    def build_query(self, origin_lat, origin_lng, destination_lat, destination_lng, time, modes_block):
        return f"""
        {{
          planConnection(
            origin: {{ location: {{ coordinate: {{ latitude: {origin_lat}, longitude: {origin_lng} }} }} }}
            destination: {{ location: {{ coordinate: {{ latitude: {destination_lat}, longitude: {destination_lng} }} }} }}
            dateTime: {{ earliestDeparture: \"{time}\" }}
            modes: {{ {modes_block} }}
            first: 1
          ) {{
            edges {{
              node {{
                legs {{
                  mode
                  distance
                  from {{
                    name
                    departure {{ scheduledTime }}
                  }}
                  to {{
                    name
                    arrival {{ scheduledTime }}
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

    def send_and_process_query(self, query, trip_label=None, identifier=None):
        response = requests.post(self.url, json={"query": query}, headers=self.headers)
        try:
            data = response.json()
            if "errors" in data:
                raise Exception(data["errors"])

            fmt = "%Y-%m-%dT%H:%M:%S%z"

            for edge in data["data"]["planConnection"]["edges"]:
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
                    leg_count = i

                # Assemble final result in correct column order
                ordered_trip_data = {
                    "identifier": identifier,
                    "attendee_id": attendee_id,
                    "direction": direction
                }

                for i in range(1, leg_count + 1):
                    ordered_trip_data[f"leg{i}_mode"] = leg_data.get(f"leg{i}_mode", "")
                    ordered_trip_data[f"leg{i}_length"] = leg_data.get(f"leg{i}_length", "")
                    ordered_trip_data[f"leg{i}_duration"] = leg_data.get(f"leg{i}_duration", "")

                ordered_trip_data["total_duration"] = total_duration_minutes
                ordered_trip_data["total_length"] = total_distance_km
                ordered_trip_data["total_carbon_footprint"] = 0

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

    def save_results_split_by_direction(self, departure_file="generated_data/departure_trips.csv",
                                        return_file="generated_data/return_trips.csv"):
        if not self.results:
            print("⚠️ No trip results to save.")
            return

        df = pd.DataFrame(self.results)

        # Determine max legs for consistent ordering
        max_legs = max([
            max([int(col[3:].split("_")[0]) for col in row.keys() if col.startswith("leg")], default=0)
            for row in self.results
        ])

        base_cols = ["identifier", "attendee_id", "direction"]
        leg_cols = [
            f"leg{i}_{field}"
            for i in range(1, max_legs + 1)
            for field in ["mode", "length", "duration"]
        ]
        summary_cols = ["total_duration", "total_length", "total_carbon_footprint"]
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

