import random
from datetime import datetime, timedelta
import pytz
import pandas as pd
import os

class SimpleAttendeeDataGenerator:
    SEED = 42
    TOTAL_ATTENDEES = 100

    EINDHOVEN_PROPORTION = 0.21
    BEST_PROPORTION = 0.06
    HELMOND_PROPORTION = 0.05
    TILBURG_PROPORTION = 0.04
    VELDHOVEN_PROPORTION = 0.04
    DEN_BOSCH_PROPORTION = 0.03
    GELDROP_PROPORTION = 0.03
    NUENEN_PROPORTION = 0.02
    VALKENSWAARD_PROPORTION = 0.02
    BREDA_BOUNDS_PROPORTION = 0.02
    REST_PROPORTION = 48

    EVENT_LAT = 51.49987310839164
    EVENT_LNG = 5.43323252389715

    DIRECT_MODES = ["WALK", "BICYCLE", "CAR"]

    TRANSIT_MODES = [
        "BUS", "RAIL", "TRAM", "SUBWAY"
    ]

    DEPARTURE_TIME_WINDOWS = [
        {"start": "16:00", "end": "18:00", "proportion": 0.2},
        {"start": "18:00", "end": "21:00", "proportion": 0.5},
        {"start": "21:00", "end": "00:00", "proportion": 0.3}
    ]

    RETURN_TIME_WINDOWS = [
        {"start": "22:00", "end": "23:59", "proportion": 0.5},
        {"start": "00:00", "end": "02:00", "proportion": 0.3},
        {"start": "02:00", "end": "05:00", "proportion": 0.2}
    ]

    NETHERLANDS_BOUNDS = {
        "min_lat": 50.75,        
        "max_lat": 53.50,        
        "min_lng": 3.35,        
        "max_lng": 7.22 
    }

    CITY_BOUNDS = {
        "EINDHOVEN": {        "min_lat": 51.40,        "max_lat": 51.50,        "min_lng": 5.40,        "max_lng": 5.55,  },
        "BEST": {        "min_lat": 51.48,        "max_lat": 51.52,        "min_lng": 5.35,        "max_lng": 5.45    }, 
        "HELMOND": {        "min_lat": 51.43,        "max_lat": 51.49,        "min_lng": 5.60,        "max_lng": 5.72    },
        "TILBURG": {        "min_lat": 51.52,        "max_lat": 51.62,        "min_lng": 5.00,        "max_lng": 5.15    },
        "VELDHOVEN": {        "min_lat": 51.39,        "max_lat": 51.44,        "min_lng": 5.37,        "max_lng": 5.47    },
        "DEN_BOSCH": {        "min_lat": 51.65,        "max_lat": 51.73,        "min_lng": 5.25,        "max_lng": 5.35    },
        "GELDROP": {        "min_lat": 51.40,        "max_lat": 51.44,        "min_lng": 5.55,        "max_lng": 5.61    },
        "NUENEN": {        "min_lat": 51.44,        "max_lat": 51.48,        "min_lng": 5.55,        "max_lng": 5.61    }, 
        "VALKENSWAARD": {        "min_lat": 51.32,        "max_lat": 51.38,        "min_lng": 5.55,        "max_lng": 5.65    },
        "BREDA": {        "min_lat": 51.55,        "max_lat": 51.62,        "min_lng": 4.70,        "max_lng": 4.85    },
    }

    CITY_PROPORTIONS = {    
        "EINDHOVEN": 0.21,
        "BEST": 0.06,    
        "HELMOND": 0.05,    
        "TILBURG": 0.04,    
        "VELDHOVEN": 0.04,    
        "DEN_BOSCH": 0.03,    
        "GELDROP": 0.03,    
        "NUENEN": 0.02,    
        "VALKENSWAARD": 0.02,    
        "BREDA": 0.02,    
    }

    def __init__(self, otp_client=None):
        self.otp_client = otp_client
        random.seed(self.SEED)
        self.attendees = []

    def parse_time(self, hm_str):
        return datetime.strptime(hm_str, "%H:%M")

    def generate_times(self, windows, total_count):
        tz = pytz.timezone("Europe/Amsterdam")
        base_date = datetime(2025, 5, 17)
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
                local_dt = datetime.combine(base_date.date(), time_obj.time())
                local_dt = tz.localize(local_dt, is_dst=True)
                times.append(local_dt.strftime("%Y-%m-%dT%H:%M:%S%z"))

        while len(times) < total_count:
            times.append(random.choice(times))

        random.shuffle(times)
        return times[:total_count]
    
    def get_direct_modes(self):
        return self.DIRECT_MODES
    
    def get_transit_modes(self, direct_mode):
        if direct_mode == 'WALK':
            transit_modes = self.TRANSIT_MODES.copy()  # All modes for WALK
        elif direct_mode == 'BICYCLE':
            transit_modes = [self.TRANSIT_MODES[1], self.TRANSIT_MODES[3]]  # Only SUBWAY and TRAIN for BIKE
        else:
            transit_modes = [] # No transit modes for CAR
        return transit_modes

    def sample_coords(self, bounds, count):
        coords = []
        while len(coords) < count:
            lat = random.uniform(bounds["min_lat"], bounds["max_lat"])
            lng = random.uniform(bounds["min_lng"], bounds["max_lng"])

            if self.otp_client:
                snapped_lat, snapped_lng, valid_points = self.otp_client.snap_point_to_road(lat, lng)
                if valid_points:  # snapping succeeded
                    coords.append({"latitude": snapped_lat, "longitude": snapped_lng})
                    print(f"✅ Snapped point ({lat}, {lng}) to ({snapped_lat}, {snapped_lng})")
                else:
                    print(f"❌ Discarded unsnappable point ({lat}, {lng})")
            else:
                coords.append({"latitude": lat, "longitude": lng})

        return coords


    def generate_coords(self, counts):
        coords = []
        for location in counts:
            if location == "OTHER":
                coords += self.sample_coords(self.NETHERLANDS_BOUNDS, counts[location])
            else:
                coords += self.sample_coords(self.CITY_BOUNDS[location], counts[location])
        random.shuffle(coords)
        return coords

    def generate(self):

        counts = {}
        for i in range(len(self.CITY_BOUNDS)):
            city = list(self.CITY_BOUNDS.keys())[i]
            proportion = self.CITY_PROPORTIONS[city]
            count = int(self.TOTAL_ATTENDEES * proportion)
            counts[city] = count
        counts["OTHER"] = self.TOTAL_ATTENDEES - sum(counts.values())

        departure_times = self.generate_times(self.DEPARTURE_TIME_WINDOWS, self.TOTAL_ATTENDEES)
        return_times = self.generate_times(self.RETURN_TIME_WINDOWS, self.TOTAL_ATTENDEES)
        coords = self.generate_coords(counts)

        self.attendees = []
        for i in range(self.TOTAL_ATTENDEES):
            self.attendees.append({
                "attendee_id": f"A{i+1:05d}",
                "departure_time": departure_times[i],
                "return_time": return_times[i],
                "departure_lat": coords[i]["latitude"],
                "departure_lng": coords[i]["longitude"],
                "return_lat": self.EVENT_LAT,
                "return_lng": self.EVENT_LNG
            })

        return self.attendees

    def get_dataframe(self):

        if not self.attendees:
            self.generate()
        
        if not self.attendees:
            print("No attendees to process. Aborting.")
            return pd.DataFrame()  # Return empty DataFrame safely

        journey_rows = []
        for att in self.attendees:
            journey_rows.append({
                "attendee_id": att["attendee_id"],
                "direction": "departure",
                "origin_lat": att["departure_lat"],
                "origin_lng": att["departure_lng"],
                "destination_lat": att["return_lat"],
                "destination_lng": att["return_lng"],
                "departure_time": att["departure_time"]
            })

            journey_rows.append({
                "attendee_id": att["attendee_id"],
                "direction": "return",
                "origin_lat": att["return_lat"],
                "origin_lng": att["return_lng"],
                "destination_lat": att["departure_lat"],
                "destination_lng": att["departure_lng"],
                "departure_time": att["return_time"]
            })

        df = pd.DataFrame(journey_rows)

        self.save_to_csv(df, "../../Data/AttendeeData/attendee_data.csv")

        return df


    def save_to_csv(self, df, relative_filepath):
        import os
        script_dir = os.path.dirname(__file__)
        abs_path = os.path.join(script_dir, relative_filepath)

        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        df.to_csv(abs_path, index=False)
