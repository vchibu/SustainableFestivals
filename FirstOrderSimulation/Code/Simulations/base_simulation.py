"""
Sustainable Transportation Simulation Framework

This module provides a framework for simulating different transportation optimization strategies
using a common codebase to reduce duplication.
"""

import pandas as pd
import os
from Code.DataGeneration.attendee_generator import SimpleAttendeeDataGenerator
from Code.DataGeneration.otp_client import OTPTripPlannerClient
from Code.Calculators.carbon_calculator import CarbonCalculator
from Code.Calculators.cost_calculator import CostCalculator
from Code.Calculators.leg_calculator import LegCalculator
from Code.StatisticalAnalysis.statistical_analysis import StatisticalAnalysis

class BaseTransportationSimulation:
    """Base class for transportation simulations with different optimization strategies."""
    
    def __init__(self):
        # Initialize the core components
        self.planner = OTPTripPlannerClient()
        self.generator = SimpleAttendeeDataGenerator(self.planner)
        self.carbon_calculator = CarbonCalculator()
        self.cost_calculator = CostCalculator()
        self.leg_calculator = LegCalculator()
        self.dep_results = None
        self.ret_results = None
        self.dep_emissions = None
        self.ret_emissions = None
        self.dep_leg = None
        self.ret_leg = None
        self.dep_costs = None
        self.ret_costs = None
        self.dep_final = None
        self.ret_final = None
        self.metrics = None
        
    def _load_attendee_data_from_file(self):
        """Load attendee data from CSV file."""
        script_dir = os.path.dirname(__file__)
        file_path = os.path.join(script_dir, "../../Data/AttendeeData/attendee_data.csv")
        file_path = os.path.normpath(file_path)
        return pd.read_csv(file_path)
    
    def _split_attendee_data_by_direction(self):
        """Split attendee data into departure and return DataFrames."""
        self.departure_df = self.attendees_df[self.attendees_df["direction"] == "departure"].reset_index(drop=True)
        self.return_df = self.attendees_df[self.attendees_df["direction"] == "return"].reset_index(drop=True)
        
    def generate_data(self, gen_data=True):
        """Generate attendee data and separate into departure and return trips."""
        if gen_data:    
            self.generator.generate()
            self.attendees_df = self.generator.get_dataframe()
        else:
            self.attendees_df = self._load_attendee_data_from_file()

        self._split_attendee_data_by_direction()

        # Get transportation modes
        self.direct_modes = self.generator.get_direct_modes()
    
    def _process_bicycle_alternative(self, idx, attendee_id, transit_modes):
        """Process alternative walking mode for bicycle trips."""
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

        # Send and process the queries
        self.planner.send_and_process_query(q_dep_alt, trip_label="Departure", identifier=f"{attendee_id}_dep_BICYCLE")
        self.planner.send_and_process_query(q_ret_alt, trip_label="Return", identifier=f"{attendee_id}_ret_BICYCLE")
    
    def _build_and_process_standard_queries(self, idx, attendee_id, modes_block, direct_mode):
        """Build and process standard departure and return queries."""
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

        # Send and process the queries
        self.planner.send_and_process_query(q_dep, trip_label="Departure", identifier=f"{attendee_id}_dep_{direct_mode}")
        self.planner.send_and_process_query(q_ret, trip_label="Return", identifier=f"{attendee_id}_ret_{direct_mode}")
    
    def _process_single_attendee_mode(self, idx, attendee_id, direct_mode):
        """Process a single attendee's journey for a specific transportation mode."""
        # Get the transit modes associated with the current direct mode
        transit_modes = self.generator.get_transit_modes(direct_mode)

        # Build the modes block for the trip planner query
        modes_block = self.planner.build_modes_block(direct_mode, transit_modes)

        # Handle bicycle special case
        if direct_mode == "BICYCLE":
            self._process_bicycle_alternative(idx, attendee_id, transit_modes)

        # Process standard queries for all modes
        self._build_and_process_standard_queries(idx, attendee_id, modes_block, direct_mode)
        
        # Log the processing of the attendee's trip
        print(f"Processed {attendee_id} with direct mode {direct_mode}")
    
    def _process_single_attendee(self, idx):
        """Process all transportation modes for a single attendee."""
        # Get the attendee ID for the current trip
        attendee_id = self.departure_df.loc[idx, "attendee_id"]

        # Iterate through each direct transportation mode
        for direct_mode in self.direct_modes:
            self._process_single_attendee_mode(idx, attendee_id, direct_mode)
    
    def process_journeys(self):
        """Process all attendee journeys through the trip planner."""
        # Loop through all attendee journeys
        for idx in self.departure_df.index:
            self._process_single_attendee(idx)

        # Save the results of the trip planner, split by direction
        self.planner.save_results_split_by_direction()
    
    def _load_trip_results_from_files(self):
        """Load trip results from CSV files."""
        base_dir = os.path.dirname(__file__)
        dep_path = os.path.normpath(os.path.join(base_dir, "../../Data/GeneratedInitialTrips/departure_trips.csv"))
        ret_path = os.path.normpath(os.path.join(base_dir, "../../Data/GeneratedInitialTrips/return_trips.csv"))
        
        self.dep_results = pd.read_csv(dep_path)
        self.ret_results = pd.read_csv(ret_path)

    def _calculate_leg_count(self):
        """
        Calculate the number of valid legs for each row and add 'leg_count' column.
        A leg is valid if mode, length, and duration are all non-null.

        Parameters:
        df (DataFrame): DataFrame including leg columns.

        Returns:
        DataFrame: DataFrame with added 'leg_count' column.
        """
        self.dep_leg = self.leg_calculator._calculate_leg_count(self.dep_results)
        self.ret_leg = self.leg_calculator._calculate_leg_count(self.ret_results)
        
    def _calculate_emissions(self):
        """Calculate carbon emissions for departure and return trips."""
        self.dep_emissions = self.carbon_calculator.process_multi_leg_trips(self.dep_leg)
        self.ret_emissions = self.carbon_calculator.process_multi_leg_trips(self.ret_leg)
    
    def _calculate_costs(self):
        """Calculate costs for departure and return trips."""
        self.dep_costs = self.cost_calculator.process_multi_leg_trips(self.dep_emissions)
        self.ret_costs = self.cost_calculator.process_multi_leg_trips(self.ret_emissions)
    
    def calculate_emissions_and_costs(self, gen_trips=True):
        """Calculate emissions and costs for all trips."""
        try:
            if gen_trips:
                # Retrieve the departure and return trip results
                self.dep_results, self.ret_results = self.planner.get_departure_and_return_dataframes()
            else:
                self._load_trip_results_from_files()

            # Calculate the number of legs for each trip
            self._calculate_leg_count()

            # Calculate carbon emissions
            self._calculate_emissions()

            # Calculate costs
            self._calculate_costs()

            self.dep_final = self.dep_costs.copy()
            self.ret_final = self.ret_costs.copy()
            
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
    
    def _generate_default_filenames(self):
        """Generate default filenames for CSV and MD outputs."""
        base_name = self.__class__.__name__.lower().replace('simulation', '')
        csv_filename = f"min_{base_name}_metrics.csv"
        md_filename = f"min_{base_name}_report.md"
        return csv_filename, md_filename
    
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
    
    def _run_simulation_steps(self, gen_data, gen_trips, gen_opt_trips):
        """Execute the main simulation steps."""
        # Generate attendee data
        self.generate_data(gen_data)

        if gen_trips:
            # Process all journeys
            self.process_journeys()
        
        # Calculate emissions and costs
        return self.calculate_emissions_and_costs(gen_trips)
        
    def __call__(self, csv_filename=None, md_filename=None, print_summary=False, gen_data=True, gen_trips=True, gen_opt_trips=True):
        """Run the entire simulation."""
        if csv_filename is None or md_filename is None:
            default_csv, default_md = self._generate_default_filenames()
            csv_filename = csv_filename or default_csv
            md_filename = md_filename or default_md
            
        # Run the main simulation steps
        if self._run_simulation_steps(gen_data, gen_trips, gen_opt_trips):
            # Select optimal trips based on the optimization strategy
            self.select_optimal_trips(gen_opt_trips)
            
            # Analyze the results and generate statistics
            return self.analyze_results(csv_filename, md_filename, print_summary)
        
        return None

