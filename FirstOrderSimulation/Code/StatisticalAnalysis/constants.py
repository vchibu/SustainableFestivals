"""
Constants used throughout the transportation analysis system.
"""

# Transportation modes
DIRECT_MODES = ['WALK', 'BICYCLE', 'CAR']
TRANSIT_MODES = ['TRAM', 'SUBWAY', 'BUS', 'RAIL']
ALL_TRANSIT_MODES = DIRECT_MODES + TRANSIT_MODES

# Metric categories
METRIC_CATEGORIES = ['departure', 'return', 'combined']