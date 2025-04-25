import random
import pandas as pd
from datetime import datetime, timedelta

class AttendeeDataGenerator:

    # Random seed for reproducibility
    SEED = 42

    # Total number of attendees to generate
    TOTAL_POINTS = 100

    # Proportion of attendees from Brabant region
    BRABANT_PROPORTION = 0.75

    # Maximum number of attendees in a carpool group
    MAX_CARPOOL_SIZE = 5

    # Proportions of transport modes for departure and return trips
    DEPARTURE_TRANSPORT_MODE_PROPORTIONS = {
        "public transport": 0.5,
        "bike": 0.2,
        "carpool": 0.3
    }

    # Proportions of transport modes for return trips
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

    # Geographical bounds for the Brabant region
    MAIN_REGION_BOUNDS = {
        "min_lat": 51.25,
        "max_lat": 51.75,
        "min_lng": 4.25,
        "max_lng": 5.75
    }

    # Constructor to initialize the random seed and dataframe   
    def __init__(self):
        random.seed(self.SEED)
        self.df_attendees = None

    # Method to parse time strings into datetime objects
    def parse_time(self, hm_str):
        return datetime.strptime(hm_str, "%H:%M")

    # Method to generate random coordinates within given bounds
    def generate_random_coords(self, min_lat, max_lat, min_lng, max_lng, count):
        return [
            {
                "latitude": round(random.uniform(min_lat, max_lat), 6),
                "longitude": round(random.uniform(min_lng, max_lng), 6)
            }
            for _ in range(count)
        ]

    # Method to generate random times based on defined windows and proportions
    def generate_times(self, windows, total_count):
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
                times.append((start + timedelta(minutes=minutes)).strftime("%H:%M"))
        while len(times) < total_count:
            times.append(random.choice(times))
        random.shuffle(times)
        return times[:total_count]

    # Method to assign transport modes based on defined proportions and total count
    def assign_transport_modes(self, proportions, total_count):
        modes = []
        for mode, prop in proportions.items():
            modes.extend([mode] * int(total_count * prop))
        while len(modes) < total_count:
            modes.append(random.choice(list(proportions.keys())))
        random.shuffle(modes)
        return modes[:total_count]

    # Method to sample carpool group sizes based on defined probabilities
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
            if (id_column_prefix == "departure"):
                carpool_id = f"{'D'}{carpool_id_counter}"
            else:
                carpool_id = f"{'R'}{carpool_id_counter}"
        
            # Assign same random coordinates to group
            coord = self.generate_random_coords(**self.MAIN_REGION_BOUNDS, count=1)[0]
            group[f"{id_column_prefix}_carpool_id"] = carpool_id
            group[f"{id_column_prefix}_lat"] = coord["latitude"]
            group[f"{id_column_prefix}_lng"] = coord["longitude"]
            carpool_info.append(group)

            index += size
            carpool_id_counter += 1

        carpool_df_updated = pd.concat(carpool_info)

        df = df.merge(
            carpool_df_updated[["attendee_id", f"{id_column_prefix}_lat", f"{id_column_prefix}_lng", f"{id_column_prefix}_carpool_id"]],
            on="attendee_id", how="left"
        )

        # Fill non-carpoolers with default values
        df[f"{id_column_prefix}_carpool_id"] = df[f"{id_column_prefix}_carpool_id"].fillna("N/A")
        df[f"{id_column_prefix}_lat"] = df[f"{id_column_prefix}_lat"].fillna(df["latitude"])
        df[f"{id_column_prefix}_lng"] = df[f"{id_column_prefix}_lng"].fillna(df["longitude"])

        return df


    # Method to generate the entire dataset
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
        df["departure_mode"] = self.assign_transport_modes(self.DEPARTURE_TRANSPORT_MODE_PROPORTIONS, self.TOTAL_POINTS)
        df["return_mode"] = self.assign_transport_modes(self.DEPARTURE_TRANSPORT_MODE_PROPORTIONS, self.TOTAL_POINTS)

        df = self.assign_carpool_groups(df, mode_column="departure_mode", id_column_prefix="departure")
        df = self.assign_carpool_groups(df, mode_column="return_mode", id_column_prefix="return")


        ordered_cols = [
            "attendee_id",
            "departure_time", "departure_mode", "departure_lat", "departure_lng", "departure_carpool_id",
            "return_time", "return_mode", "return_lat", "return_lng", "return_carpool_id"
        ]

        self.df_attendees = df[ordered_cols]

    # Method to get the generated dataframe
    def get_dataframe(self):
        if self.df_attendees is None:
            raise ValueError("Data not generated yet. Call .generate() first.")
        return self.df_attendees

# Example usage
# generator = AttendeeDataGenerator()
# generator.generate()
# print(generator.get_dataframe())
