import os
import pandas as pd
from Code.Simulations.base_simulation import BaseTransportationSimulation
from Code.Calculators.leg_calculator import LegCalculator
from Code.Calculators.time_calculator import TimeCalculator
from Code.Calculators.RealisticCalculator.realistic_calculator import RealisticCalculator


class CarbonSimulation(BaseTransportationSimulation):
    """Simulation that optimizes for minimum carbon emissions."""
    
    def _get_chosen_trips_directory(self):
        """Get the directory path for chosen trips."""
        base_dir = os.path.dirname(__file__)
        chosen_dir = os.path.normpath(os.path.join(base_dir, "../../Data/ChosenTrips"))
        os.makedirs(chosen_dir, exist_ok=True)
        return chosen_dir
    
    def _save_optimal_trips(self, chosen_dir):
        """Save optimal trips to CSV files."""
        self.optimal_dep.to_csv(os.path.join(chosen_dir, "lowest_carbon_departure.csv"), index=False)
        self.optimal_ret.to_csv(os.path.join(chosen_dir, "lowest_carbon_return.csv"), index=False)
    
    def _load_optimal_trips(self, chosen_dir):
        """Load optimal trips from CSV files."""
        dep_path = os.path.join(chosen_dir, "lowest_carbon_departure.csv")
        ret_path = os.path.join(chosen_dir, "lowest_carbon_return.csv")
        
        self.optimal_dep = pd.read_csv(dep_path)
        self.optimal_ret = pd.read_csv(ret_path)
    
    def select_optimal_trips(self, gen_opt_trips):
        """Select trips with the lowest carbon emissions."""
        chosen_dir = self._get_chosen_trips_directory()
        
        if gen_opt_trips:
            # Identify the lowest carbon options
            self.optimal_dep = self.carbon_calculator.select_lowest_carbon_options(self.dep_final)
            self.optimal_ret = self.carbon_calculator.select_lowest_carbon_options(self.ret_final)
            
            # Save to CSV
            self._save_optimal_trips(chosen_dir)
        else: 
            # Load from CSV
            self._load_optimal_trips(chosen_dir)

class CostSimulation(BaseTransportationSimulation):
    """Simulation that optimizes for minimum cost."""
    
    def _get_chosen_trips_directory(self):
        """Get the directory path for chosen trips."""
        base_dir = os.path.dirname(__file__)
        chosen_dir = os.path.normpath(os.path.join(base_dir, "../../Data/ChosenTrips"))
        os.makedirs(chosen_dir, exist_ok=True)
        return chosen_dir
    
    def _save_optimal_trips(self, chosen_dir):
        """Save optimal trips to CSV files."""
        self.optimal_dep.to_csv(os.path.join(chosen_dir, "lowest_cost_departure.csv"), index=False)
        self.optimal_ret.to_csv(os.path.join(chosen_dir, "lowest_cost_return.csv"), index=False)
    
    def _load_optimal_trips(self, chosen_dir):
        """Load optimal trips from CSV files."""
        dep_path = os.path.join(chosen_dir, "lowest_cost_departure.csv")
        ret_path = os.path.join(chosen_dir, "lowest_cost_return.csv")
        
        self.optimal_dep = pd.read_csv(dep_path)
        self.optimal_ret = pd.read_csv(ret_path)
    
    def select_optimal_trips(self, gen_opt_trips):
        """Select trips with the lowest cost."""
        chosen_dir = self._get_chosen_trips_directory()
        
        if gen_opt_trips:
            # Identify the lowest cost options
            self.optimal_dep = self.cost_calculator.select_lowest_cost_options(self.dep_final)
            self.optimal_ret = self.cost_calculator.select_lowest_cost_options(self.ret_final)
            
            # Save to CSV
            self._save_optimal_trips(chosen_dir)
        else:
            # Load from CSV
            self._load_optimal_trips(chosen_dir)


class LegSimulation(BaseTransportationSimulation):
    """Simulation that optimizes for minimum number of legs in a journey."""
    
    def __init__(self):
        super().__init__()
        self.leg_calculator = LegCalculator()
    
    def _get_chosen_trips_directory(self):
        """Get the directory path for chosen trips."""
        base_dir = os.path.dirname(__file__)
        chosen_dir = os.path.normpath(os.path.join(base_dir, "../../Data/ChosenTrips"))
        os.makedirs(chosen_dir, exist_ok=True)
        return chosen_dir
    
    def _save_optimal_trips(self, chosen_dir):
        """Save optimal trips to CSV files."""
        self.optimal_dep.to_csv(os.path.join(chosen_dir, "least_legs_departure.csv"), index=False)
        self.optimal_ret.to_csv(os.path.join(chosen_dir, "least_legs_return.csv"), index=False)
    
    def _load_optimal_trips(self, chosen_dir):
        """Load optimal trips from CSV files."""
        dep_path = os.path.join(chosen_dir, "least_legs_departure.csv")
        ret_path = os.path.join(chosen_dir, "least_legs_return.csv")
        
        self.optimal_dep = pd.read_csv(dep_path)
        self.optimal_ret = pd.read_csv(ret_path)
    
    def select_optimal_trips(self, gen_opt_trips):
        """Select trips with the least number of legs."""
        chosen_dir = self._get_chosen_trips_directory()
        
        if gen_opt_trips:
            # Identify options with least legs
            self.optimal_dep = self.leg_calculator.select_least_leg_options(self.dep_final)
            self.optimal_ret = self.leg_calculator.select_least_leg_options(self.ret_final)
            
            # Save to CSV
            self._save_optimal_trips(chosen_dir)
        else:
            # Load from CSV
            self._load_optimal_trips(chosen_dir)


class TimeSimulation(BaseTransportationSimulation):
    """Simulation that optimizes for minimum journey time."""
    
    def __init__(self):
        super().__init__()
        self.time_calculator = TimeCalculator()
    
    def _get_chosen_trips_directory(self):
        """Get the directory path for chosen trips."""
        base_dir = os.path.dirname(__file__)
        chosen_dir = os.path.normpath(os.path.join(base_dir, "../../Data/ChosenTrips"))
        os.makedirs(chosen_dir, exist_ok=True)
        return chosen_dir
    
    def _save_optimal_trips(self, chosen_dir):
        """Save optimal trips to CSV files."""
        self.optimal_dep.to_csv(os.path.join(chosen_dir, "lowest_time_departure.csv"), index=False)
        self.optimal_ret.to_csv(os.path.join(chosen_dir, "lowest_time_return.csv"), index=False)
    
    def _load_optimal_trips(self, chosen_dir):
        """Load optimal trips from CSV files."""
        dep_path = os.path.join(chosen_dir, "lowest_time_departure.csv")
        ret_path = os.path.join(chosen_dir, "lowest_time_return.csv")
        
        self.optimal_dep = pd.read_csv(dep_path)
        self.optimal_ret = pd.read_csv(ret_path)
    
    def select_optimal_trips(self, gen_opt_trips):
        """Select trips with the lowest travel time."""
        chosen_dir = self._get_chosen_trips_directory()
        
        if gen_opt_trips:
            # Identify the lowest time options
            self.optimal_dep = self.time_calculator.select_lowest_time_options(self.dep_final)
            self.optimal_ret = self.time_calculator.select_lowest_time_options(self.ret_final)
            
            # Save to CSV
            self._save_optimal_trips(chosen_dir)
        else:
            # Load from CSV
            self._load_optimal_trips(chosen_dir)


class RealisticSimulation(BaseTransportationSimulation):
    """Simulation that selects trips based on realistic priorities."""
    
    def __init__(self):
        super().__init__()
        self.realistic_calculator = RealisticCalculator()
    
    def _get_chosen_trips_directory(self):
        """Get the directory path for chosen trips."""
        base_dir = os.path.dirname(__file__)
        chosen_dir = os.path.normpath(os.path.join(base_dir, "../../Data/ChosenTrips"))
        os.makedirs(chosen_dir, exist_ok=True)
        return chosen_dir
    
    def _save_optimal_trips(self, chosen_dir):
        """Save optimal trips to CSV files."""
        self.optimal_dep.to_csv(os.path.join(chosen_dir, "realistic_departure.csv"), index=False)
        self.optimal_ret.to_csv(os.path.join(chosen_dir, "realistic_return.csv"), index=False)
    
    def _load_optimal_trips(self, chosen_dir):
        """Load optimal trips from CSV files."""
        dep_path = os.path.join(chosen_dir, "realistic_departure.csv")
        ret_path = os.path.join(chosen_dir, "realistic_return.csv")
        
        self.optimal_dep = pd.read_csv(dep_path)
        self.optimal_ret = pd.read_csv(ret_path)
    
    def select_optimal_trips(self, gen_opt_trips):
        """Select trips based on realistic priorities."""
        chosen_dir = self._get_chosen_trips_directory()
        
        if gen_opt_trips:
            # Assign priorities and select best trips
            self.optimal_dep, self.optimal_ret = self.realistic_calculator.select_best_trips(self.dep_final, self.ret_final)

            # Save to CSV
            self._save_optimal_trips(chosen_dir)
        else:
            # Load from CSV
            self._load_optimal_trips(chosen_dir)