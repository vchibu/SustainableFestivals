from Code.Calculators.RealisticCalculator.constants import PriorityConstants
import numpy as np

class PriorityAssigner:
    """Handles assignment of primary and secondary priorities to attendees."""
    
    def __init__(self):
        self.constants = PriorityConstants()
    
    def assign_priorities_to_attendees(self, unique_attendees):
        """Assign priorities to unique attendees and return mapping."""
        primary_priorities = self._assign_primary_priorities(len(unique_attendees))
        
        attendee_priority_map = {}
        for i, attendee_id in enumerate(unique_attendees):
            primary_priority = primary_priorities[i]
            second_priority = self._get_second_priority(primary_priority)
            attendee_priority_map[attendee_id] = {
                'priority': primary_priority,
                'second_priority': second_priority
            }
        
        return attendee_priority_map
    
    def _assign_primary_priorities(self, n_attendees):
        """Assigns primary priorities based on distribution."""
        priority_counts = self._calculate_priority_counts(
            n_attendees, self.constants.PRIMARY_PRIORITY_DISTRIBUTION
        )
        
        priorities = []
        for priority, count in priority_counts.items():
            priorities.extend([priority] * count)
        
        np.random.shuffle(priorities)
        return priorities
    
    def _get_second_priority(self, primary_priority):
        """Determines second priority based on primary priority."""
        distribution = self.constants.SECOND_PRIORITY_DISTRIBUTION[primary_priority]
        priorities = list(distribution.keys())
        probabilities = list(distribution.values())
        
        return np.random.choice(priorities, p=probabilities)
    
    def _calculate_priority_counts(self, n_attendees, distribution):
        """Calculates exact counts for each priority."""
        counts = {}
        total_assigned = 0
        
        for priority, percentage in distribution.items():
            count = int(n_attendees * percentage)
            counts[priority] = count
            total_assigned += count
        
        remaining = n_attendees - total_assigned
        if remaining > 0:
            largest_priority = max(distribution.keys(), key=lambda k: distribution[k])
            counts[largest_priority] += remaining
        
        return counts