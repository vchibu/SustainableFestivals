from Code.Simulations.fixed_simulations import (
    CarbonSimulation, 
    CostSimulation, 
    LegSimulation, 
    TimeSimulation
)

from Code.ComparativeAnalysis.comparative_analysis import ComparativeAnalysis
import os

def run_all_simulations(print_summary=True, gen_data=True, gen_trips=True, gen_opt_trips=True):
    """Run all four simulation types and return their metrics."""
    results = {}
    
    # Carbon optimization simulation
    print("\n--- Running Carbon Optimization Simulation ---")
    carbon_sim = CarbonSimulation()
    carbon_metrics = carbon_sim(print_summary=print_summary, gen_data=gen_data,
                                gen_trips=gen_trips, gen_opt_trips=gen_opt_trips)
    results['carbon'] = carbon_metrics
    
    # Cost optimization simulation
    print("\n--- Running Cost Optimization Simulation ---")
    cost_sim = CostSimulation()
    cost_metrics = cost_sim(print_summary=print_summary, gen_data=gen_data,
                            gen_trips=gen_trips, gen_opt_trips=gen_opt_trips)
    results['cost'] = cost_metrics
    
    # Leg optimization simulation
    print("\n--- Running Leg Optimization Simulation ---")
    leg_sim = LegSimulation()
    leg_metrics = leg_sim(print_summary=print_summary, gen_data=gen_data,
                          gen_trips=gen_trips, gen_opt_trips=gen_opt_trips)
    results['leg'] = leg_metrics
    
    # Time optimization simulation
    print("\n--- Running Time Optimization Simulation ---")
    time_sim = TimeSimulation()
    time_metrics = time_sim(print_summary=print_summary, gen_data=gen_data,
                            gen_trips=gen_trips, gen_opt_trips=gen_opt_trips)
    results['time'] = time_metrics
    
    return results

def run_single_simulation(sim_type, csv_filename=None, md_filename=None, print_summary=False, gen_data=True, gen_trips=True, gen_opt_trips=True):
    """Run a single simulation of the specified type."""
    sim_classes = {
        'carbon': CarbonSimulation,
        'cost': CostSimulation,
        'leg': LegSimulation,
        'time': TimeSimulation
    }
    
    if sim_type not in sim_classes:
        raise ValueError(f"Invalid simulation type '{sim_type}'. Valid types: {list(sim_classes.keys())}")
    
    print(f"\n--- Running {sim_type.capitalize()} Optimization Simulation ---")
    sim = sim_classes[sim_type]()
    metrics = sim(csv_filename=csv_filename, md_filename=md_filename, print_summary=print_summary,
                   gen_data=gen_data, gen_trips=gen_trips, gen_opt_trips=gen_opt_trips)
    
    return metrics


# Example usage
if __name__ == "__main__":

    # Run all simulations
    all_results = run_all_simulations(print_summary=False, gen_data=False, gen_trips=False, gen_opt_trips=True)

    # Initialize the analyzer (it will find the CSV directory automatically)
    analyzer = ComparativeAnalysis()
    
    # Create output directory if it doesn't exist
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "..", "..", "Data", "ComparativeStatistics")
    os.makedirs(output_dir, exist_ok=True)
    
    # Run the complete analysis
    analyzer.run_analysis(
        csv_output_path=os.path.join(output_dir, "comparative_analysis.csv"),
        md_output_path=os.path.join(output_dir, "comparative_analysis.md")
    )