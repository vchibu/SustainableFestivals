from SimpleDataGenerator import SimpleAttendeeDataGenerator
from OTPTripPlannerClient import OTPTripPlannerClient
from CarbonCalculator import CarbonCalculator

planner = OTPTripPlannerClient()
generator = SimpleAttendeeDataGenerator(planner)
generator.generate()
attendees_df = generator.get_dataframe()
departure_df = attendees_df[attendees_df["direction"] == "departure"].reset_index(drop=True)
return_df = attendees_df[attendees_df["direction"] == "return"].reset_index(drop=True)
direct_modes = generator.get_direct_modes()
# Carbon calculation
carbon_calculator = CarbonCalculator()

# Loop through all attendee journeys
for idx in departure_df.index:
    attendee_id = departure_df.loc[idx, "attendee_id"]

    for direct_mode in direct_modes:
        transit_modes = generator.get_transit_modes(direct_mode)
        modes_block = planner.build_modes_block(direct_mode, transit_modes)

        # Build departure query
        q_dep = planner.build_query(
            origin_lat=departure_df.loc[idx, "origin_lat"],
            origin_lng=departure_df.loc[idx, "origin_lng"],
            destination_lat=departure_df.loc[idx, "destination_lat"],
            destination_lng=departure_df.loc[idx, "destination_lng"],
            time=departure_df.loc[idx, "departure_time"],
            modes_block=modes_block
        )

        # Build return query
        q_ret = planner.build_query(
            origin_lat=return_df.loc[idx, "origin_lat"],
            origin_lng=return_df.loc[idx, "origin_lng"],
            destination_lat=return_df.loc[idx, "destination_lat"],
            destination_lng=return_df.loc[idx, "destination_lng"],
            time=return_df.loc[idx, "departure_time"],
            modes_block=modes_block
        )

        # Send and process
        planner.send_and_process_query(q_dep, trip_label="Departure", identifier=f"{attendee_id}_dep_{direct_mode}")
        planner.send_and_process_query(q_ret, trip_label="Return", identifier=f"{attendee_id}_ret_{direct_mode}")

        print(f"Processed {attendee_id} with direct mode {direct_mode}")

# Save results
planner.save_results_split_by_direction()

# Carbon calculation
try:
    # Read the CSV files provided in the documents
    dep_results, ret_results = planner.get_departure_and_return_dataframes()

    # Process trips to add carbon footprints for each leg and calculate total
    dep_emissions = carbon_calculator.process_multi_leg_trips(dep_results)
    ret_emissions = carbon_calculator.process_multi_leg_trips(ret_results)

    # Save results to CSV files
    dep_emissions.to_csv("generated_data/departure_trips.csv", index=False)
    ret_emissions.to_csv("generated_data/return_trips.csv", index=False)
    
    # Find lowest carbon options for each attendee
    lowest_carbon_dep = carbon_calculator.select_lowest_carbon_options(dep_emissions)
    lowest_carbon_ret = carbon_calculator.select_lowest_carbon_options(ret_emissions)
    
    # Save lowest carbon options
    lowest_carbon_dep.to_csv("generated_data/lowest_carbon_departure_options.csv", index=False)
    lowest_carbon_ret.to_csv("generated_data/lowest_carbon_return_options.csv", index=False)
    
    print("Carbon calculations completed and saved.")
    print("Lowest carbon options also generated.")
except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Trip result CSVs not found. Skipping carbon calculation.")
except Exception as e:
    print(f"An error occurred: {e}")