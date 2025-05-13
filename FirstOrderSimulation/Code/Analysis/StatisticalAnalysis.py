import pandas as pd

class StatisticalAnalysis:
    """
    A class that analyzes transportation data for festival attendees,
    calculating carbon footprints, travel times, transportation modes, and costs.
    """
    
    def __init__(self, departure_df, return_df):
        """
        Initialize with the departure and return dataframes.
        
        Args:
            departure_df: DataFrame containing departure trip data
            return_df: DataFrame containing return trip data
        """
        self.departure_df = departure_df
        self.return_df = return_df
        
        # List of all possible transport modes to check
        self.transit_modes = ['WALK', 'BICYCLE', 'CAR', 'BUS', 'SUBWAY', 'TRAM', 'RAIL']
        
        # Merge dataframes to get complete attendee data
        self.all_attendees = pd.merge(
            self.departure_df, 
            self.return_df,
            on='attendee_id', 
            suffixes=('_dep', '_ret')
        )
        
        # Get the total number of unique attendees
        self.total_attendees = len(pd.concat([
            self.departure_df['attendee_id'], 
            self.return_df['attendee_id']
        ]).unique())
        
        # Process data to prepare for analysis
        self._process_journey_legs()
    
    def _process_journey_legs(self):
        """Count journey legs and prepare data for analysis."""
        # Function to count non-empty legs in a trip
        def count_legs(row):
            leg_columns = [col for col in row.index if 'leg' in col and 'mode' in col]
            return sum(1 for col in leg_columns if pd.notna(row[col]) and row[col] != '')
        
        # Count legs for departure and return trips
        self.departure_df['leg_count'] = self.departure_df.apply(count_legs, axis=1)
        self.return_df['leg_count'] = self.return_df.apply(count_legs, axis=1)
    
    def _count_attendees_using_mode(self, df, mode):
        """
        Count attendees who use a specific mode in any leg of their journey.
        
        Args:
            df: DataFrame containing trip data
            mode: Transportation mode to count
            
        Returns:
            Set of attendee IDs using the specified mode
        """
        # Get all leg mode columns
        leg_columns = [col for col in df.columns if 'leg' in col and 'mode' in col]
        
        # Find attendees using this mode in any leg
        attendees_using_mode = set()
        for col in leg_columns:
            mode_users = df[df[col] == mode]['attendee_id']
            attendees_using_mode.update(mode_users)
            
        return attendees_using_mode
    
    def analyze(self, output_csv=None, output_md=None, print_summary=False):
        """
        Analyze transportation data and return metrics.
        
        Args:
            output_csv: Optional file path to save results as CSV
            output_md: Optional file path to save results as Markdown
            print_summary: Whether to print a summary of results to console
            
        Returns:
            Dictionary containing all computed metrics
        """
        # Compute all metrics
        metrics = self._compute_all_metrics()
        
        # Save results to CSV if specified
        if output_csv:
            self._save_results_to_csv(metrics, output_csv)
        
        # Save results to Markdown if specified
        if output_md:
            self._save_results_to_markdown(metrics, output_md)
        
        # Print summary if requested
        if print_summary:
            self._print_summary(metrics)
        
        return metrics    
    
    def _compute_all_metrics(self):
        """
        Compute all transportation metrics categorized by trip type.
        
        Returns:
            Dictionary with metrics in three categories: 
            'departure', 'return', and 'combined'
        """
        # Create a structured dictionary with three categories
        metrics = {'departure': {}, 'return': {}, 'combined': {}}
        
        # Calculate carbon footprint metrics
        self._compute_carbon_metrics(metrics)
        
        # Calculate cost metrics
        self._compute_cost_metrics(metrics)
        
        # Calculate travel time metrics
        self._compute_time_metrics(metrics)
        
        # Calculate journey leg metrics
        self._compute_leg_metrics(metrics)
        
        # Calculate direct mode metrics (first leg only)
        self._compute_direct_mode_metrics(metrics)
        
        # Calculate transit mode metrics (any leg)
        self._compute_transit_mode_metrics(metrics)
        
        return metrics
    
    def _compute_carbon_metrics(self, metrics):
        """Calculate carbon footprint metrics."""
        # Calculate carbon footprint for departure trips
        dep_carbon_total = self.departure_df['calculated_total_carbon_footprint'].sum()
        dep_carbon_avg = dep_carbon_total / len(self.departure_df)
        
        # Calculate carbon footprint for return trips
        ret_carbon_total = self.return_df['calculated_total_carbon_footprint'].sum()
        ret_carbon_avg = ret_carbon_total / len(self.return_df)
        
        # Calculate combined carbon footprint
        total_carbon = dep_carbon_total + ret_carbon_total
        avg_carbon_per_attendee = total_carbon / max((len(self.departure_df)), (len(self.return_df)))
        
        # Store metrics
        metrics['departure']['total_carbon_footprint'] = dep_carbon_total
        metrics['departure']['avg_carbon_footprint'] = dep_carbon_avg
        metrics['return']['total_carbon_footprint'] = ret_carbon_total
        metrics['return']['avg_carbon_footprint'] = ret_carbon_avg
        metrics['combined']['total_carbon_footprint'] = total_carbon
        metrics['combined']['avg_carbon_per_attendee'] = avg_carbon_per_attendee
    
    def _compute_cost_metrics(self, metrics):
        """Calculate trip cost metrics."""
        # Calculate cost for departure trips
        dep_cost_total = self.departure_df['calculated_total_cost'].sum()
        dep_cost_avg = dep_cost_total / len(self.departure_df)
        
        # Calculate cost for return trips
        ret_cost_total = self.return_df['calculated_total_cost'].sum()
        ret_cost_avg = ret_cost_total / len(self.return_df)
        
        # Calculate combined cost
        total_cost = dep_cost_total + ret_cost_total
        avg_cost_per_attendee = total_cost / max(len(self.departure_df), len(self.return_df))
        
        # Store metrics
        metrics['departure']['total_cost'] = dep_cost_total
        metrics['departure']['avg_cost'] = dep_cost_avg
        metrics['return']['total_cost'] = ret_cost_total
        metrics['return']['avg_cost'] = ret_cost_avg
        metrics['combined']['total_cost'] = total_cost
        metrics['combined']['avg_cost_per_attendee'] = avg_cost_per_attendee
    
    def _compute_time_metrics(self, metrics):
        """Calculate travel time metrics."""
        # Calculate travel time for departure trips
        dep_duration_total = self.departure_df['total_duration'].sum()
        dep_duration_avg = dep_duration_total / len(self.departure_df)
        
        # Calculate travel time for return trips
        ret_duration_total = self.return_df['total_duration'].sum()
        ret_duration_avg = ret_duration_total / len(self.return_df)
        
        # Calculate combined travel time
        total_duration = dep_duration_total + ret_duration_total
        avg_duration_attendee = total_duration / max(len(self.departure_df), len(self.return_df))
        
        # Store metrics
        metrics['departure']['total_travel_time'] = dep_duration_total
        metrics['departure']['avg_travel_time'] = dep_duration_avg
        metrics['return']['total_travel_time'] = ret_duration_total
        metrics['return']['avg_travel_time'] = ret_duration_avg
        metrics['combined']['total_travel_time'] = total_duration
        metrics['combined']['avg_travel_time_per_attendee'] = avg_duration_attendee
    
    def _compute_leg_metrics(self, metrics):
        """Calculate journey leg metrics."""
        # Calculate total and average legs for departure trips
        total_legs_departure = self.departure_df['leg_count'].sum()
        avg_legs_per_attendee_departure = total_legs_departure / len(self.departure_df)
        
        # Calculate total and average legs for return trips
        total_legs_return = self.return_df['leg_count'].sum()
        avg_legs_per_attendee_return = total_legs_return / len(self.return_df)
        
        # Calculate combined metrics
        total_legs = total_legs_departure + total_legs_return
        avg_legs_per_attendee = total_legs / max(len(self.departure_df), len(self.return_df))
    
        
        # Store metrics
        metrics['departure']['total_legs'] = total_legs_departure
        metrics['departure']['avg_legs_per_attendee'] = avg_legs_per_attendee_departure
        metrics['return']['total_legs'] = total_legs_return
        metrics['return']['avg_legs_per_attendee'] = avg_legs_per_attendee_return
        metrics['combined']['total_legs'] = total_legs
        metrics['combined']['avg_legs_per_attendee'] = avg_legs_per_attendee
    
    def _compute_direct_mode_metrics(self, metrics):
        """Calculate direct mode metrics (any leg, not just the first)."""
        for mode in ['WALK', 'BICYCLE', 'CAR']:
            # Count for departure trips using any leg
            dep_users = self._count_attendees_using_mode(self.departure_df, mode)
            dep_count = len(dep_users)
            
            # Count for return trips using any leg
            ret_users = self._count_attendees_using_mode(self.return_df, mode)
            ret_count = len(ret_users)
            
            # Combined unique users
            combined_users = dep_users | ret_users
            combined_count = len(combined_users)
            
            # Store metrics
            metrics['departure'][f'direct_mode_{mode}_count'] = dep_count
            metrics['departure'][f'direct_mode_{mode}_proportion'] = dep_count / len(self.departure_df)
            metrics['return'][f'direct_mode_{mode}_count'] = ret_count
            metrics['return'][f'direct_mode_{mode}_proportion'] = ret_count / len(self.return_df)
            metrics['combined'][f'direct_mode_{mode}_count'] = combined_count
            metrics['combined'][f'direct_mode_{mode}_proportion'] = combined_count / self.total_attendees
    
    def _compute_transit_mode_metrics(self, metrics):
        """Calculate transit mode metrics (any leg)."""
        # For each transit mode, calculate metrics separately for departure and return
        for mode in ['TRAM', 'SUBWAY', 'BUS', 'RAIL']:
            # Count attendees using this mode in departure trips
            dep_users = self._count_attendees_using_mode(self.departure_df, mode)
            dep_count = len(dep_users)
            
            # Count attendees using this mode in return trips
            ret_users = self._count_attendees_using_mode(self.return_df, mode)
            ret_count = len(ret_users)
            
            # Combined users across both directions
            combined_users = set(dep_users) | set(ret_users)
            combined_count = len(combined_users)
            
            # Store metrics
            metrics['departure'][f'transit_mode_{mode}_count'] = dep_count
            metrics['departure'][f'transit_mode_{mode}_proportion'] = dep_count / len(self.departure_df)
            metrics['return'][f'transit_mode_{mode}_count'] = ret_count
            metrics['return'][f'transit_mode_{mode}_proportion'] = ret_count / len(self.return_df)
            metrics['combined'][f'transit_mode_{mode}_count'] = combined_count
            metrics['combined'][f'transit_mode_{mode}_proportion'] = combined_count / self.total_attendees
    
    def _save_results_to_csv(self, metrics, file_path):
        """Save metrics to a CSV file."""
        # Flatten the metrics dictionary into a DataFrame
        flattened_metrics = []
        for category, category_metrics in metrics.items():
            for metric_name, value in category_metrics.items():
                flattened_metrics.append({
                    "Category": category,
                    "Metric": metric_name,
                    "Value": value
                })

        # Convert to a DataFrame and save
        metrics_df = pd.DataFrame(flattened_metrics)
        metrics_df.to_csv(file_path, index=False)
        print(f"Metrics saved to CSV: {file_path}")

    def _save_results_to_markdown(self, metrics, file_path):
        """Save metrics to a Markdown file with formatted tables."""
        with open(file_path, 'w') as md_file:
            # Write the header
            md_file.write("# Transportation Analysis Results\n\n")
            md_file.write(f"Total number of attendees: {self.total_attendees}\n\n")
            
            # Process each category
            for category in ['departure', 'return', 'combined']:
                md_file.write(f"## {category.capitalize()} Trip Metrics\n\n")
                cat_metrics = metrics[category]
                
                # Carbon footprint section
                md_file.write("### Carbon Footprint\n\n")
                md_file.write("| Metric | Value |\n")
                md_file.write("|--------|-------|\n")
                
                if 'total_carbon_footprint' in cat_metrics:
                    md_file.write(f"| Total carbon footprint | {cat_metrics['total_carbon_footprint']:.2f} units |\n")
                if 'avg_carbon_footprint' in cat_metrics:
                    md_file.write(f"| Average carbon footprint | {cat_metrics['avg_carbon_footprint']:.2f} units |\n")
                if 'avg_carbon_per_attendee' in cat_metrics:
                    md_file.write(f"| Average carbon per attendee | {cat_metrics['avg_carbon_per_attendee']:.2f} units |\n")
                
                md_file.write("\n")
                
                # Cost section
                md_file.write("### Cost\n\n")
                md_file.write("| Metric | Value |\n")
                md_file.write("|--------|-------|\n")
                
                if 'total_cost' in cat_metrics:
                    md_file.write(f"| Total cost | {cat_metrics['total_cost']:.2f} |\n")
                if 'avg_cost' in cat_metrics:
                    md_file.write(f"| Average cost | {cat_metrics['avg_cost']:.2f} |\n")
                if 'avg_cost_per_attendee' in cat_metrics:
                    md_file.write(f"| Average cost per attendee | {cat_metrics['avg_cost_per_attendee']:.2f} |\n")
                
                md_file.write("\n")
                
                # Travel time section
                md_file.write("### Travel Time\n\n")
                md_file.write("| Metric | Value |\n")
                md_file.write("|--------|-------|\n")
                
                if 'total_travel_time' in cat_metrics:
                    md_file.write(f"| Total travel time | {cat_metrics['total_travel_time']:.2f} minutes |\n")
                if 'avg_travel_time' in cat_metrics:
                    md_file.write(f"| Average travel time | {cat_metrics['avg_travel_time']:.2f} minutes |\n")
                if 'avg_travel_time_per_attendee' in cat_metrics:
                    md_file.write(f"| Average travel time per attendee | {cat_metrics['avg_travel_time_per_attendee']:.2f} minutes |\n")
                
                md_file.write("\n")
                
                # Journey complexity section
                md_file.write("### Journey Complexity\n\n")
                md_file.write("| Metric | Value |\n")
                md_file.write("|--------|-------|\n")
                
                if 'total_legs' in cat_metrics:
                    md_file.write(f"| Total journey legs | {cat_metrics['total_legs']} |\n")
                if 'avg_legs_per_attendee' in cat_metrics:
                    md_file.write(f"| Average legs per attendee | {cat_metrics['avg_legs_per_attendee']:.2f} |\n")
                
                md_file.write("\n")
                
                # Direct mode distribution section
                md_file.write("### Direct Mode Distribution\n\n")
                md_file.write("| Mode | Count | Percentage |\n")
                md_file.write("|------|-------|------------|\n")
                
                for mode in ['WALK', 'BICYCLE', 'CAR']:
                    mode_count_key = f'direct_mode_{mode}_count'
                    mode_prop_key = f'direct_mode_{mode}_proportion'
                    
                    if mode_count_key in cat_metrics and mode_prop_key in cat_metrics:
                        count = cat_metrics[mode_count_key]
                        proportion = cat_metrics[mode_prop_key] * 100
                        md_file.write(f"| {mode} | {count} | {proportion:.1f}% |\n")
                
                md_file.write("\n")
                
                # Transit mode usage section
                md_file.write("### Transit Mode Usage\n\n")
                md_file.write("| Mode | Count | Percentage |\n")
                md_file.write("|------|-------|------------|\n")
                
                for mode in ['TRAM', 'SUBWAY', 'BUS', 'RAIL']:
                    mode_count_key = f'transit_mode_{mode}_count'
                    mode_prop_key = f'transit_mode_{mode}_proportion'
                    
                    if mode_count_key in cat_metrics and mode_prop_key in cat_metrics:
                        count = cat_metrics[mode_count_key]
                        proportion = cat_metrics[mode_prop_key] * 100
                        md_file.write(f"| {mode} | {count} | {proportion:.1f}% |\n")
                
                md_file.write("\n")
            
            # Add summary and conclusions
            md_file.write("## Summary and Recommendations\n\n")
            md_file.write("This analysis provides insights into attendee transportation patterns for the festival. ")
            md_file.write("Based on the data, recommendations can be made for improving sustainability, cost-efficiency, and overall transportation experience in future events.\n\n")
            
            # Add timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            md_file.write(f"*Report generated on: {timestamp}*\n")
            
        print(f"Metrics saved to Markdown: {file_path}")    
    
    def _print_summary(self, metrics):
        """Print a summary of analysis results."""
        print("===== TRANSPORTATION ANALYSIS SUMMARY =====")
        print(f"Total number of attendees: {self.total_attendees}")
        
        # Print each category of metrics
        for category in ['departure', 'return', 'combined']:
            print(f"\n==== {category.upper()} TRIP METRICS ====")
            cat_metrics = metrics[category]
            
            # Carbon footprint
            print("\n----- CARBON FOOTPRINT -----")
            if 'total_carbon_footprint' in cat_metrics:
                print(f"Total carbon footprint: {cat_metrics['total_carbon_footprint']:.2f} units")
            if 'avg_carbon_footprint' in cat_metrics:
                print(f"Average carbon footprint: {cat_metrics['avg_carbon_footprint']:.2f} units")
            if 'avg_carbon_per_attendee' in cat_metrics:
                print(f"Average carbon per attendee: {cat_metrics['avg_carbon_per_attendee']:.2f} units")
            
            # Cost section
            print("\n----- COST -----")
            if 'total_cost' in cat_metrics:
                print(f"Total cost: {cat_metrics['total_cost']:.2f}")
            if 'avg_cost' in cat_metrics:
                print(f"Average cost: {cat_metrics['avg_cost']:.2f}")
            if 'avg_cost_per_attendee' in cat_metrics:
                print(f"Average cost per attendee: {cat_metrics['avg_cost_per_attendee']:.2f}")
            
            # Travel time
            print("\n----- TRAVEL TIME -----")
            if 'total_travel_time' in cat_metrics:
                print(f"Total travel time: {cat_metrics['total_travel_time']:.2f} minutes")
            if 'avg_travel_time' in cat_metrics:
                print(f"Average travel time: {cat_metrics['avg_travel_time']:.2f} minutes")
            if 'avg_travel_time_per_attendee' in cat_metrics:
                print(f"Average travel time per attendee: {cat_metrics['avg_travel_time_per_attendee']:.2f} minutes")
            
            # Journey complexity
            print("\n----- JOURNEY COMPLEXITY -----")
            if 'total_legs' in cat_metrics:
                print(f"Total legs: {cat_metrics['total_legs']}")
            if 'avg_legs_per_attendee' in cat_metrics:
                print(f"Average legs per attendee: {cat_metrics['avg_legs_per_attendee']:.2f}")
            
            # Direct mode distribution
            print("\n----- DIRECT MODE DISTRIBUTION -----")
            for mode in ['WALK', 'BICYCLE', 'CAR']:
                if f'direct_mode_{mode}_count' in cat_metrics:
                    count = cat_metrics[f'direct_mode_{mode}_count']
                    if f'direct_mode_{mode}_proportion' in cat_metrics:
                        proportion = cat_metrics[f'direct_mode_{mode}_proportion'] * 100
                        print(f"{mode}: {count} attendees ({proportion:.1f}%)")
                    else:
                        print(f"{mode}: {count} attendees")
                
            # Transit mode usage
            print("\n----- TRANSIT MODE USAGE -----")
            for mode in ['TRAM', 'SUBWAY', 'BUS', 'RAIL']:
                if f'transit_mode_{mode}_count' in cat_metrics:
                    count = cat_metrics[f'transit_mode_{mode}_count']
                    proportion = cat_metrics[f'transit_mode_{mode}_proportion'] * 100
                    print(f"{mode}: {count} attendees ({proportion:.1f}%)")