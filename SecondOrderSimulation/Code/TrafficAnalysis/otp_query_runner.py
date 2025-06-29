import pandas as pd
from pathlib import Path
from collections import Counter
from OTPQuerying.otp_client import OTPTripPlannerClient

class TripRequeryAnalyzer:

    def __init__(self):
        self.current_dir = Path(__file__).resolve().parent.parent.parent
        self.otp = OTPTripPlannerClient(base_url="http://localhost:8080/otp/gtfs/v1")

        # Load datasets
        self.trip_path_dep = self.current_dir.parent / "FirstOrderSimulation" / "Data" / "ChosenTrips" / "realistic_departure.csv"
        self.trip_path_ret = self.current_dir.parent / "FirstOrderSimulation" / "Data" / "ChosenTrips" / "realistic_return.csv"
        self.attendee_data_path = self.current_dir.parent / "FirstOrderSimulation" / "Data" / "AttendeeData" / "attendee_data.csv"

        self.output_dir = self.current_dir / "Data"
        self.output_dir.mkdir(parents=True, exist_ok=True)  

        self.trips_dep_df = pd.read_csv(self.trip_path_dep)
        self.trips_ret_df = pd.read_csv(self.trip_path_ret)
        self.od_df = pd.read_csv(self.attendee_data_path)

    def classify_modes(self, df: pd.DataFrame) -> pd.DataFrame:
        def contains_mode(row, mode):
            return any(str(row.get(f"leg{i}_mode", "")).strip().upper() == mode for i in range(1, 16))

        df["has_car_leg"] = df.apply(lambda r: contains_mode(r, "CAR"), axis=1)
        df["has_walk_leg"] = df.apply(lambda r: contains_mode(r, "WALK"), axis=1)
        df["has_bicycle_leg"] = df.apply(lambda r: contains_mode(r, "BICYCLE"), axis=1)

        def get_category(row):
            tags = []
            if row["has_car_leg"]: tags.append("CAR")
            if row["has_walk_leg"]: tags.append("WALK")
            if row["has_bicycle_leg"]: tags.append("BICYCLE")
            return "+".join(tags) if tags else "OTHER"

        df["trip_mode_category"] = df.apply(get_category, axis=1)
        return df

    def requery_trips(self, df: pd.DataFrame, label: str, mode: str, transit_modes: list):
        df = df[df[f"has_{mode.lower()}_leg"]]
        print(f"🔁 Found {len(df)} {label} trips with {mode} legs.")

        for _, row in df.iterrows():
            attendee_id = row["attendee_id"]
            identifier = f"{attendee_id}_{label}"
            od_match = self.od_df[self.od_df["attendee_id"] == attendee_id]
            filtered = od_match[od_match["direction"] == label]
            if filtered.empty:
                print(f"No matching direction '{label}' found.")
                od_match = pd.Series()
            else:
                od_match = filtered.iloc[0]


            if od_match.empty:
                print(f"⚠️ No OD match for {identifier}")
                continue

            # Get trip_option from realistic trips (departure or return)
            trip_row_source = self.trips_dep_df if label == "departure" else self.trips_ret_df
            trip_match = trip_row_source[
                (trip_row_source["attendee_id"] == attendee_id) &
                (trip_row_source[f"has_{mode.lower()}_leg"])
            ]

            if trip_match.empty:
                print(f"⚠️ No trip_option found for {identifier}")
                continue

            try:
                trip_option = int(trip_match.iloc[0]["trip_option"])
            except Exception as e:
                print(f"⚠️ Invalid trip_option for {identifier}: {e}")
                continue

            
            modes_block = self.otp.build_modes_block(direct_mode=mode, transit_modes=transit_modes)

            if label == "departure":
                dep_or_ret = True
            else:
                dep_or_ret = False


            query = self.otp.build_query(
                origin_lat=od_match["origin_lat"],
                origin_lng=od_match["origin_lng"],
                destination_lat=od_match["destination_lat"],
                destination_lng=od_match["destination_lng"],
                time=od_match["departure_time"],
                modes_block=modes_block,
                dep_or_ret=dep_or_ret,
                first=trip_option  
            )

            print(f"🛰️ Querying {mode} trip: {identifier} (trip option {trip_option})")

            self.otp.send_and_process_query(
                query,
                trip_label=f"{mode}_{label}",
                identifier=identifier,
                target_trip_option=trip_option
            )


    def analyze_road_usage(self):
        results_df = self.otp.get_results_dataframe()
        results_df.sort_values(by="attendee_id").to_csv(self.output_dir / "RequeriedTrips" / "QueriedTripsWithDetails.csv", index=False)
        print("✅ Saved all OTP trip results to QueriedTripsWithDetails.csv")

        generic_roads = {
            "road", "track", "path", "bike path", "parking aisle", "service road", 
            "underpass", "ramp", "steps", "link", "platform", "sidewalk", "open area"
        }

        road_counter = Counter()
        hour_counter = {}
        attendee_road_rows = []

        for _, row in results_df.iterrows():
            attendee_id = row["attendee_id"]
            direction = row["direction"]
            roads_used = set()

            for i in range(1, 16):
                road_col = f"leg{i}_roads"
                time_col = f"leg{i}_from_scheduledTime"
                if pd.isna(row.get(road_col)) or pd.isna(row.get(time_col)):
                    continue

                try:
                    dt = pd.to_datetime(row[time_col])
                    hour = f"{dt.strftime('%H')}:00–{(dt + pd.Timedelta(hours=1)).strftime('%H')}:00"
                except Exception:
                    continue

                roads = [r.strip() for r in str(row[road_col]).split(',') if r.strip()]
                unique_roads = set(r for r in roads if r.lower() not in generic_roads)
                for road in unique_roads:
                    key = (road, direction)
                    road_counter[key] += 1
                    if key not in hour_counter:
                        hour_counter[key] = Counter()
                    hour_counter[key][hour] += 1
                    roads_used.add(road)

            if roads_used:
                attendee_road_rows.append({
                    "attendee_id": attendee_id,
                    "direction": direction,
                    "roads_used": sorted(list(roads_used))
                })

        # Save per-attendee road usage
        attendee_road_df = pd.DataFrame(attendee_road_rows)
        attendee_road_df.sort_values(by=["attendee_id", "direction"]).to_csv(self.output_dir / "AttendeeUsage" / "AttendeeRoadUsage.csv", index=False)

        # Aggregate with hourly usage per direction
        all_hours = sorted({h for counts in hour_counter.values() for h in counts})
        rows = []
        for (road, direction), total in road_counter.items():
            row = {"road": road, "direction": direction, "total_uses": total}
            for hour in all_hours:
                row[hour] = hour_counter[(road, direction)].get(hour, 0)
            rows.append(row)

        road_usage_df = pd.DataFrame(rows)
        road_usage_df.sort_values(by="total_uses", ascending=False).to_csv(self.output_dir / "MostUsed" / "MostUsedRoads.csv", index=False)

        print("✅ Saved road usage to AttendeeRoadUsage.csv and MostUsedRoads.csv")


    def analyze_transit_usage(self):
        csv_path = self.output_dir / "RequeriedTrips" / "QueriedTripsWithDetails.csv"
        if not csv_path.exists():
            print("❌ QueriedTripsWithDetails.csv not found.")
            return

        results_df = pd.read_csv(csv_path)

        transit_counter = Counter()
        hour_counter = {}
        attendee_transit_rows = []

        for _, row in results_df.iterrows():
            attendee_id = row["attendee_id"]
            direction = row["direction"]
            routes_used = set()

            for i in range(1, 16):
                mode = row.get(f"leg{i}_mode")
                route_name = row.get(f"leg{i}_route")
                time_str = row.get(f"leg{i}_from_scheduledTime")

                if pd.isna(mode) or pd.isna(route_name) or pd.isna(time_str):
                    continue
                if mode not in {"BUS", "TRAM", "RAIL", "SUBWAY"}:
                    continue

                route = route_name.strip()
                if not route:
                    continue

                try:
                    dt = pd.to_datetime(time_str)
                    hour = f"{dt.strftime('%H')}:00–{(dt + pd.Timedelta(hours=1)).strftime('%H')}:00"
                except Exception:
                    continue

                key = (route, direction)
                transit_counter[key] += 1
                if key not in hour_counter:
                    hour_counter[key] = Counter()
                hour_counter[key][hour] += 1
                routes_used.add(route)

            if routes_used:
                attendee_transit_rows.append({
                    "attendee_id": attendee_id,
                    "direction": direction,
                    "routes_used": sorted(list(routes_used))
                })

        # Save per-attendee transit usage
        attendee_df = pd.DataFrame(attendee_transit_rows)
        if attendee_df.empty:
            print("⚠️ No transit usage found — writing empty CSVs.")

            (self.output_dir / "AttendeeUsage").mkdir(parents=True, exist_ok=True)
            (self.output_dir / "MostUsed").mkdir(parents=True, exist_ok=True)

            pd.DataFrame(columns=["attendee_id", "direction", "routes_used"]).to_csv(
                self.output_dir / "AttendeeUsage" / "AttendeePublicTransportUsed.csv", index=False
            )
            pd.DataFrame(columns=["route_name", "direction", "total_uses"]).to_csv(
                self.output_dir / "MostUsed" / "MostUsedPublicTransport.csv", index=False
            )
            return
        attendee_df.sort_values(by=["attendee_id", "direction"]).to_csv(self.output_dir / "AttendeeUsage" / "AttendeePublicTransportUsed.csv", index=False)

        # Aggregate with hourly usage per direction
        all_hours = sorted({h for counts in hour_counter.values() for h in counts})
        rows = []
        for (route, direction), total in transit_counter.items():
            row = {"route_name": route, "direction": direction, "total_uses": total}
            for hour in all_hours:
                row[hour] = hour_counter[(route, direction)].get(hour, 0)
            rows.append(row)

        transit_df = pd.DataFrame(rows)
        transit_df.sort_values(by="total_uses", ascending=False).to_csv(self.output_dir / "MostUsed" / "MostUsedPublicTransport.csv", index=False)

        print("✅ Saved transit usage to AttendeePublicTransportUsed.csv and MostUsedPublicTransport.csv")


    def run_full_trip_requery_and_analysis(self):
        self.trips_dep_df = self.classify_modes(self.trips_dep_df)
        self.trips_ret_df = self.classify_modes(self.trips_ret_df)

        for mode, transits in [
            ("CAR", []),
            ("BICYCLE", ["RAIL", "SUBWAY"]),
            ("WALK", ["BUS", "TRAM", "RAIL", "SUBWAY"])
        ]:
            self.requery_trips(self.trips_dep_df, "departure", mode, transits)
            self.requery_trips(self.trips_ret_df, "return", mode, transits)

        self.analyze_road_usage()
        self.analyze_transit_usage()
