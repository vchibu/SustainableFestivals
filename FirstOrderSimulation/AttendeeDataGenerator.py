import random
import pandas as pd
from datetime import datetime, timedelta
import pytz
import requests


class AttendeeDataGenerator:

    # Random seed for reproducibility
    SEED = 42

    # Total number of attendees to generate
    TOTAL_POINTS = 10

    # Proportion of attendees from Brabant region
    BRABANT_PROPORTION = 0.75

    # Maximum number of attendees in a carpool group
    MAX_CARPOOL_SIZE = 5

    # Set return location to fixed event coordinates
    EVENT_LAT = 51.49987310839164
    EVENT_LNG = 5.43323252389715

    # Proportions of transport modes for departure and return trips
    DEPARTURE_TRANSPORT_MODE_PROPORTIONS = {
        "public transport": 0.5,
        "bike": 0.2,
        "carpool": 0.3
    }

    RETURN_TRANSPORT_MODE_PROPORTIONS = {
        "public transport": 0.3,
        "bike": 0.2,
        "carpool": 0.5
    }

    # Proportions of carpool group sizes
    CARPOOL_SIZE_PROBABILITIES = {
        1: 0.1,
        2: 0.2,
        3: 0.4,
        4: 0.2,
        5: 0.1
    }

    # Departure windows with proportions
    DEPARTURE_TIME_WINDOWS = [
        {"start": "16:00", "end": "18:00", "proportion": 0.2},
        {"start": "18:00", "end": "21:00", "proportion": 0.5},
        {"start": "21:00", "end": "00:00", "proportion": 0.3}
    ]

    # Return time windows with proportions
    RETURN_TIME_WINDOWS = [
        {"start": "22:00", "end": "23:59", "proportion": 0.5},
        {"start": "00:00", "end": "02:00", "proportion": 0.3},
        {"start": "02:00", "end": "05:00", "proportion": 0.2}
    ]

    # Geographical bounds for the Netherlands and Brabant region
    NETHERLANDS_BOUNDS = {
        "min_lat": 50.75,
        "max_lat": 53.55,
        "min_lng": 3.36,
        "max_lng": 7.22
    }

    MAIN_REGION_BOUNDS = {
        "min_lat": 51.25,
        "max_lat": 51.75,
        "min_lng": 4.25,
        "max_lng": 5.75
    }

    DIRECT_MODES = ["WALK", "BICYCLE", "CAR"]

    TRANSIT_MODES = [
        "BUS", "RAIL", "TRAM", "SUBWAY"
    ]

    def __init__(self):
        random.seed(self.SEED)
        self.df_attendees = None

    def parse_time(self, hm_str):
        return datetime.strptime(hm_str, "%H:%M")

    def generate_random_coords(self, min_lat, max_lat, min_lng, max_lng, count):
        return [
            {
                "latitude": round(random.uniform(min_lat, max_lat), 6),
                "longitude": round(random.uniform(min_lng, max_lng), 6)
            }
            for _ in range(count)
        ]

    def generate_times(self, windows, total_count):

        tz = pytz.timezone("Europe/Amsterdam")
        date_prefix = datetime(2025, 5, 17)  # Festival date
        times = []

        for window in windows:
            count = int(total_count * window["proportion"])
            start = self.parse_time(window["start"])
            end = self.parse_time(window["end"])
            if end <= start:
                end += timedelta(days=1)

            for _ in range(count):
                delta = end - start
                minutes = random.randint(0, int(delta.total_seconds() / 60))
                time_obj = start + timedelta(minutes=minutes)

                # Combine with date prefix
                local_dt = datetime.combine(date_prefix.date(), time_obj.time())
                local_dt = tz.localize(local_dt, is_dst=True)  # Correct for DST

                # Output ISO-8601
                formatted_time = local_dt.strftime("%Y-%m-%dT%H:%M:%S%z")
                times.append(formatted_time)

        while len(times) < total_count:
            times.append(random.choice(times))

        random.shuffle(times)
        return times[:total_count]



    def assign_transport_modes(self, proportions, total_count):
        modes = []
        for mode, prop in proportions.items():
            modes.extend([mode] * int(total_count * prop))
        while len(modes) < total_count:
            modes.append(random.choice(list(proportions.keys())))
        random.shuffle(modes)
        return modes[:total_count]
    
    def assign_transit_modes_based_on_direct(self, direct_modes):
        transit_choices = []
        for direct_mode in direct_modes:
            if direct_mode == "WALK":
                # WALK → all transit modes
                transit_choices.append(",".join(self.TRANSIT_MODES))
            elif direct_mode == "BICYCLE":
                # BICYCLE → only RAIL
                transit_choices.append("RAIL")
            elif direct_mode == "CAR":
                # CAR → no transit
                transit_choices.append("")
            else:
                # fallback (shouldn't happen)
                transit_choices.append(",".join(self.TRANSIT_MODES))
        return transit_choices

    def map_departure_mode_to_direct(self, mode):
        mapping = {
            "public transport": "WALK",
            "bike": "BICYCLE",
            "carpool": "CAR"
        }
        return mapping.get(mode, "WALK")

    def sample_carpool_group_sizes(self, total_carpoolers):
        sizes = []
        while total_carpoolers > 0:
            size = random.choices(
                population=list(self.CARPOOL_SIZE_PROBABILITIES.keys()),
                weights=self.CARPOOL_SIZE_PROBABILITIES.values(),
                k=1
            )[0]
            size = min(size, total_carpoolers)
            sizes.append(size)
            total_carpoolers -= size
        return sizes

    def assign_carpool_groups(self, df, mode_column, id_column_prefix):
        carpool_df = df[df[mode_column] == "carpool"].copy()
        total = len(carpool_df)
        group_sizes = self.sample_carpool_group_sizes(total)

        carpool_id_counter = 1
        carpool_info = []

        index = 0
        for size in group_sizes:
            group = carpool_df.iloc[index:index+size].copy()
            carpool_id = f"{'D' if id_column_prefix == 'departure' else 'R'}{carpool_id_counter}"
            coord = self.generate_random_coords(**self.MAIN_REGION_BOUNDS, count=1)[0]
            group[f"{id_column_prefix}_carpool_id"] = carpool_id
            group[f"{id_column_prefix}_lat"] = coord["latitude"]
            group[f"{id_column_prefix}_lng"] = coord["longitude"]
            carpool_info.append(group)

            index += size
            carpool_id_counter += 1

        if carpool_info:
            carpool_df_updated = pd.concat(carpool_info)
            df = df.merge(
                carpool_df_updated[["attendee_id", f"{id_column_prefix}_lat", f"{id_column_prefix}_lng", f"{id_column_prefix}_carpool_id"]],
                on="attendee_id", how="left"
            )

        df[f"{id_column_prefix}_carpool_id"] = df[f"{id_column_prefix}_carpool_id"].fillna("N/A")
        df[f"{id_column_prefix}_lat"] = df[f"{id_column_prefix}_lat"].fillna(df["latitude"])
        df[f"{id_column_prefix}_lng"] = df[f"{id_column_prefix}_lng"].fillna(df["longitude"])

        return df

    def generate(self):
        brabant_count = int(self.TOTAL_POINTS * self.BRABANT_PROPORTION)
        other_count = self.TOTAL_POINTS - brabant_count

        coords = self.generate_random_coords(**self.MAIN_REGION_BOUNDS, count=brabant_count) + \
                 self.generate_random_coords(**self.NETHERLANDS_BOUNDS, count=other_count)

        random.shuffle(coords)
        df = pd.DataFrame(coords)

        df["attendee_id"] = [f"A{i:05d}" for i in range(1, self.TOTAL_POINTS + 1)]
        df["departure_time"] = self.generate_times(self.DEPARTURE_TIME_WINDOWS, self.TOTAL_POINTS)
        df["return_time"] = self.generate_times(self.RETURN_TIME_WINDOWS, self.TOTAL_POINTS)

        raw_departure_modes = self.assign_transport_modes(self.DEPARTURE_TRANSPORT_MODE_PROPORTIONS, self.TOTAL_POINTS)
        raw_return_modes = self.assign_transport_modes(self.RETURN_TRANSPORT_MODE_PROPORTIONS, self.TOTAL_POINTS)

        df["departure_raw_mode"] = raw_departure_modes
        df["return_raw_mode"] = raw_return_modes

        df["departure_mode"] = df["departure_raw_mode"].map(self.map_departure_mode_to_direct)
        df["return_mode"] = df["return_raw_mode"].map(self.map_departure_mode_to_direct)

        df["departure_transit"] = self.assign_transit_modes_based_on_direct(df["departure_mode"])
        df["return_transit"] = self.assign_transit_modes_based_on_direct(df["return_mode"])

        df = self.assign_carpool_groups(df, mode_column="departure_raw_mode", id_column_prefix="departure")
        df = self.assign_carpool_groups(df, mode_column="return_raw_mode", id_column_prefix="return")

        df["return_lat"] = self.EVENT_LAT
        df["return_lng"] = self.EVENT_LNG

        ordered_cols = [
            "attendee_id",
            "departure_time", "departure_mode", "departure_transit", "departure_lat", "departure_lng", "departure_carpool_id",
            "return_time", "return_mode", "return_transit", "return_lat", "return_lng", "return_carpool_id"
        ]

        self.df_attendees = df[ordered_cols]

    def get_dataframe(self):
        if self.df_attendees is None:
            raise ValueError("Data not generated yet. Call .generate() first.")
        return self.df_attendees
    
generator = AttendeeDataGenerator()
generator.generate()
df_attendees = generator.get_dataframe()
print(df_attendees.head())

