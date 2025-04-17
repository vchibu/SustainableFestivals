import random
import pandas as pd
from datetime import datetime, timedelta

class AttendeeDataGenerator:
    # -----------------------------
    # Configuration Constants
    # -----------------------------

    # Set seed to ensure reproducibility of random operations
    SEED = 42

    # Total number of attendees to generate
    TOTAL_POINTS = 100

    # Percentage of attendees from Noord Brabant region
    BRABANT_PROPORTION = 0.75

    # Maximum number of people allowed in a single carpool group
    MAX_CARPOOL_SIZE = 5

    # Proportion of attendees using different transport modes
    TRANSPORT_MODE_PROPORTIONS = {
        "public transport": 0.5,
        "bike": 0.2,
        "carpool": 0.3
    }

    # Time windows (in HH:MM) and their distribution proportions
    # Simulates different patterns of attendee arrival times
    DEPARTURE_TIME_WINDOWS = [
        {"start": "16:00", "end": "18:00", "proportion": 0.2},  # Early departures
        {"start": "18:00", "end": "21:00", "proportion": 0.5},  # Peak time
        {"start": "21:00", "end": "00:00", "proportion": 0.3}   # Late arrivals
    ]

    # Bounding box for the entire Netherlands
    NETHERLANDS_BOUNDS = {
        "min_lat": 50.75,
        "max_lat": 53.55,
        "min_lng": 3.36,
        "max_lng": 7.22
    }

    # Bounding box for Noord Brabant region
    MAIN_REGION_BOUNDS = {
        "min_lat": 51.25,
        "max_lat": 51.75,
        "min_lng": 4.25,
        "max_lng": 5.75
    }

    def __init__(self):
        # Set the seed and initialize the DataFrame container
        random.seed(self.SEED)
        self.df_attendees = None

    def parse_time(self, hm_str):
        """
        Converts time from string format 'HH:MM' to a datetime object.
        """
        return datetime.strptime(hm_str, "%H:%M")

    def generate_random_coords(self, min_lat, max_lat, min_lng, max_lng, count):
        """
        Generates a list of dictionaries with random lat/lng within a bounding box.
        """
        return [
            {
                "latitude": round(random.uniform(min_lat, max_lat), 6),
                "longitude": round(random.uniform(min_lng, max_lng), 6)
            }
            for _ in range(count)
        ]

    def generate_departure_times(self, windows, total_count):
        """
        Generates random departure times based on defined time windows and proportions.
        Ensures the resulting list matches the total_count by trimming or padding.
        """
        times = []
        for window in windows:
            count = int(total_count * window["proportion"])
            start = self.parse_time(window["start"])
            end = self.parse_time(window["end"])
            if end <= start:  # Handle overnight times (e.g., 21:00 to 00:00)
                end += timedelta(days=1)
            for _ in range(count):
                delta = end - start
                minutes = random.randint(0, int(delta.total_seconds() / 60))
                times.append((start + timedelta(minutes=minutes)).strftime("%H:%M"))
        while len(times) < total_count:
            times.append(random.choice(times))
        random.shuffle(times)
        return times[:total_count]

    def assign_transport_modes(self, proportions, total_count):
        """
        Assigns transport modes to attendees based on defined proportions.
        Pads the list if needed, then shuffles.
        """
        modes = []
        for mode, prop in proportions.items():
            modes.extend([mode] * int(total_count * prop))
        while len(modes) < total_count:
            modes.append(random.choice(list(proportions.keys())))
        random.shuffle(modes)
        return modes[:total_count]

    def assign_carpool_ids(self, df):
        """
        Assigns unique carpool IDs to attendees using carpool mode.
        Ensures no carpool group exceeds the MAX_CARPOOL_SIZE.
        """
        carpool_df = df[df["transport_mode"] == "carpool"].copy()
        total = len(carpool_df)
        group_count = (total + self.MAX_CARPOOL_SIZE - 1) // self.MAX_CARPOOL_SIZE
        carpool_ids = [f"C{str(i).zfill(5)}" for i in range(1, group_count + 1)]

        # Expand and assign IDs so each group can have up to MAX_CARPOOL_SIZE
        expanded_ids = []
        for cid in carpool_ids:
            expanded_ids.extend([cid] * self.MAX_CARPOOL_SIZE)
        random.shuffle(expanded_ids)

        # Assign only as many IDs as there are attendees
        carpool_df["carpool_id"] = expanded_ids[:total]

        # Merge back into the main DataFrame
        return df.merge(carpool_df[["attendee_id", "carpool_id"]], on="attendee_id", how="left")

    def generate(self):
        """
        Generates the complete dataset of attendees with geographic location,
        departure times, transport modes, and carpool IDs.
        """
        brabant_count = int(self.TOTAL_POINTS * self.BRABANT_PROPORTION)
        other_count = self.TOTAL_POINTS - brabant_count

        coords = self.generate_random_coords(**self.MAIN_REGION_BOUNDS, count=brabant_count) + \
                 self.generate_random_coords(**self.NETHERLANDS_BOUNDS, count=other_count)

        random.shuffle(coords)

        df = pd.DataFrame(coords)

        # Assign ID and other fields
        df["attendee_id"] = [f"A{i:05d}" for i in range(1, self.TOTAL_POINTS + 1)]
        df["departure_time"] = self.generate_departure_times(self.DEPARTURE_TIME_WINDOWS, self.TOTAL_POINTS)
        df["transport_mode"] = self.assign_transport_modes(self.TRANSPORT_MODE_PROPORTIONS, self.TOTAL_POINTS)

        # Assign carpool groups
        df = self.assign_carpool_ids(df)

        # Reorder columns for clarity
        ordered_cols = ["attendee_id", "latitude", "longitude", "departure_time", "transport_mode", "carpool_id"]
        self.df_attendees = df[ordered_cols]

    def get_dataframe(self):
        """
        Returns the final DataFrame containing all generated attendee data.
        Raises an error if generate() hasn't been called yet.
        """
        if self.df_attendees is None:
            raise ValueError("Data not generated yet. Call .generate() first.")
        return self.df_attendees
