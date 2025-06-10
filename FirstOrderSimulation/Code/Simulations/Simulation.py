"""
Sustainable Transportation Simulation Framework

This module provides a framework for simulating different transportation optimization strategies
using a common codebase to reduce duplication.
"""

import pandas as pd
import os

from Code.DataGeneration.SimpleDataGenerator import SimpleAttendeeDataGenerator
from Code.DataGeneration.OTPTripPlannerClient import OTPTripPlannerClient
from Code.Calculators.CarbonCalculator import CarbonCalculator
from Code.Calculators.CostCalculator import CostCalculator
from Code.Calculators.TimeCalculator import TimeCalculator
from Code.Calculators.LegCalculator import LegCalculator
from Code.Analysis.StatisticalAnalysis import StatisticalAnalysis

class BaseTransportationSimulation:
    """Base class for transportation simulations with different optimization strategies."""
    
    def __init__(self):
        # Initialize the core components
        self.planner = OTPTripPlannerClient()
        self.generator = SimpleAttendeeDataGenerator(self.planner)
        self.carbon_calculator = CarbonCalculator()
        self.cost_calculator = CostCalculator()
        self.dep_results = None
        self.ret_results = None
        self.dep_costs = None
        self.ret_costs = None
        self.metrics = None
        
    def generate_data(self, gen_data=True):
        """Generate attendee data and separate into departure and return trips."""
        if gen_data:    
            self.generator.generate()
            self.attendees_df = self.generator.get_dataframe()
            
        else:
            script_dir = os.path.dirname(__file__)
            file_path = os.path.join(script_dir, "../../Data/AttendeeData/attendee_data.csv")
            file_path = os.path.normpath(file_path)
            self.attendees_df = pd.read_csv(file_path)

        self.departure_df = self.attendees_df[self.attendees_df["direction"] == "departure"].reset_index(drop=True)
        self.return_df = self.attendees_df[self.attendees_df["direction"] == "return"].reset_index(drop=True)

        # Get transportation modes
        self.direct_modes = self.generator.get_direct_modes()
    
    def process_journeys(self):
        """Process all attendee journeys through the trip planner."""
        # Loop through all attendee journeys
        for idx in self.departure_df.index:
            # Get the attendee ID for the current trip
            attendee_id = self.departure_df.loc[idx, "attendee_id"]

            # Iterate through each direct transportation mode
            for direct_mode in self.direct_modes:
                # Get the transit modes associated with the current direct mode
                transit_modes = self.generator.get_transit_modes(direct_mode)

                # Build the modes block for the trip planner query
                modes_block = self.planner.build_modes_block(direct_mode, transit_modes)

                if direct_mode == "BICYCLE":
                    # For walking, we only need the origin and destination coordinates
                    modes_block_alt = self.planner.build_modes_block("WALK", transit_modes)

                    # Build the departure trip query
                    q_dep_alt = self.planner.build_query(
                        origin_lat=self.departure_df.loc[idx, "origin_lat"],
                        origin_lng=self.departure_df.loc[idx, "origin_lng"],
                        destination_lat=self.departure_df.loc[idx, "destination_lat"],
                        destination_lng=self.departure_df.loc[idx, "destination_lng"],
                        time=self.departure_df.loc[idx, "departure_time"],
                        modes_block=modes_block_alt,
                        dep_or_ret=True
                    )

                    # Build the return trip query
                    q_ret_alt = self.planner.build_query(
                        origin_lat=self.return_df.loc[idx, "origin_lat"],
                        origin_lng=self.return_df.loc[idx, "origin_lng"],
                        destination_lat=self.return_df.loc[idx, "destination_lat"],
                        destination_lng=self.return_df.loc[idx, "destination_lng"],
                        time=self.return_df.loc[idx, "departure_time"],
                        modes_block=modes_block_alt,
                        dep_or_ret=False
                    )

                    # Send and process the departure query
                    self.planner.send_and_process_query(q_dep_alt, trip_label="Departure", identifier=f"{attendee_id}_dep_{direct_mode}")

                    # Send and process the return query
                    self.planner.send_and_process_query(q_ret_alt, trip_label="Return", identifier=f"{attendee_id}_ret_{direct_mode}")

                # Build the departure trip query
                q_dep = self.planner.build_query(
                    origin_lat=self.departure_df.loc[idx, "origin_lat"],
                    origin_lng=self.departure_df.loc[idx, "origin_lng"],
                    destination_lat=self.departure_df.loc[idx, "destination_lat"],
                    destination_lng=self.departure_df.loc[idx, "destination_lng"],
                    time=self.departure_df.loc[idx, "departure_time"],
                    modes_block=modes_block,
                    dep_or_ret=True
                )

                # Build the return trip query
                q_ret = self.planner.build_query(
                    origin_lat=self.return_df.loc[idx, "origin_lat"],
                    origin_lng=self.return_df.loc[idx, "origin_lng"],
                    destination_lat=self.return_df.loc[idx, "destination_lat"],
                    destination_lng=self.return_df.loc[idx, "destination_lng"],
                    time=self.return_df.loc[idx, "departure_time"],
                    modes_block=modes_block,
                    dep_or_ret=False
                )

                # Send and process the departure query
                self.planner.send_and_process_query(q_dep, trip_label="Departure", identifier=f"{attendee_id}_dep_{direct_mode}")

                # Send and process the return query
                self.planner.send_and_process_query(q_ret, trip_label="Return", identifier=f"{attendee_id}_ret_{direct_mode}")

                # Log the processing of the attendee's trip
                print(f"Processed {attendee_id} with direct mode {direct_mode}")

        # Save the results of the trip planner, split by direction
        self.planner.save_results_split_by_direction()
    
    def calculate_emissions_and_costs(self, gen_trips=True):
        """Calculate emissions and costs for all trips."""
        try:

            if gen_trips:
                # Retrieve the departure and return trip results
                self.dep_results, self.ret_results = self.planner.get_departure_and_return_dataframes()
            else:
                base_dir = os.path.dirname(__file__)
                dep_path = os.path.normpath(os.path.join(base_dir, "../../Data/GeneratedInitialTrips/departure_trips.csv"))
                ret_path = os.path.normpath(os.path.join(base_dir, "../../Data/GeneratedInitialTrips/return_trips.csv"))
                
                self.dep_results = pd.read_csv(dep_path)
                self.ret_results = pd.read_csv(ret_path)

            # Calculate carbon emissions
            self.dep_emissions = self.carbon_calculator.process_multi_leg_trips(self.dep_results)
            self.ret_emissions = self.carbon_calculator.process_multi_leg_trips(self.ret_results)

            # Calculate costs
            self.dep_costs = self.cost_calculator.process_multi_leg_trips(self.dep_emissions)
            self.ret_costs = self.cost_calculator.process_multi_leg_trips(self.ret_emissions)
            
            return True
            
        except FileNotFoundError as e:
            print(f"Error: {e}")
            print("Trip result CSVs not found. Skipping calculations.")
            return False
            
        except Exception as e:
            print(f"An error occurred: {e}")
            return False
    
    def select_optimal_trips(self, gen_opt_trips):
        """
        Select the optimal trips based on optimization strategy.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement select_optimal_trips method")
    
    def analyze_results(self, csv_filename, md_filename, print_summary=False):
        """Analyze the optimal trips and generate statistics."""
        # Perform statistical analysis using the selected options
        stat_analysis = StatisticalAnalysis(self.optimal_dep, self.optimal_ret)

        # Analyze the data with all options: compute metrics, save to CSV, and print summary
        self.metrics = stat_analysis.analyze(
            output_csv=f"Data/FinalStatistics/CSVs/{csv_filename}",
            output_md=f"Data/FinalStatistics/MDs/{md_filename}",
            print_summary=print_summary
        )
        
        return self.metrics
        
    def __call__(self, csv_filename=None, md_filename=None, print_summary=False, gen_data=True, gen_trips=True, gen_opt_trips=True):
        """Run the entire simulation."""

        if csv_filename is None:
            csv_filename = f"min_{self.__class__.__name__.lower().replace('simulation', '')}_metrics.csv"
        if md_filename is None:
            md_filename = f"min_{self.__class__.__name__.lower().replace('simulation', '')}_report.md"
            
        # Generate attendee data
        self.generate_data(gen_data)

        if gen_trips:
            # Process all journeys
            self.process_journeys()
        
        # Calculate emissions and costs
        if self.calculate_emissions_and_costs(gen_trips):
            # Select optimal trips based on the optimization strategy
            self.select_optimal_trips(gen_opt_trips)
            
            # Analyze the results and generate statistics
            return self.analyze_results(csv_filename, md_filename, print_summary)
        
        return None


class CarbonSimulation(BaseTransportationSimulation):
    """Simulation that optimizes for minimum carbon emissions."""
    
    def select_optimal_trips(self, gen_opt_trips):
        """Select trips with the lowest carbon emissions."""

        if gen_opt_trips:
            # Identify the lowest carbon options
            self.optimal_dep = self.carbon_calculator.select_lowest_carbon_options(self.dep_costs)
            self.optimal_ret = self.carbon_calculator.select_lowest_carbon_options(self.ret_costs)
        
            base_dir = os.path.dirname(__file__)
            chosen_dir = os.path.normpath(os.path.join(base_dir, "../../Data/ChosenTrips"))

            # Make sure the directory exists before saving
            os.makedirs(chosen_dir, exist_ok=True)

            # Save to CSV
            self.optimal_dep.to_csv(os.path.join(chosen_dir, "lowest_carbon_departure.csv"), index=False)
            self.optimal_ret.to_csv(os.path.join(chosen_dir, "lowest_carbon_return.csv"), index=False)

        else: 
            base_dir = os.path.dirname(__file__)
            chosen_dir = os.path.normpath(os.path.join(base_dir, "../../Data/ChosenTrips"))

            dep_path = os.path.join(chosen_dir, "lowest_carbon_departure.csv")
            ret_path = os.path.join(chosen_dir, "lowest_carbon_return.csv")

            self.optimal_dep = pd.read_csv(dep_path)
            self.optimal_ret = pd.read_csv(ret_path)


class CostSimulation(BaseTransportationSimulation):
    """Simulation that optimizes for minimum cost."""
    
    def select_optimal_trips(self, gen_opt_trips):
        """Select trips with the lowest cost."""
        if gen_opt_trips:
            # Identify the lowest cost options
            self.optimal_dep = self.cost_calculator.select_lowest_cost_options(self.dep_costs)
            self.optimal_ret = self.cost_calculator.select_lowest_cost_options(self.ret_costs)
            
            base_dir = os.path.dirname(__file__)
            chosen_dir = os.path.normpath(os.path.join(base_dir, "../../Data/ChosenTrips"))

            # Make sure the directory exists before saving
            os.makedirs(chosen_dir, exist_ok=True)

            # Save to CSV
            self.optimal_dep.to_csv(os.path.join(chosen_dir, "lowest_cost_departure.csv"), index=False)
            self.optimal_ret.to_csv(os.path.join(chosen_dir, "lowest_cost_return.csv"), index=False)

        else:
            base_dir = os.path.dirname(__file__)
            chosen_dir = os.path.normpath(os.path.join(base_dir, "../../Data/ChosenTrips"))

            dep_path = os.path.join(chosen_dir, "lowest_cost_departure.csv")
            ret_path = os.path.join(chosen_dir, "lowest_cost_return.csv")

            self.optimal_dep = pd.read_csv(dep_path)
            self.optimal_ret = pd.read_csv(ret_path)

class LegSimulation(BaseTransportationSimulation):
    """Simulation that optimizes for minimum number of legs in a journey."""
    
    def __init__(self):
        super().__init__()
        self.leg_calculator = LegCalculator()
    
    def select_optimal_trips(self, gen_opt_trips):
        """Select trips with the least number of legs."""

        if gen_opt_trips:
            # Identify options with least legs
            self.optimal_dep = self.leg_calculator.select_least_leg_options(self.dep_costs)
            self.optimal_ret = self.leg_calculator.select_least_leg_options(self.ret_costs)
            
            base_dir = os.path.dirname(__file__)
            chosen_dir = os.path.normpath(os.path.join(base_dir, "../../Data/ChosenTrips"))

            # Make sure the directory exists before saving
            os.makedirs(chosen_dir, exist_ok=True)

            # Save to CSV
            self.optimal_dep.to_csv(os.path.join(chosen_dir, "least_legs_departure.csv"), index=False)
            self.optimal_ret.to_csv(os.path.join(chosen_dir, "least_legs_return.csv"), index=False)
        else:
            base_dir = os.path.dirname(__file__)
            chosen_dir = os.path.normpath(os.path.join(base_dir, "../../Data/ChosenTrips"))

            dep_path = os.path.join(chosen_dir, "least_legs_departure.csv")
            ret_path = os.path.join(chosen_dir, "least_legs_return.csv")

            self.optimal_dep = pd.read_csv(dep_path)
            self.optimal_ret = pd.read_csv(ret_path)

class TimeSimulation(BaseTransportationSimulation):
    """Simulation that optimizes for minimum journey time."""
    
    def __init__(self):
        super().__init__()
        self.time_calculator = TimeCalculator()
    
    def select_optimal_trips(self, gen_opt_trips):
        """Select trips with the lowest travel time."""
        if gen_opt_trips:
            # Identify the lowest time options
            self.optimal_dep = self.time_calculator.select_lowest_time_options(self.dep_costs)
            self.optimal_ret = self.time_calculator.select_lowest_time_options(self.ret_costs)
            
            base_dir = os.path.dirname(__file__)
            chosen_dir = os.path.normpath(os.path.join(base_dir, "../../Data/ChosenTrips"))

            # Make sure the directory exists before saving
            os.makedirs(chosen_dir, exist_ok=True)

            # Save to CSV
            self.optimal_dep.to_csv(os.path.join(chosen_dir, "lowest_time_departure.csv"), index=False)
            self.optimal_ret.to_csv(os.path.join(chosen_dir, "lowest_time_return.csv"), index=False)

        else:

            base_dir = os.path.dirname(__file__)
            chosen_dir = os.path.normpath(os.path.join(base_dir, "../../Data/ChosenTrips"))

            dep_path = os.path.join(chosen_dir, "lowest_time_departure.csv")
            ret_path = os.path.join(chosen_dir, "lowest_time_return.csv")

            self.optimal_dep = pd.read_csv(dep_path)
            self.optimal_ret = pd.read_csv(ret_path)