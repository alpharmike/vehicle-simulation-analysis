from datetime import timedelta
import pandas as pd
import pm4py
import re


def get_processed_metadata(meta_file_path: str):
    """
    Read and preprocess metadata to ensure consistency between all
    """
    locations_meta_df = pd.read_excel(meta_file_path, sheet_name="Locations")
    vehicles_meta_df = pd.read_excel(meta_file_path, sheet_name="Vehicles")
    co_meta_df = pd.read_excel(meta_file_path, sheet_name="ContainerOrders")

    locations_meta_df.rename(columns={"Location Name": "location_name", "X-Coordinate [mm]": "x", "Y-Coordinate [mm]": "y", "Capacity limitation (# SC)": "capacity"}, inplace=True)
    vehicles_meta_df.rename(columns={"ID": "id", "StartLocation": "start_location", "LogOn": "log_on", "LogOff": "log_off"}, inplace=True)
    co_meta_df.rename(
        columns={"TractorOrderId": "to_id", "ContainerOrderId": "co_id", "ContainerName": "container_name", "Length": "length", "OriginLocation": "origin", "DestinationLocation": "dest", "Time first known": "time_first_known"},
        inplace=True
    )

    locations_meta_df = preprocess_data(locations_meta_df)
    vehicles_meta_df = preprocess_data(vehicles_meta_df)
    co_meta_df = preprocess_data(co_meta_df)

    locations_meta_df["location_type"] = locations_meta_df["location_name"].apply(lambda loc: re.match(pattern=r"[A-Z]+", string=loc)[0])

    return locations_meta_df, vehicles_meta_df, co_meta_df


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Trim all object columns to ensure consistency across tables
    """
    object_cols = df.select_dtypes('object').columns
    df[object_cols] = df[object_cols].apply(lambda x: x.str.strip())
    return df


def create_event_log(parsed_logs: list[tuple[str, dict]]) -> pd.DataFrame:
    """
    Given a list of parsed logs including their pattern and extracted data, create an event log compatible for Process Mining.
    The event log should ensure correct temporal ordering and causal dependencies.

    :param parsed_logs: A list of 2-element tuples, where the first element of each tuple represent the log pattern and the second element holds data for the corresponding log.
    :return: An event log compatible for process mining
    """
    event_log = []
    opt_schedules = {}
    for pattern, log_data in parsed_logs:
        log_time = log_data["log_time"]
        # Submission of a container to the realm of the optimizer
        if pattern == "container_submission":
            co_id = log_data["to_id"].removeprefix("TO_")
            event = {
                "to_id": log_data["to_id"],
                "co_id": co_id,
                "action": "submit for scheduling",
                "timestamp": log_time
            }
            start_event = {**event, 'lifecycle': 'start'}
            end_event = {**event, 'lifecycle': 'complete'}
        # Scheduling the traveling and action timeline for a container by the optimizer
        elif pattern == "travel_action_schedule":
            opt_scheduling = {
                "to_id": log_data["to_id"],
                "co_id": log_data["co_id"],
                "action": f"schedule {log_data['action'].lower()} by optimizer",
                "timestamp": log_time
            }
            opt_schedules[log_data["co_id"]] = log_data
            start_event = {**opt_scheduling, 'lifecycle': 'start'}
            end_event = {**opt_scheduling, 'lifecycle': 'complete'}
        # Actual driving log
        elif pattern == "driving":
            event = {
                "to_id": log_data["to_id"],
                "co_id": log_data["co_id"],
                "vehicle_id": log_data["vehicle_id"],
                "action": f"dispatch vehicle to {log_data['action'].lower()} container",
            }
            start_time = min(log_time, opt_schedules[log_data["co_id"]]["travel_start_time"])
            extracted_duration = (opt_schedules[log_data["co_id"]]["travel_end_time"] - opt_schedules[log_data["co_id"]]["travel_start_time"]).total_seconds()
            reported_duration = log_data['duration_in_s']
            start_event = {**event, 'timestamp': start_time, 'lifecycle': 'start'}
            end_event = {**event, 'timestamp': start_time + timedelta(seconds=min(extracted_duration, reported_duration)), 'lifecycle': 'complete'}
        # Actual action log, where the status can be working or waiting, or finished.
        elif pattern == "action":
            event = {
                "to_id": log_data["to_id"],
                "co_id": log_data["co_id"],
                "vehicle_id": log_data["vehicle_id"],
                "location": log_data["location_name"]
            }
            if log_data["status"] == "working":
                action = f"{log_data['action'].lower()} container"
                start_time = log_time
                extracted_duration = (opt_schedules[log_data["co_id"]]["action_end_time"] - opt_schedules[log_data["co_id"]]["action_start_time"]).total_seconds()
                reported_duration = log_data['duration_in_s']
                end_time = log_time + timedelta(seconds=min(extracted_duration, reported_duration))
            elif log_data["status"] == "waited":
                action = "wait for a lane to be freed"
                start_time = log_time - timedelta(seconds=log_data['duration_in_s'])
                end_time = log_time
            elif log_data["status"] == "finished":
                continue
            else:
                raise ValueError("Invalid status for action")

            event['action'] = action
            start_event = {**event, 'timestamp': start_time, 'lifecycle': 'start'}
            end_event = {**event, 'timestamp': end_time, 'lifecycle': 'complete'}
        else:
            continue
        event_log.extend([start_event, end_event])

    event_log_df = pd.DataFrame(event_log)
    # Ensure correct vehicle resource is propagated for all events corresponding to one container (case)
    event_log_df["vehicle_id"] = event_log_df.groupby("co_id")["vehicle_id"].transform(lambda x: x.bfill().ffill())

    # Format and rename the event log dataframe columns to make it compatible for process mining
    event_log_df = event_log_df.rename(columns={"co_id": "case_id", "action": "activity", "vehicle_id": "org:resource", "lifecycle": "lifecycle:transition"})
    event_log_df = pm4py.format_dataframe(event_log_df, case_id='case_id', activity_key='activity', timestamp_key='timestamp')
    #
    event_log_df = event_log_df.fillna("")

    return event_log_df


def create_position_tracking_df(position_tracking_logs: list[dict], vehicles_meta_df: pd.DataFrame, locations_meta_df: pd.DataFrame):
    # Merge vehicles and locations table to get the initial coordinates of vehicles
    vehicle_location_df = vehicles_meta_df.merge(locations_meta_df, how="left", left_on="start_location", right_on="location_name")

    def add_initial_location(row):
        # Add the start location of vehicles to the position tracking list of vehicles
        vehicle_rec = vehicle_location_df[vehicle_location_df["id"] == row["vehicle_id"]]
        row["x"].insert(0, vehicle_rec["x"].iloc[0])
        row["y"].insert(0, vehicle_rec["y"].iloc[0])
        return row

    position_tracking_df = pd.DataFrame(position_tracking_logs)
    position_tracking_df = position_tracking_df.merge(locations_meta_df, how="left", on=["x", "y"])
    position_tracking_df = position_tracking_df.groupby("vehicle_id", as_index=False).agg({"x": lambda x: list(x), "y": lambda y: list(y)})
    position_tracking_df.apply(lambda row: add_initial_location(row), axis=1)

    return position_tracking_df


def create_travel_info_df(travel_info_logs: list[dict]):
    driving_df = pd.DataFrame(travel_info_logs).rename(columns={"duration_in_s": "driving_time"})
    driving_df[["driving_time", "distance_in_mm"]] = driving_df[["driving_time", "distance_in_mm"]].astype(int)
    driving_df["speed"] = driving_df["distance_in_mm"] / driving_df["driving_time"]
    return driving_df


def create_action_df(action_logs: list[dict]):
    action_df = pd.DataFrame(action_logs)
    action_df['duration_in_s'] = action_df['duration_in_s'].fillna(0.0).astype(int)

    # Separate action-related logs based on status (waiting, working, etc)
    waiting_df = action_df[action_df['status'] == "waited"].rename(columns={"duration_in_s": "waiting_time"})
    working_df = action_df[action_df['status'] == "working"].rename(columns={"duration_in_s": "processing_time"})
    merged_action_df = working_df.merge(waiting_df[["co_id", "action", "waiting_time"]], how="left", on=["co_id", "action"]).drop(columns=["status"])
    # Fill waiting time with 0 for records indicate processing/working
    merged_action_df["waiting_time"] = merged_action_df["waiting_time"].fillna(0.0)

    return merged_action_df


def create_optimizer_scheduling_df(optimizer_scheduling_logs: list[dict]):
    travel_action_df = pd.DataFrame(optimizer_scheduling_logs)
    travel_action_df["expected_travel_duration"] = (travel_action_df["travel_end_time"] - travel_action_df["travel_start_time"]).dt.total_seconds()
    travel_action_df["expected_action_duration"] = (travel_action_df["action_end_time"] - travel_action_df["action_start_time"]).dt.total_seconds()
    return travel_action_df
