import random
from datetime import datetime, timedelta
import pytz
import pandas as pd

class SimpleAttendeeDataGenerator:
    SEED = 42
    TOTAL_ATTENDEES = 10
    BRABANT_PROPORTION = 0.75

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

    MAIN_REGION_BOUNDS = {
        "min_lat": 51.25,
        "max_lat": 51.75,
        "min_lng": 4.25,
        "max_lng": 5.75
    }

    NETHERLANDS_BOUNDS = {
        "min_lat": 50.75,
        "max_lat": 53.55,
        "min_lng": 3.36,
        "max_lng": 7.22
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
        attempts = 0
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


    def generate_coords(self, brabant_count, other_count):
        coords = self.sample_coords(self.MAIN_REGION_BOUNDS, brabant_count)
        coords += self.sample_coords(self.NETHERLANDS_BOUNDS, other_count)
        random.shuffle(coords)
        return coords

    def generate(self):
        brabant_count = int(self.TOTAL_ATTENDEES * self.BRABANT_PROPORTION)
        other_count = self.TOTAL_ATTENDEES - brabant_count

        departure_times = self.generate_times(self.DEPARTURE_TIME_WINDOWS, self.TOTAL_ATTENDEES)
        return_times = self.generate_times(self.RETURN_TIME_WINDOWS, self.TOTAL_ATTENDEES)
        coords = self.generate_coords(brabant_count, other_count)

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

        return pd.DataFrame(journey_rows)


    def save_to_csv(self, filepath):
        if not self.attendees:
            self.generate()
        df = pd.DataFrame(self.attendees)
        df.to_csv(filepath, index=False)
