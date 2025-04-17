import googlemaps
from datetime import datetime
import pandas as pd
import time
from AttendeeDataGenerator import AttendeeDataGenerator

class Simulation:
    # Target destination coordinates
    DESTINATION = (51.4994356, 5.434003)

    # Emission factors in kg CO2 per km by transport mode
    EMISSION_FACTORS = {
        "carpool": 0.12,
        "public transport": 0.08,
        "bike": 0.0
    }

    # Batch size for Distance Matrix API requests to avoid hitting rate limits
    BATCH_SIZE = 100

    def __init__(self, api_key):
        # Initialize the simulation with Google Maps API client and attendee generator
        self.api_key = api_key
        self.gmaps = googlemaps.Client(key=self.api_key)
        self.generator = AttendeeDataGenerator()
        self.df_attendees = None

    def run(self):
        # Generate synthetic attendees and simulate their travel
        self.generator.generate()
        self.df_attendees = self.generator.get_dataframe()
        self._simulate_travel()

    def _simulate_travel(self):
        # Lists to accumulate travel results
        distances = []
        durations = []
        emissions = []

        # Determine how many batches we need to process
        batch_count = (len(self.df_attendees) + self.BATCH_SIZE - 1) // self.BATCH_SIZE

        for batch_index in range(batch_count):
            # Slice out current batch
            start_idx = batch_index * self.BATCH_SIZE
            end_idx = min((batch_index + 1) * self.BATCH_SIZE, len(self.df_attendees))
            batch = self.df_attendees.iloc[start_idx:end_idx]

            # Extract origins, travel modes, and departure times for this batch
            origins = [(row["latitude"], row["longitude"]) for _, row in batch.iterrows()]
            modes = [self._map_mode(row["transport_mode"]) for _, row in batch.iterrows()]
            departures = [self._build_departure_datetime(row["departure_time"]) for _, row in batch.iterrows()]

            for i, origin in enumerate(origins):
                try:
                    # Call Google Distance Matrix API for individual attendee
                    result = self.gmaps.distance_matrix(
                        origins=[origin],
                        destinations=[self.DESTINATION],
                        mode=modes[i],
                        departure_time=departures[i]
                    )

                    # Extract distance and duration if API call succeeded
                    element = result["rows"][0]["elements"][0]
                    if element["status"] == "OK":
                        distance_km = element["distance"]["value"] / 1000  # Convert meters to km
                        duration_min = element["duration"]["value"] / 60    # Convert seconds to minutes
                    else:
                        distance_km = None
                        duration_min = None

                except Exception:
                    # Fallback for failed requests
                    distance_km = None
                    duration_min = None

                # Temporarily store travel distance and duration
                distances.append(distance_km)
                durations.append(duration_min)

                # Placeholder, to be filled with actual value after carpool handling
                emissions.append(None)

                # Short delay to respect Google API rate limits
                time.sleep(0.05)

        # Attach distances and durations to the dataframe first
        self.df_attendees["travel_distance_km"] = distances
        self.df_attendees["travel_duration_min"] = durations

        # Now compute emissions, handling carpool groups correctly
        emissions = [None] * len(self.df_attendees)
        carpool_groups = self.df_attendees[self.df_attendees["transport_mode"] == "carpool"].groupby("carpool_id")

        # Handle carpool attendees
        for carpool_id, group in carpool_groups:
            if pd.isna(carpool_id):
                continue
            idxs = group.index.tolist()
            first_idx = idxs[0]
            distance = self.df_attendees.at[first_idx, "travel_distance_km"]
            emission_total = self.EMISSION_FACTORS["carpool"] * distance if distance is not None else None
            emission_per_person = round(emission_total / len(idxs), 3) if emission_total is not None else None
            for idx in idxs:
                emissions[idx] = emission_per_person

        # Handle non-carpool attendees
        for idx, row in self.df_attendees.iterrows():
            if row["transport_mode"] != "carpool":
                distance = row["travel_distance_km"]
                factor = self.EMISSION_FACTORS.get(row["transport_mode"], 0.0)
                emissions[idx] = round(factor * distance, 3) if distance is not None else None

        # Attach final emissions to dataframe
        self.df_attendees["carbon_footprint_kg"] = emissions

    def _map_mode(self, transport_mode):
        # Translate internal transport mode to Google Maps API-compatible value
        mapping = {
            "carpool": "driving",
            "public transport": "transit",
            "bike": "bicycling"
        }
        return mapping.get(transport_mode, "driving")

    def _build_departure_datetime(self, time_str):
        # Convert a "HH:MM" string to a datetime object using today's date
        today = datetime.now().date()
        full_time = datetime.strptime(time_str, "%H:%M").time()
        return datetime.combine(today, full_time)

    def _calculate_emission(self, mode, distance_km):
        # This method is now only used for non-carpool attendees
        if distance_km is None:
            return None
        factor = self.EMISSION_FACTORS.get(mode, 0.0)
        return round(factor * distance_km, 3)

    def get_attendees(self):
        # Return the simulation results
        if self.df_attendees is None:
            raise ValueError("Simulation not run yet. Call .run() first.")
        return self.df_attendees

if __name__ == "__main__":
    # Entry point for running the simulation
    API_KEY = "AIzaSyDNMe9BaKDaVFMlH4T1ZqzJ5mB66g-dMyU"  # Replace with secure key handling in production
    sim = Simulation(api_key=API_KEY)
    sim.run()
    print(sim.get_attendees().head())