import numpy as np
import pandas as pd
import pm4py


def analyze_case_durations(event_log_df: pd.DataFrame, bin_size: int = 500):
    """
    How long does each case (container) in the process take from the tine of submission to the optimizer until it;s dropped at the destination
    """
    case_durations = pm4py.get_all_case_durations(event_log_df)
    bins = list(range(0, int(np.ceil(max(case_durations) / bin_size) + 1) * bin_size, bin_size))
    binned_values = np.digitize(case_durations, bins)
    return case_durations, bins, binned_values


def analyze_running_cases(event_log_df: pd.DataFrame):
    """
    Determines how many cases are running at every point of time throughout the process
    """

    # Note: In our preliminary analysis, we only have one start and one end activity
    start_activities = pm4py.get_start_activities(event_log_df)
    end_activities = pm4py.get_end_activities(event_log_df)
    started_cases = []
    running_cases = []
    timestamps = []

    time_sorted_df = event_log_df.copy().sort_values(by='time:timestamp')
    for idx, row in time_sorted_df.iterrows():
        case_id = row['case:concept:name']
        activity = row['concept:name']
        timestamp = row['time:timestamp']
        lifecycle_transition = row['lifecycle:transition']
        if activity in start_activities and lifecycle_transition == "start":
            started_cases.append(case_id)
        elif activity in end_activities and lifecycle_transition == 'complete':
            started_cases.remove(case_id)

        # Add the number of running cases at each point of observing an event
        running_cases.append(len(started_cases))
        timestamps.append(timestamp)

    return running_cases, timestamps


def analyze_location_occupancy(event_log_df: pd.DataFrame, location: str):
    """
    Analyze the number of running and waiting cases for a location over time. This implies the congestion at a specific location, and a possible room for improvement in the process
    """
    time_sorted_df = event_log_df.sort_values(by='time:timestamp')
    loc_related_df = time_sorted_df[time_sorted_df['location'] == location]

    occupancy_data = []
    latest_running_snapshot = set()
    latest_waiting_snapshot = set()
    for idx, row in loc_related_df.iterrows():
        location = row.get("location", None)
        case_id = row['case:concept:name']
        activity = row['concept:name']
        timestamp = row['time:timestamp']
        lifecycle_transition = row['lifecycle:transition']

        if "wait" in activity:
            if lifecycle_transition == "start":
                latest_waiting_snapshot.add(case_id)
            else:
                latest_waiting_snapshot.remove(case_id)
        elif activity in ["pick container", "drop container"]:
            if lifecycle_transition == "start":
                latest_running_snapshot.add(case_id)
            else:
                latest_running_snapshot.remove(case_id)
        else:
            continue

        occupancy_data.append({
            "timestamp": timestamp,
            "location": location,
            "running_cases": latest_running_snapshot.copy(),
            "waiting_cases": latest_waiting_snapshot.copy()
        })

    # Avoid duplicate results at similar points in time by keeping the last snapshot at each observation time
    occupancy_df = pd.DataFrame(occupancy_data).groupby("timestamp", as_index=False).last()
    occupancy_df["running_count"] = occupancy_df["running_cases"].apply(lambda cases: len(cases))
    occupancy_df["waiting_count"] = occupancy_df["waiting_cases"].apply(lambda cases: len(cases))

    return occupancy_df
