import requests
from datetime import datetime
import csv
from AttendeeDataGenerator import AttendeeDataGenerator

adg = AttendeeDataGenerator()

url = "http://localhost:8080/otp/gtfs/v1"

adg.generate()
attendees = adg.get_dataframe()

headers = {
    "Content-Type": "application/json"
}

trip_results = []

def build_modes_block(direct_mode, transit_modes):
    parts = []
    
    # Add direct mode if available
    if direct_mode.strip():
        parts.append(f"direct: [{direct_mode.strip()}]")
    
    # Add transit modes if available
    if transit_modes:
        transit_modes_list = [mode.strip() for mode in transit_modes.split(",") if mode.strip()]
        if transit_modes_list:
            # Format for the nested transit structure
            transit_modes_formatted = ", ".join([f"{{ mode: {mode} }}" for mode in transit_modes_list])
            parts.append(f"transit: {{ transit: [{transit_modes_formatted}] }}")
    
    return " ".join(parts)
    
def send_and_process_query(query, attendee_id, trip_label):
    response = requests.post(url, json={"query": query}, headers=headers)
    try:
        data = response.json()
        if "errors" in data:
            raise Exception(data["errors"])

        fmt = "%Y-%m-%dT%H:%M:%S%z"

        for edge in data["data"]["planConnection"]["edges"]:
            trip_data = {
                "attendee_id": attendee_id
            }
            total_duration_minutes = 0.0
            total_distance_km = 0.0

            legs = edge["node"]["legs"]
            for i, leg in enumerate(legs, 1):
                mode = leg["mode"]
                distance_km = leg.get("distance", 0.0) / 1000.0

                departure_time = leg['from']['departure']['scheduledTime']
                arrival_time = leg['to']['arrival']['scheduledTime']

                try:
                    t1 = datetime.strptime(departure_time, fmt)
                    t2 = datetime.strptime(arrival_time, fmt)
                    duration_minutes = (t2 - t1).total_seconds() / 60
                except Exception:
                    duration_minutes = 0.0

                total_duration_minutes += duration_minutes
                total_distance_km += distance_km

                trip_data[f"leg{i}_mode"] = mode
                trip_data[f"leg{i}_length"] = distance_km
                trip_data[f"leg{i}_duration"] = duration_minutes

            trip_data["total_duration"] = total_duration_minutes
            trip_data["total_length"] = total_distance_km
            trip_data["total_carbon_footprint"] = 0

            trip_results.append(trip_data)

    except Exception as e:
        print(f"\u274c Error during {trip_label}: {e}")
        print("Text:", response.text[:500])

for index, row in attendees.iterrows():
    origin_lat = row["departure_lat"]
    origin_lng = row["departure_lng"]
    destination_lat = row["return_lat"]
    destination_lng = row["return_lng"]
    departure_time = row["departure_time"]
    return_time = row["return_time"]
    departure_mode = row["departure_mode"]
    return_mode = row["return_mode"]
    departure_transit = row["departure_transit"]
    return_transit = row['return_transit']
    attendee_id = row["attendee_id"]

    modes_departure = build_modes_block(departure_mode, departure_transit)
    modes_return = build_modes_block(return_mode, return_transit)

    query_departure = f"""
    {{
      planConnection(
        origin: {{ location: {{ coordinate: {{ latitude: {origin_lat}, longitude: {origin_lng} }} }} }}
        destination: {{ location: {{ coordinate: {{ latitude: {destination_lat}, longitude: {destination_lng} }} }} }}
        dateTime: {{ earliestDeparture: \"{departure_time}\" }}
        modes: {{ {modes_departure} }}
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

    query_return = f"""
    {{
      planConnection(
        origin: {{ location: {{ coordinate: {{ latitude: {destination_lat}, longitude: {destination_lng} }} }} }}
        destination: {{ location: {{ coordinate: {{ latitude: {origin_lat}, longitude: {origin_lng} }} }} }}
        dateTime: {{ earliestDeparture: \"{return_time}\" }}
        modes: {{ {modes_return} }}
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

    send_and_process_query(query_departure, attendee_id, f"Departure Trip for Attendee {index}")
    send_and_process_query(query_return, attendee_id, f"Return Trip for Attendee {index}")

    print(f"\u2705 Processed Attendee {index + 1}/{len(attendees)}: {attendee_id}")

# Write results
all_keys = set()
for trip in trip_results:
    all_keys.update(trip.keys())

with open("trip_results.csv", mode="w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=sorted(all_keys))
    writer.writeheader()
    for trip in trip_results:
        writer.writerow(trip)

print("\u2705 Trip results saved to trip_results.csv")