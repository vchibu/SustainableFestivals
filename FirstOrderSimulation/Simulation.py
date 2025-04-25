import requests
from datetime import datetime

url = "http://localhost:8080/otp/gtfs/v1"

query = """
{
  planConnection(
    origin: {
      location: { coordinate: { latitude: 52.379189, longitude: 4.899431 } }
    }
    destination: {
      location: { coordinate: { latitude: 52.090737, longitude: 5.121420 } }
    }
    dateTime: { earliestDeparture: "2025-04-24T08:00:00+02:00" }
    modes: {
      direct: [WALK]
      transit: { transit: [{ mode: BUS }, { mode: RAIL }] }
    }
    first: 1
  ) {
    edges {
      node {
        legs {
          mode
          distance
          from {
            name
            departure {
              scheduledTime
            }
          }
          to {
            name
            arrival {
              scheduledTime
            }
          }
          route {
            shortName
            longName
          }
        }
      }
    }
  }
}
"""

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json={"query": query}, headers=headers)

try:
    data = response.json()
    fmt = "%Y-%m-%dT%H:%M:%S%z"

    for edge in data["data"]["planConnection"]["edges"]:
        print("🛣️ New Trip:")

        total_duration_minutes = 0.0
        total_distance_km = 0.0

        legs = edge["node"]["legs"]
        for i, leg in enumerate(legs, 1):
            route = leg.get("route")
            print(f"Leg {i}: 🚍 {leg['mode']} from {leg['from']['name']} to {leg['to']['name']}")
            if route:
                print(f"     Route: {route.get('shortName', '')} {route.get('longName', '')}")
            departure_time = leg['from']['departure']['scheduledTime']
            arrival_time = leg['to']['arrival']['scheduledTime']
            print(f"     Departure: {departure_time}")
            print(f"     Arrival:   {arrival_time}")

            # Calculate leg duration and distance
            try:
                t1 = datetime.strptime(departure_time, fmt)
                t2 = datetime.strptime(arrival_time, fmt)
                duration_minutes = (t2 - t1).total_seconds() / 60
            except Exception:
                duration_minutes = 0.0

            distance_km = leg.get("distance", 0.0) / 1000.0

            # Add to totals
            total_duration_minutes += duration_minutes
            total_distance_km += distance_km

            print(f"     🧾 Duration: {duration_minutes:.1f} min, Distance: {distance_km:.2f} km")

        # After all legs are printed
        print("\n📊 Total Trip Summary:")
        print(f"   🧭 Total Duration: {total_duration_minutes:.1f} min")
        print(f"   🛣️ Total Distance: {total_distance_km:.2f} km\n")

except Exception as e:
    print("❌ Error:", e)
    print("Text:", response.text[:500])
