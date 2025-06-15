class PriorityConstants:
    """Centralized constants for priority distributions and mappings."""
    
    PRIMARY_PRIORITY_DISTRIBUTION = {
        'CONVENIENCE': 0.44,
        'COST': 0.34,
        'DURATION': 0.19,
        'FOOTPRINT': 0.03
    }
    
    SECOND_PRIORITY_DISTRIBUTION = {
        'DURATION': {'COST': 0.8, 'CONVENIENCE': 0.2},
        'COST': {'CONVENIENCE': 0.5, 'DURATION': 0.5},
        'CONVENIENCE': {'COST': 0.5, 'DURATION': 0.5},
        'FOOTPRINT': {'CONVENIENCE': 0.44, 'COST': 0.36, 'DURATION': 0.20}
    }
    
    PRIORITY_COLUMNS = {
        'DURATION': 'total_duration',
        'COST': 'calculated_total_cost',
        'CONVENIENCE': 'leg_count',
        'FOOTPRINT': 'calculated_total_carbon_footprint'
    }

class TradeOffThresholds:
    """Survey-based trade-off thresholds for different priority combinations."""
    
    THRESHOLDS = {
        'DURATION_COST': {
            'min_cost_savings': 5,
            'time_tolerance': {
                5: 15,    # For €5-10 savings, accept up to 15 min extra
                10: 30,   # For €10-20 savings, accept up to 30 min extra
                20: 60,   # For €20+ savings, accept up to 1 hour extra
            }
        },
        'COST_DURATION': {
            'min_time_savings': 5,
            'cost_tolerance': {
                5: 5,     # For 5-15 min savings, pay up to €5 extra
                15: 10,   # For 15-30 min savings, pay up to €10 extra
                30: 20,   # For 30+ min savings, pay up to €20 extra
            }
        },
        'COST_CONVENIENCE': {
            'min_convenience_gain': 1,
            'cost_tolerance': {
                1: 15,    # For 1 leg reduction, pay up to €15 extra
                2: 25,    # For 2+ leg reduction, pay up to €25 extra
            }
        },
        'CONVENIENCE_COST': {
            'min_cost_savings': 10,
            'convenience_tolerance': {
                10: 1,    # For €10-20 savings, accept 1 extra leg
                20: 2,    # For €20+ savings, accept 2+ extra legs
            }
        },
        'CONVENIENCE_DURATION': {
            'min_time_savings': 15,
            'convenience_tolerance': {
                15: 1,    # For 15-30 min savings, accept 1 extra leg
                30: 2,    # For 30+ min savings, accept 2+ extra legs
            }
        }
    }