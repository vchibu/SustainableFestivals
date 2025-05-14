import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from io import StringIO

class ComparativeAnalysis:
    """
    A class that compares different final statistics for different simulations.
    """
    
    def __init__(self, custom_priorities=None):
        """
        Initialize the ComparativeAnalysis class.
        
        Parameters:
        -----------
        custom_priorities : dict, optional
            Dictionary mapping custom priority keys to display names
            (e.g., {"bruh": "Custom Bruh Optimization"})
        """
        self.data = {}
        self.priorities = {}  # Dictionary to store the optimization priority for each simulation
        self.report = ""
        self.metrics_to_compare = [
            "total_carbon_footprint", 
            "avg_carbon_footprint",
            "total_cost", 
            "avg_cost",
            "total_travel_time", 
            "avg_travel_time",
            "total_legs", 
            "avg_legs_per_attendee"
        ]
        self.metric_display_names = {
            "total_carbon_footprint": "Total Carbon Footprint (g CO2)",
            "avg_carbon_footprint": "Average Carbon Footprint per Attendee (g CO2)",
            "total_cost": "Total Cost ($)",
            "avg_cost": "Average Cost per Attendee ($)",
            "total_travel_time": "Total Travel Time (minutes)",
            "avg_travel_time": "Average Travel Time per Attendee (minutes)",
            "total_legs": "Total Number of Trip Legs",
            "avg_legs_per_attendee": "Average Legs per Attendee"
        }
        # Default priority display names
        self.priority_display_names = {
            "carbon": "Lowest Carbon Footprint",
            "cost": "Lowest Cost",
            "time": "Shortest Travel Time",
            "legs": "Fewest Trip Legs"
        }
        
        # Add custom priorities if provided
        if custom_priorities:
            self.priority_display_names.update(custom_priorities)
        
    def load_data_files(self, file_priorities):
        """
        Load data from CSV files into pandas DataFrames with their optimization priorities.
        
        Parameters:
        -----------
        file_priorities : dict
            Dictionary mapping file paths to their optimization priorities
            (e.g., {"path/to/file1.csv": "carbon", "path/to/file2.csv": "cost"})
            Valid priorities: "carbon", "cost", "time", "legs"
        """
        for file_path, priority in file_priorities.items():
            if not os.path.exists(file_path):
                print(f"File {file_path} not found.")
                continue
                
            file_name = os.path.basename(file_path).replace('.csv', '')
            self.data[file_name] = pd.read_csv(file_path)
            self.priorities[file_name] = priority
        
        return self
    
    def read_csv_string(self, csv_string_priorities):
        """
        Read CSV data from strings with their optimization priorities.
        
        Parameters:
        -----------
        csv_string_priorities : dict
            Dictionary mapping names to tuples of (csv_string, priority)
            (e.g., {"simulation1": (csv_string1, "carbon"), "simulation2": (csv_string2, "cost")})
        """
        for name, (csv_string, priority) in csv_string_priorities.items():
            self.data[name] = pd.read_csv(StringIO(csv_string))
            self.priorities[name] = priority
        return self
    
    def _get_metric_value(self, df, category, metric):
        """
        Get the value of a specific metric in a specific category from a DataFrame.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame containing the data
        category : str
            Category to filter by
        metric : str
            Metric to get the value of
            
        Returns:
        --------
        float
            Value of the metric
        """
        value = df[(df['Category'] == category) & (df['Metric'] == metric)]['Value'].values
        if len(value) > 0:
            return value[0]
        return None
    
    def _get_simulation_label(self, sim_name):
        """
        Get a formatted label for a simulation including its optimization priority.
        
        Parameters:
        -----------
        sim_name : str
            The name of the simulation
            
        Returns:
        --------
        str
            Formatted simulation label
        """
        priority = self.priorities.get(sim_name, "Unknown")
        # If it's a custom priority not in our display names, use the priority itself capitalized
        priority_display = self.priority_display_names.get(priority, priority.capitalize())
        return f"{sim_name} ({priority_display})"
    
    def generate_comparison_table(self, categories=None):
        """
        Generate a comparison table of metrics across different simulations.
        
        Parameters:
        -----------
        categories : list
            List of categories to include in the comparison
            
        Returns:
        --------
        str
            Markdown table comparing metrics
        """
        if not self.data:
            return "No data loaded."
            
        if not categories:
            # Try to infer categories from the data
            first_data_key = list(self.data.keys())[0]
            categories = self.data[first_data_key]['Category'].unique().tolist()
        
        comparison_tables = []
        
        for category in categories:
            table = f"### {category.capitalize()} Metrics\n\n"
            table += "| Metric | " + " | ".join([self._get_simulation_label(k) for k in self.data.keys()]) + " |\n"
            table += "| ------ | " + " | ".join(["------" for _ in self.data.keys()]) + " |\n"
            
            for metric in self.metrics_to_compare:
                display_name = self.metric_display_names.get(metric, metric)
                table += f"| {display_name} | "
                
                metric_values = []
                for data_key in self.data.keys():
                    value = self._get_metric_value(self.data[data_key], category, metric)
                    formatted_value = f"{value:.2f}" if value is not None else "N/A"
                    table += f"{formatted_value} | "
                    if value is not None:
                        metric_values.append((data_key, value))
                
                # Highlight the best value if possible
                if len(metric_values) > 0 and any(["carbon" in metric or "cost" in metric or "time" in metric or "legs" in metric for metric in [m[0] for m in metric_values]]):
                    best_sim, best_value = min(metric_values, key=lambda x: x[1])
                    table = table.replace(f"| {best_value:.2f} |", f"| **{best_value:.2f}** |")
                
                table += "\n"
            
            comparison_tables.append(table)
        
        return "\n\n".join(comparison_tables)
    
    def generate_mode_comparison(self, categories=None):
        """
        Generate a comparison of transportation modes across different simulations.
        
        Parameters:
        -----------
        categories : list
            List of categories to include in the comparison
            
        Returns:
        --------
        str
            Markdown text with mode comparisons
        """
        if not self.data:
            return "No data loaded."
            
        if not categories:
            # Try to infer categories from the data
            first_data_key = list(self.data.keys())[0]
            categories = self.data[first_data_key]['Category'].unique().tolist()
        
        mode_comparison = []
        
        # Direct modes
        direct_modes = ["WALK", "BICYCLE", "CAR"]
        
        for category in categories:
            comparison = f"### {category.capitalize()} Transportation Mode Analysis\n\n"
            comparison += "#### Direct Modes\n\n"
            
            # Table for direct modes
            comparison += "| Mode | " + " | ".join([self._get_simulation_label(k) for k in self.data.keys()]) + " |\n"
            comparison += "| ---- | " + " | ".join(["----" for _ in self.data.keys()]) + " |\n"
            
            for mode in direct_modes:
                comparison += f"| {mode} | "
                
                for data_key in self.data.keys():
                    count = self._get_metric_value(self.data[data_key], category, f"direct_mode_{mode}_count")
                    proportion = self._get_metric_value(self.data[data_key], category, f"direct_mode_{mode}_proportion")
                    
                    if count is not None and proportion is not None:
                        comparison += f"{int(count)} ({proportion:.1%}) | "
                    else:
                        comparison += "N/A | "
                
                comparison += "\n"
            
            # Transit modes
            transit_modes = ["TRAM", "SUBWAY", "BUS", "RAIL"]
            
            comparison += "\n#### Transit Modes\n\n"
            comparison += "| Mode | " + " | ".join([self._get_simulation_label(k) for k in self.data.keys()]) + " |\n"
            comparison += "| ---- | " + " | ".join(["----" for _ in self.data.keys()]) + " |\n"
            
            for mode in transit_modes:
                comparison += f"| {mode} | "
                
                for data_key in self.data.keys():
                    count = self._get_metric_value(self.data[data_key], category, f"transit_mode_{mode}_count")
                    proportion = self._get_metric_value(self.data[data_key], category, f"transit_mode_{mode}_proportion")
                    
                    if count is not None and proportion is not None:
                        comparison += f"{int(count)} ({proportion:.1%}) | "
                    else:
                        comparison += "N/A | "
                
                comparison += "\n"
            
            mode_comparison.append(comparison)
        
        return "\n\n".join(mode_comparison)
    
    def generate_comparative_charts(self, output_dir=None):
        """
        Generate comparative charts for the metrics.
        
        Parameters:
        -----------
        output_dir : str
            Directory to save the charts to
            
        Returns:
        --------
        str
            Markdown text with embedded charts
        """
        if not self.data:
            return "No data loaded."
            
        # Create charts directory if it doesn't exist
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        charts_md = "## Comparative Charts\n\n"
        
        # Identify all categories present in the data
        categories = set()
        for data_key in self.data.keys():
            categories.update(self.data[data_key]['Category'].unique())
        categories = list(categories)
        
        # For each category, create a chart comparing key metrics
        for category in categories:
            # Extract data for specified metrics in this category
            chart_data = {}
            
            for metric in self.metrics_to_compare:
                metric_values = []
                
                for data_key in self.data.keys():
                    value = self._get_metric_value(self.data[data_key], category, metric)
                    if value is not None:
                        metric_values.append(value)
                    else:
                        metric_values.append(0)  # Use 0 for missing values
                
                chart_data[metric] = metric_values
            
            # Create DataFrames for plotting
            plot_data = pd.DataFrame(chart_data, index=[self._get_simulation_label(k) for k in self.data.keys()])
            
            # Generate individual charts for each metric
            for metric in self.metrics_to_compare:
                plt.figure(figsize=(12, 7))
                
                # Create bars with colors based on simulation priorities
                bars = plot_data[metric].plot(kind='bar', color=[self._get_priority_color(self.priorities[k]) for k in self.data.keys()])
                
                plt.title(f"{category.capitalize()} - {self.metric_display_names.get(metric, metric)}")
                plt.ylabel(self.metric_display_names.get(metric, metric))
                plt.xlabel("Simulation (Optimization Priority)")
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                plt.xticks(rotation=45, ha='right')
                
                # Add value labels on top of each bar
                for i, v in enumerate(plot_data[metric]):
                    plt.text(i, v * 1.01, f'{v:.1f}', ha='center', fontsize=9)
                
                # Add a legend for priority colors
                unique_priorities = list(set(self.priorities.values()))
                legend_handles = [plt.Rectangle((0,0),1,1, color=self._get_priority_color(p)) for p in unique_priorities]
                legend_labels = [self.priority_display_names.get(p, p.capitalize()) for p in unique_priorities]
                plt.legend(legend_handles, legend_labels, title="Optimization Priority")
                
                plt.tight_layout()
                
                # Save chart if output directory is specified
                if output_dir:
                    chart_path = os.path.join(output_dir, f"{category}_{metric}.png")
                    plt.savefig(chart_path)
                    charts_md += f"![{category.capitalize()} - {metric}]({chart_path})\n\n"
                
                plt.close()
            
            # Generate transportation mode comparison charts
            direct_modes = ["WALK", "BICYCLE", "CAR"]
            transit_modes = ["TRAM", "SUBWAY", "BUS", "RAIL"]
            
            # Direct modes chart
            direct_mode_data = {}
            
            for mode in direct_modes:
                mode_values = []
                
                for data_key in self.data.keys():
                    value = self._get_metric_value(self.data[data_key], category, f"direct_mode_{mode}_proportion")
                    if value is not None:
                        mode_values.append(value)
                    else:
                        mode_values.append(0)
                
                direct_mode_data[mode] = mode_values
            
            direct_mode_df = pd.DataFrame(direct_mode_data, index=[self._get_simulation_label(k) for k in self.data.keys()])
            
            plt.figure(figsize=(14, 8))
            direct_mode_df.plot(kind='bar', stacked=True, colormap='tab10')
            plt.title(f"{category.capitalize()} - Direct Transportation Modes")
            plt.ylabel("Proportion")
            plt.xlabel("Simulation (Optimization Priority)")
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.xticks(rotation=45, ha='right')
            plt.legend(title="Mode")
            plt.tight_layout()
            
            if output_dir:
                chart_path = os.path.join(output_dir, f"{category}_direct_modes.png")
                plt.savefig(chart_path)
                charts_md += f"![{category.capitalize()} - Direct Modes]({chart_path})\n\n"
            
            plt.close()
            
            # Transit modes chart
            transit_mode_data = {}
            
            for mode in transit_modes:
                mode_values = []
                
                for data_key in self.data.keys():
                    value = self._get_metric_value(self.data[data_key], category, f"transit_mode_{mode}_proportion")
                    if value is not None:
                        mode_values.append(value)
                    else:
                        mode_values.append(0)
                
                transit_mode_data[mode] = mode_values
            
            transit_mode_df = pd.DataFrame(transit_mode_data, index=[self._get_simulation_label(k) for k in self.data.keys()])
            
            plt.figure(figsize=(14, 8))
            transit_mode_df.plot(kind='bar', stacked=True, colormap='Paired')
            plt.title(f"{category.capitalize()} - Transit Transportation Modes")
            plt.ylabel("Proportion")
            plt.xlabel("Simulation (Optimization Priority)")
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.xticks(rotation=45, ha='right')
            plt.legend(title="Mode")
            plt.tight_layout()
            
            if output_dir:
                chart_path = os.path.join(output_dir, f"{category}_transit_modes.png")
                plt.savefig(chart_path)
                charts_md += f"![{category.capitalize()} - Transit Modes]({chart_path})\n\n"
            
            plt.close()
        
        return charts_md
    
    def _get_priority_color(self, priority):
        """
        Get color based on optimization priority.
        
        Parameters:
        -----------
        priority : str
            Optimization priority
            
        Returns:
        --------
        str
            Color hex code
        """
        # Base priority colors
        priority_colors = {
            "carbon": "#2ca02c",  # Green for carbon optimization
            "cost": "#1f77b4",    # Blue for cost optimization
            "time": "#ff7f0e",    # Orange for time optimization
            "legs": "#9467bd"     # Purple for legs optimization
        }
        
        # If it's a standard priority, return its color
        if priority in priority_colors:
            return priority_colors[priority]
        
        # For custom priorities, generate a deterministic color based on the string
        if priority:
            # Simple hash function to generate colors based on the string
            hash_val = sum(ord(c) for c in priority)
            # Generate a hue between 0 and 1 based on the hash
            hue = (hash_val % 100) / 100.0
            
            # Convert HSV to RGB (simplified approach)
            h = hue * 6
            i = int(h)
            f = h - i
            q = 1 - f
            t = f
            i = i % 6
            
            r, g, b = 0, 0, 0
            if i == 0: r, g, b = 1, t, 0
            elif i == 1: r, g, b = q, 1, 0
            elif i == 2: r, g, b = 0, 1, t
            elif i == 3: r, g, b = 0, q, 1
            elif i == 4: r, g, b = t, 0, 1
            elif i == 5: r, g, b = 1, 0, q
            
            # Convert to hex
            return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        
        return "#7f7f7f"  # Gray for unknown/empty
        
    def generate_key_findings(self):
        """
        Generate key findings from the comparison.
        
        Returns:
        --------
        str
            Markdown text with key findings
        """
        if not self.data:
            return "No data loaded."
            
        findings = "## Key Findings\n\n"
        
        # Extract categories
        categories = set()
        for data_key in self.data.keys():
            categories.update(self.data[data_key]['Category'].unique())
        categories = list(categories)
        
        # Define key metrics to analyze
        key_metrics = [
            "total_carbon_footprint",
            "avg_carbon_footprint",
            "total_cost",
            "avg_cost",
            "total_travel_time",
            "avg_travel_time"
        ]
        
        # For each category and metric, find the best (lowest) simulation
        for category in categories:
            findings += f"### {category.capitalize()} Analysis\n\n"
            
            for metric in key_metrics:
                findings += f"#### {self.metric_display_names.get(metric, metric)}\n\n"
                
                metric_values = {}
                
                for data_key in self.data.keys():
                    value = self._get_metric_value(self.data[data_key], category, metric)
                    if value is not None:
                        metric_values[data_key] = value
                
                if metric_values:
                    best_sim = min(metric_values, key=metric_values.get)
                    worst_sim = max(metric_values, key=metric_values.get)
                    
                    best_priority = self.priorities.get(best_sim, "Unknown")
                    worst_priority = self.priorities.get(worst_sim, "Unknown")
                    
                    findings += f"- Best simulation: **{best_sim}** (Priority: {self.priority_display_names.get(best_priority, best_priority.capitalize())}) with value {metric_values[best_sim]:.2f}\n"
                    findings += f"- Worst simulation: **{worst_sim}** (Priority: {self.priority_display_names.get(worst_priority, worst_priority.capitalize())}) with value {metric_values[worst_sim]:.2f}\n"
                    
                    # Calculate percentage difference
                    pct_diff = ((metric_values[worst_sim] - metric_values[best_sim]) / metric_values[best_sim]) * 100
                    findings += f"- Percentage difference: **{pct_diff:.2f}%**\n\n"
                    
                    # Check if the optimization priority matches the metric
                    metric_type = None
                    if "carbon" in metric:
                        metric_type = "carbon"
                    elif "cost" in metric:
                        metric_type = "cost"
                    elif "time" in metric:
                        metric_type = "time"
                    elif "legs" in metric:
                        metric_type = "legs"
                    
                    if metric_type and metric_type == best_priority:
                        findings += f"- **Note**: The simulation optimized for {self.priority_display_names.get(best_priority)} indeed achieved the best result for this metric.\n\n"
                    elif metric_type:
                        # Find the simulation with the matching priority
                        matching_sims = [k for k, v in self.priorities.items() if v == metric_type]
                        if matching_sims and matching_sims[0] in metric_values:
                            matching_value = metric_values[matching_sims[0]]
                            matching_rank = sorted(metric_values.values()).index(matching_value) + 1
                            findings += f"- **Note**: The simulation optimized for {self.priority_display_names.get(metric_type)} ranked #{matching_rank} for this metric.\n\n"
                else:
                    findings += "- No data available for this metric\n\n"
            
            # Analyze transportation modes
            findings += "#### Transportation Mode Analysis\n\n"
            
            for data_key in self.data.keys():
                priority = self.priorities.get(data_key, "Unknown")
                findings += f"**{data_key}** (Priority: {self.priority_display_names.get(priority, priority.capitalize())}):\n"
                
                # Direct modes
                direct_modes = {}
                for mode in ["WALK", "BICYCLE", "CAR"]:
                    proportion = self._get_metric_value(self.data[data_key], category, f"direct_mode_{mode}_proportion")
                    if proportion is not None:
                        direct_modes[mode] = proportion
                
                if direct_modes:
                    predominant_mode = max(direct_modes, key=direct_modes.get)
                    findings += f"- Predominant direct mode: **{predominant_mode}** ({direct_modes[predominant_mode]:.1%})\n"
                
                # Transit modes
                transit_modes = {}
                for mode in ["TRAM", "SUBWAY", "BUS", "RAIL"]:
                    proportion = self._get_metric_value(self.data[data_key], category, f"transit_mode_{mode}_proportion")
                    if proportion is not None and proportion > 0:
                        transit_modes[mode] = proportion
                
                if transit_modes:
                    predominant_transit = max(transit_modes, key=transit_modes.get)
                    findings += f"- Predominant transit mode: **{predominant_transit}** ({transit_modes[predominant_transit]:.1%})\n"
                else:
                    findings += "- No significant transit usage\n"
                
                findings += "\n"
        
        return findings
    
    def generate_recommendations(self):
        """
        Generate recommendations based on the analysis.
        
        Returns:
        --------
        str
            Markdown text with recommendations
        """
        if not self.data:
            return "No data loaded."
            
        recommendations = "## Recommendations\n\n"
        
        # Extract categories
        categories = set()
        for data_key in self.data.keys():
            categories.update(self.data[data_key]['Category'].unique())
        categories = list(categories)
        
        # Define metrics to consider for recommendations
        metrics = {
            "carbon": "total_carbon_footprint",
            "cost": "total_cost",
            "time": "total_travel_time",
            "legs": "avg_legs_per_attendee"
        }
        
        # For each optimization target, recommend the best simulation
        for target, metric in metrics.items():
            recommendations += f"### For {self.priority_display_names.get(target, target.capitalize())} Optimization\n\n"
            
            best_sim = None
            best_value = float('inf')
            
            for data_key in self.data.keys():
                for category in categories:
                    value = self._get_metric_value(self.data[data_key], category, metric)
                    if value is not None and value < best_value:
                        best_value = value
                        best_sim = data_key
            
            if best_sim:
                priority = self.priorities.get(best_sim, "Unknown")
                recommendations += f"- **Recommended simulation: {best_sim}** (Priority: {self.priority_display_names.get(priority, priority.capitalize())})\n"
                recommendations += f"- {self.metric_display_names.get(metric, metric)}: {best_value:.2f}\n\n"
                
                # Check if the recommendation matches the actual priority
                if priority == target:
                    recommendations += f"- **Note**: This matches the simulation's optimization priority.\n\n"
                else:
                    recommendations += f"- **Note**: Interestingly, a simulation with a different optimization priority ({self.priority_display_names.get(priority, priority.capitalize())}) performed best for this metric.\n\n"
                
                # Add supporting data
                recommendations += "Supporting metrics:\n\n"
                
                for category in categories:
                    for m in self.metrics_to_compare:
                        if m != metric:
                            value = self._get_metric_value(self.data[best_sim], category, m)
                            if value is not None:
                                recommendations += f"- {category.capitalize()} {self.metric_display_names.get(m, m)}: {value:.2f}\n"
                
                recommendations += "\n"
            else:
                recommendations += "- No recommendation available due to insufficient data\n\n"
        
        # Add general recommendations
        recommendations += "### General Recommendations\n\n"
        recommendations += "1. **Balance optimization targets**: Consider the trade-offs between carbon footprint, cost, and travel time.\n"
        recommendations += "2. **Mode selection**: Promote sustainable transportation modes while maintaining reasonable travel times.\n"
        recommendations += "3. **Further analysis**: Conduct sensitivity analysis to understand the impact of different parameters.\n"
        recommendations += "4. **User experience**: Consider user preferences and comfort in addition to quantitative metrics.\n"
        
        # Add priority-specific recommendations
        recommendations += "\n### Priority-Specific Recommendations\n\n"
        
        recommendations += "**Carbon Footprint Reduction**:\n"
        recommendations += "- Encourage use of public transit and cycling for shorter distances.\n"
        recommendations += "- Consider carbon offset programs for unavoidable high-emission journeys.\n\n"
        
        recommendations += "**Cost Optimization**:\n"
        recommendations += "- Look for group discounts on public transit where available.\n"
        recommendations += "- Consider carpooling options to share costs among attendees.\n\n"
        
        recommendations += "**Time Efficiency**:\n"
        recommendations += "- Prioritize direct connections and minimize transfers.\n"
        recommendations += "- Consider dedicated transportation services for larger groups.\n\n"
        
        recommendations += "**Trip Simplicity (Fewer Legs)**:\n"
        recommendations += "- Balance the number of legs with other factors like cost and carbon footprint.\n"
        recommendations += "- Consider the cognitive load of complex itineraries on attendees.\n"
        
        return recommendations
    
    def generate_full_report(self, output_dir=None):
        """
        Generate a full comparative analysis report.
        
        Parameters:
        -----------
        output_dir : str
            Directory to save charts to
            
        Returns:
        --------
        str
            Markdown report with the full analysis
        """
        if not self.data:
            return "# Comparative Analysis Report\n\nNo data loaded."
        
        report = "# Comparative Analysis Report\n\n"
        report += "## Overview\n\n"
        report += f"This report compares {len(self.data)} different simulation scenarios:\n\n"
        
        for data_key in self.data.keys():
            priority = self.priorities.get(data_key, "Unknown")
            report += f"- **{data_key}** (Optimization Priority: {self.priority_display_names.get(priority, priority.capitalize())})\n"
        
        report += "\n"
        
        # Extract categories
        categories = set()
        for data_key in self.data.keys():
            categories.update(self.data[data_key]['Category'].unique())
        categories = list(categories)
        
        # Generate comparison table
        report += "## Metric Comparison\n\n"
        report += self.generate_comparison_table(categories)
        report += "\n\n"
        
        # Generate mode comparison
        report += "## Transportation Mode Comparison\n\n"
        report += self.generate_mode_comparison(categories)
        report += "\n\n"
        
        # Generate key findings
        report += self.generate_key_findings()
        report += "\n\n"
        
        # Generate recommendations
        report += self.generate_recommendations()
        report += "\n\n"
        
        # Generate charts
        charts_md = self.generate_comparative_charts(output_dir)
        report += charts_md
        
        self.report = report
        return report
    
    def save_report(self, output_path):
        """
        Save the generated report to a file.
        
        Parameters:
        -----------
        output_path : str
            Path to save the report to
        """
        if not self.report:
            self.generate_full_report()
            
        with open(output_path, 'w') as f:
            f.write(self.report)
        
        print(f"Report saved to {output_path}")