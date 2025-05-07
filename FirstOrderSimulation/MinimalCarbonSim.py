from SimpleDataGenerator import SimpleAttendeeDataGenerator
from OTPTripPlannerClient import OTPTripPlannerClient
from CarbonCalculator import CarbonCalculator
from StatisticalAnalysis import StatisticalAnalysis

# Initialize the trip planner client
planner = OTPTripPlannerClient()

# Generate attendee data using a simple data generator
generator = SimpleAttendeeDataGenerator(planner)
generator.generate()

# Retrieve the generated attendee data as a DataFrame
attendees_df = generator.get_dataframe()

# Separate the data into departure and return trips
departure_df = attendees_df[attendees_df["direction"] == "departure"].reset_index(drop=True)
return_df = attendees_df[attendees_df["direction"] == "return"].reset_index(drop=True)

# Get the list of direct transportation modes (e.g., car, bike, etc.)
direct_modes = generator.get_direct_modes()

# Initialize the carbon calculator for emissions calculations
carbon_calculator = CarbonCalculator()

# Loop through all attendee journeys
for idx in departure_df.index:
    # Get the attendee ID for the current trip
    attendee_id = departure_df.loc[idx, "attendee_id"]

    # Iterate through each direct transportation mode
    for direct_mode in direct_modes:
        # Get the transit modes associated with the current direct mode
        transit_modes = generator.get_transit_modes(direct_mode)

        # Build the modes block for the trip planner query
        modes_block = planner.build_modes_block(direct_mode, transit_modes)

        # Build the departure trip query
        q_dep = planner.build_query(
            origin_lat=departure_df.loc[idx, "origin_lat"],  # Departure origin latitude
            origin_lng=departure_df.loc[idx, "origin_lng"],  # Departure origin longitude
            destination_lat=departure_df.loc[idx, "destination_lat"],  # Destination latitude
            destination_lng=departure_df.loc[idx, "destination_lng"],  # Destination longitude
            time=departure_df.loc[idx, "departure_time"],  # Departure time
            modes_block=modes_block  # Transportation modes block
        )

        # Build the return trip query
        q_ret = planner.build_query(
            origin_lat=return_df.loc[idx, "origin_lat"],  # Return origin latitude
            origin_lng=return_df.loc[idx, "origin_lng"],  # Return origin longitude
            destination_lat=return_df.loc[idx, "destination_lat"],  # Destination latitude
            destination_lng=return_df.loc[idx, "destination_lng"],  # Destination longitude
            time=return_df.loc[idx, "departure_time"],  # Return time
            modes_block=modes_block  # Transportation modes block
        )

        # Send and process the departure query
        planner.send_and_process_query(q_dep, trip_label="Departure", identifier=f"{attendee_id}_dep_{direct_mode}")

        # Send and process the return query
        planner.send_and_process_query(q_ret, trip_label="Return", identifier=f"{attendee_id}_ret_{direct_mode}")

        # Log the processing of the attendee's trip
        print(f"Processed {attendee_id} with direct mode {direct_mode}")

# Save the results of the trip planner, split by direction (departure/return)
planner.save_results_split_by_direction()

# Carbon calculation and analysis
try:
    # Retrieve the departure and return trip results as DataFrames
    dep_results, ret_results = planner.get_departure_and_return_dataframes()

    # Calculate carbon emissions for each leg of the departure and return trips
    dep_emissions = carbon_calculator.process_multi_leg_trips(dep_results)
    ret_emissions = carbon_calculator.process_multi_leg_trips(ret_results)

    # Save the emissions data to CSV files
    dep_emissions.to_csv("generated_data/departure_trips.csv", index=False)
    ret_emissions.to_csv("generated_data/return_trips.csv", index=False)

    # Identify the lowest carbon options for each attendee's departure and return trips
    lowest_carbon_dep = carbon_calculator.select_lowest_carbon_options(dep_emissions)
    lowest_carbon_ret = carbon_calculator.select_lowest_carbon_options(ret_emissions)

    # Save the lowest carbon options to CSV files
    lowest_carbon_dep.to_csv("generated_data/lowest_carbon_departure_options.csv", index=False)
    lowest_carbon_ret.to_csv("generated_data/lowest_carbon_return_options.csv", index=False)

    # Perform transportation analysis using the lowest carbon options
    analysis = StatisticalAnalysis(lowest_carbon_dep, lowest_carbon_ret)

    # Analyze the data with all options: compute metrics, save to CSV, and print summary
    metrics = analysis.analyze(
        output_file='generated_data/lowest_carbon_statistics.csv',
        print_summary=True
    )

# Handle the case where the required CSV files are not found
except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Trip result CSVs not found. Skipping carbon calculation.")

# Handle any other exceptions that may occur
except Exception as e:
    print(f"An error occurred: {e}")